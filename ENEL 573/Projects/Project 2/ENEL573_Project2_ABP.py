"""
ENEL 573 Project 2, Question 1: Alternating Bit Protocol (ABP) simulator.

Discrete event simulation (DES) of ABP over a noisy point-to-point link.
Sender option 1: an ACK in error, or an error-free ACK whose RN is not
NEXT_EXPECTED_ACK, is ignored. Only a TIME-OUT makes the sender retransmit.

Building blocks (same names as the manual):
  EventScheduler : time-ordered list of events (register / dequeue / purge)
  channel()      : forward and reverse channel (one function for both)
  send()         : SEND() = forward channel + receiver + reverse channel
  simulate()     : the ABP sender, i.e. the next-event processor
"""
import bisect
import numpy as np

# ---------------- fixed parameters ----------------
H = 54 * 8                 # frame header = ACK length (bits)
l = 1500 * 8               # packet payload (bits)
L = H + l                  # data frame length (bits)
C = 5_000_000              # channel capacity (bits/s) = 5 Mb/s
N_HALF = 5000              # packets per half run (5,000 then 5,000 more)
SEED = 573                 # fixed seed so the report numbers can be reproduced

TIMEOUT, ACK = "TIMEOUT", "ACK"   # the two event types
NIL = None                        # what the channel / SEND() return on a loss


class Event:
    """An event: type, time, error flag (0 = no error, 1 = error), sequence number."""
    __slots__ = ("type", "time", "error_flag", "seq")

    def __init__(self, etype, time, error_flag=0, seq=-1):
        self.type, self.time, self.error_flag, self.seq = etype, time, error_flag, seq


class EventScheduler:
    """ES: events kept sorted by time, earliest event at the head."""

    def __init__(self):
        self.events = []

    def register(self, ev):
        # insert in time order (an equal time goes after the events already there)
        bisect.insort_right(self.events, ev, key=lambda e: e.time)

    def dequeue(self):
        # remove and return the next (earliest) event
        return self.events.pop(0)

    def purge_timeouts(self):
        # only one TIME-OUT may be outstanding, so drop the old one
        self.events = [e for e in self.events if e.type != TIMEOUT]


class ABPSimulator:
    def __init__(self, tau, delta, ber, rng):
        self.tau, self.delta, self.ber, self.rng = tau, delta, ber, rng
        self.ES = EventScheduler()
        # sender state
        self.tc = 0.0                 # sender current time
        self.SN = 0
        self.next_expected_ack = 1
        self.successes = 0            # packets confirmed by a correct ACK
        # receiver state
        self.tcs = 0.0                # receiver current time
        self.next_expected_frame = 0
        self.delivered = 0            # packets passed up to layer 3 at B
        # statistics
        self.stats = dict(frames_sent=0, timeouts=0, frame_lost=0, frame_error=0,
                          ack_lost=0, ack_error=0, ack_ignored=0)

    # ---------------- channel (forward and reverse) ----------------
    def channel(self, t, seq, length):
        """Send `length` bits that are fully on the link at time t.
        One Bernoulli trial per bit: a bit is in error (0) with probability BER.
        Returns NIL if 5 or more bits are in error (lost), otherwise
        (arrival time t + tau, error flag, unchanged sequence number)."""
        bits = np.where(self.rng.random(length) < self.ber, 0, 1)   # L iterations
        n_errors = length - int(bits.sum())                        # number of zeroes
        if n_errors >= 5:
            return NIL                                  # frame LOSS
        flag = 1 if n_errors > 0 else 0                 # ERROR (1 to 4 bits) or NOERROR
        return (t + self.tau, flag, seq)

    # ---------------- SEND(): forward channel + receiver + reverse channel ----------------
    def send(self, t, sn):
        """t = time the data frame has been completely put on the link (tc + L/C).
        Returns the ACK event to register in the ES, or NIL if frame or ACK is lost."""
        fwd = self.channel(t, sn, L)                    # forward channel
        if fwd is NIL:
            self.stats["frame_lost"] += 1
            return NIL

        # receiver
        self.tcs, flag, seq = fwd                       # frame fully received at tcs
        if flag == 0 and seq == self.next_expected_frame:
            self.delivered += 1                         # new packet up to layer 3
            self.next_expected_frame = (self.next_expected_frame + 1) % 2
        elif flag == 1:
            self.stats["frame_error"] += 1
        rn = self.next_expected_frame                   # ACK always carries RN

        # reverse channel: the ACK (H bits) leaves B at tcs + H/C
        rev = self.channel(self.tcs + H / C, rn, H)
        if rev is NIL:
            self.stats["ack_lost"] += 1
            return NIL
        t_ack, ack_flag, rn = rev
        if ack_flag == 1:
            self.stats["ack_error"] += 1
        return Event(ACK, t_ack, ack_flag, rn)

    # ---------------- sender ----------------
    def transmit(self):
        """Send the buffered packet with the current SN (new packet or retransmission)."""
        self.tc += L / C                                # frame is on the link at tc + L/C
        self.ES.purge_timeouts()                        # cancel the outstanding time-out
        self.ES.register(Event(TIMEOUT, self.tc + self.delta))
        self.stats["frames_sent"] += 1
        ack = self.send(self.tc, self.SN)
        if ack is not NIL:
            self.ES.register(ack)

    def run(self, n_packets, checkpoints):
        """Run until n_packets have been confirmed. Returns {N: time of N-th correct ACK}."""
        times = {}
        self.transmit()                                 # first packet at tc = 0
        while self.successes < n_packets:
            ev = self.ES.dequeue()
            # the sender cannot be interrupted, so an event that arrived while it
            # was still busy transmitting is handled when it becomes free
            self.tc = max(self.tc, ev.time)
            if ev.type == TIMEOUT:
                self.stats["timeouts"] += 1
                self.transmit()                         # resend same packet, same SN
            elif ev.error_flag == 0 and ev.seq == self.next_expected_ack:
                self.successes += 1                     # packet done, empty the buffer
                self.SN = (self.SN + 1) % 2
                self.next_expected_ack = (self.next_expected_ack + 1) % 2
                if self.successes in checkpoints:
                    times[self.successes] = self.tc
                if self.successes < n_packets:
                    self.transmit()                     # layer 3 always has a new packet
            else:
                self.stats["ack_ignored"] += 1          # option 1: do nothing
        return times


def simulate(delta_over_tau, two_tau, ber, seed=SEED):
    """One experiment. Returns throughput (bits/s, payload only) after 5,000 packets,
    for the 5,000 more packets, and over all 10,000 packets."""
    tau = two_tau / 2
    sim = ABPSimulator(tau, delta_over_tau * tau, ber, np.random.default_rng(seed))
    t = sim.run(2 * N_HALF, {N_HALF, 2 * N_HALF})
    t1, t2 = t[N_HALF], t[2 * N_HALF]
    return dict(first=N_HALF * l / t1,                  # first 5,000 packets
                second=N_HALF * l / (t2 - t1),          # the 5,000 more packets
                total=2 * N_HALF * l / t2,              # all 10,000 packets
                sim_time=t2, delivered=sim.delivered, **sim.stats)


def frame_probs(n, ber):
    """P(NOERROR), P(ERROR: 1 to 4 bit errors), P(LOSS: 5 or more) for an n-bit frame."""
    from math import comb
    p = [comb(n, k) * ber ** k * (1 - ber) ** (n - k) for k in range(5)]
    return p[0], sum(p[1:]), max(0.0, 1 - sum(p))


def theory(delta_over_tau, two_tau, ber):
    """Expected throughput (bits/s). Every failed attempt costs L/C + delta, because
    delta > 2*tau + H/C in every case. Two states per packet:
      1: B has not received the packet yet -> needs frame NOERROR and ACK NOERROR
      2: B already has it (only its ACK failed) -> a retransmission that is not
         lost makes B send RN = SN+1 again, so it only needs ACK NOERROR."""
    tau = two_tau / 2
    f_ok, f_err, f_loss = frame_probs(L, ber)
    a_ok = frame_probs(H, ber)[0]
    t_ok = L / C + 2 * tau + H / C                      # successful exchange
    t_fail = L / C + delta_over_tau * tau               # failed attempt ends at the time-out
    s_2 = (1 - f_loss) * a_ok                           # success prob. in state 2
    fails_2 = (1 - s_2) / s_2                           # mean failures in state 2
    fails_1 = ((1 - f_ok) + f_ok * (1 - a_ok) * (1 + fails_2)) / f_ok
    return l / (t_ok + fails_1 * t_fail)


DELTAS = [2.5, 5, 7.5, 10, 12.5]       # delta / tau
TWO_TAUS = [0.010, 0.500]              # 2*tau in seconds
BERS = [0.0, 1e-5, 1e-4]


def main():
    import json, os, time
    results = []
    start = time.time()
    print("ABP simulation, C = 5 Mb/s, H = 54 B, l = 1500 B, 2 x 5,000 packets per case")
    print("%-6s %-6s %-8s %12s %12s %12s %8s %12s %7s" % (
        "2tau", "D/tau", "BER", "1st 5000", "next 5000", "all 10000", "diff",
        "theory", "error"))
    for two_tau in TWO_TAUS:
        for ber in BERS:
            for k in DELTAS:
                r = simulate(k, two_tau, ber)
                th = theory(k, two_tau, ber)
                diff = abs(r["second"] - r["first"]) / r["first"] * 100
                err = abs(r["total"] - th) / th * 100
                r.update(two_tau=two_tau, ber=ber, delta_over_tau=k, theory=th,
                         half_diff_pct=diff, theory_err_pct=err)
                results.append(r)
                print("%-6s %-6s %-8s %12.1f %12.1f %12.1f %7.2f%% %12.1f %6.2f%%" % (
                    "%gms" % (two_tau * 1000), k, "%g" % ber, r["first"], r["second"],
                    r["total"], diff, th, err))
    print("Done in %.1f s" % (time.time() - start))

    # summary table in the layout asked for in the manual (bits/s)
    print("\nThroughput (bits/s) over 10,000 delivered packets")
    print("%-6s | %10s %10s %10s | %10s %10s %10s" % (
        "D/tau", "BER=0", "BER=1e-5", "BER=1e-4", "BER=0", "BER=1e-5", "BER=1e-4"))
    print("%-6s | %32s | %32s" % ("", "2tau = 10 ms", "2tau = 500 ms"))
    for k in DELTAS:
        row = [next(r["total"] for r in results if r["delta_over_tau"] == k
                    and r["two_tau"] == tt and r["ber"] == b)
               for tt in TWO_TAUS for b in BERS]
        print("%-6s | %10.0f %10.0f %10.0f | %10.0f %10.0f %10.0f" % (k, *row))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "abp_results.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=1)
    plot(results)


def plot(results):
    """Throughput vs delta/tau, one panel per 2*tau, one line per BER."""
    import os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = ["#2a78d6", "#eb6834", "#1baf7a"]            # one hue per BER, fixed order
    markers = ["o", "s", "^"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, two_tau in zip(axes, TWO_TAUS):
        for b, c, m in zip(BERS, colors, markers):
            rs = [r for r in results if r["two_tau"] == two_tau and r["ber"] == b]
            x = [r["delta_over_tau"] for r in rs]
            name = {0.0: "0", 1e-5: "1e-5", 1e-4: "1e-4"}[b]
            ax.plot(x, [r["theory"] / 1000 for r in rs], color=c, lw=1.5,
                    label="BER = %s, theory" % name)                 # line: theory
            ax.plot(x, [r["total"] / 1000 for r in rs], color=c, lw=0, marker=m, ms=9,
                    mec="white", mew=1.5, label="BER = %s, simulation" % name)  # markers
        ax.set_title("2τ = %g ms" % (two_tau * 1000))
        ax.set_xlabel("Time-out Δ / τ")
        ax.set_ylabel("Throughput (kb/s)")
        ax.set_xticks(DELTAS)
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.3, lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(fontsize=8, frameon=False)
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ABP_throughput.png")
    fig.savefig(out, dpi=200)


if __name__ == "__main__":
    main()
