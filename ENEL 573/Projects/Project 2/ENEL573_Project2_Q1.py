"""
Project 2 - Question 1: Alternating Bit Protocol (ABP) simulator
Discrete event simulation of ABP over a noisy link. Sender option 1: an ACK in
error, or with RN != NEXT_EXPECTED_ACK, is ignored (only a TIME-OUT resends).
"""
import bisect
import numpy as np

H = 54 * 8              # frame header = ACK length (bits)
l = 1500 * 8            # packet payload (bits)
L = H + l               # data frame length (bits)
C = 5_000_000           # channel capacity (bits/s) = 5 Mb/s
N_HALF = 5000           # 5,000 packets, then 5,000 more
SEED = 573              # fixed seed so results can be reproduced
TIMEOUT, ACK = "TIMEOUT", "ACK"
NIL = None              # returned when a frame or ACK is lost


class Event:
    """Event: type, time, error flag (0 = no error, 1 = error), sequence number."""
    def __init__(self, etype, time, error_flag=0, seq=-1):
        self.type, self.time, self.error_flag, self.seq = etype, time, error_flag, seq


class EventScheduler:
    """ES: events kept in time order, earliest event at the head."""
    def __init__(self):
        self.events = []

    def register(self, ev):                         # insert in time order
        bisect.insort_right(self.events, ev, key=lambda e: e.time)

    def dequeue(self):                              # remove and return the earliest event
        return self.events.pop(0)

    def purge_timeouts(self):                       # only one TIME-OUT may be in the ES
        self.events = [e for e in self.events if e.type != TIMEOUT]


class ABP:
    def __init__(self, tau, delta, ber, rng):
        self.tau, self.delta, self.ber, self.rng = tau, delta, ber, rng
        self.ES = EventScheduler()
        self.tc, self.SN, self.next_expected_ack = 0.0, 0, 1    # sender
        self.tcs, self.next_expected_frame = 0.0, 0             # receiver

    def channel(self, t, seq, length):
        """Forward and reverse channel. Returns NIL (lost) or (t + tau, error flag, seq)."""
        bits = np.where(self.rng.random(length) < self.ber, 0, 1)   # each bit is 0 w.p. BER
        n_errors = length - bits.sum()                              # number of zeroes
        if n_errors >= 5:
            return NIL                                              # LOSS
        return (t + self.tau, 1 if n_errors > 0 else 0, seq)        # ERROR or NOERROR

    def send(self, t, sn):
        """SEND(): forward channel + receiver + reverse channel. Returns an ACK event or NIL."""
        fwd = self.channel(t, sn, L)                    # forward channel
        if fwd is NIL:
            return NIL
        self.tcs, flag, seq = fwd                       # receiver
        if flag == 0 and seq == self.next_expected_frame:
            self.next_expected_frame = (self.next_expected_frame + 1) % 2   # deliver packet
        rn = self.next_expected_frame
        rev = self.channel(self.tcs + H / C, rn, H)     # reverse channel (ACK of H bits)
        if rev is NIL:
            return NIL
        return Event(ACK, *rev)

    def transmit(self):
        """Send the packet in the buffer with the current SN."""
        self.tc += L / C                                # frame fully sent at tc + L/C
        self.ES.purge_timeouts()
        self.ES.register(Event(TIMEOUT, self.tc + self.delta))
        ack = self.send(self.tc, self.SN)
        if ack is not NIL:
            self.ES.register(ack)

    def run(self, n_packets):
        """Run until n_packets are acknowledged. Returns the time of every 5,000th one."""
        successes, times = 0, {}
        self.transmit()                                 # first packet at tc = 0
        while successes < n_packets:
            ev = self.ES.dequeue()
            self.tc = max(self.tc, ev.time)             # sender is not interrupted while busy
            if ev.type == TIMEOUT:
                self.transmit()                         # resend same packet, same SN
            elif ev.error_flag == 0 and ev.seq == self.next_expected_ack:
                successes += 1                          # packet delivered
                self.SN = (self.SN + 1) % 2
                self.next_expected_ack = (self.next_expected_ack + 1) % 2
                if successes % N_HALF == 0:
                    times[successes] = self.tc
                if successes < n_packets:
                    self.transmit()                     # next packet
            # any other ACK: do nothing (option 1)
        return times


def simulate(delta_over_tau, two_tau, ber):
    """Throughput (bits/s, payload only) for the first 5,000, next 5,000 and all 10,000 packets."""
    tau = two_tau / 2
    t = ABP(tau, delta_over_tau * tau, ber, np.random.default_rng(SEED)).run(2 * N_HALF)
    t1, t2 = t[N_HALF], t[2 * N_HALF]
    return N_HALF * l / t1, N_HALF * l / (t2 - t1), 2 * N_HALF * l / t2


DELTAS = [2.5, 5, 7.5, 10, 12.5]      # delta / tau
TWO_TAUS = [0.010, 0.500]             # 2*tau (s)
BERS = [0.0, 1e-5, 1e-4]


def main():
    total = {}
    print("%-6s %-6s %-7s %11s %11s %7s %11s" % (
        "2tau", "D/tau", "BER", "1st 5000", "next 5000", "diff", "all 10000"))
    for two_tau in TWO_TAUS:
        for ber in BERS:
            for k in DELTAS:
                first, second, total[two_tau, ber, k] = simulate(k, two_tau, ber)
                diff = abs(second - first) / first * 100
                print("%-6s %-6s %-7g %11.0f %11.0f %6.2f%% %11.0f" % (
                    "%gms" % (two_tau * 1000), k, ber, first, second, diff, total[two_tau, ber, k]))

    print("\nThroughput (bits/s), 10,000 packets")
    print("%-6s|%27s |%27s" % ("", "2tau = 10 ms", "2tau = 500 ms"))
    print("D/tau |" + "%9s%9s%9s |" % ("BER=0", "1e-5", "1e-4") * 2)
    for k in DELTAS:
        row = [total[tt, b, k] for tt in TWO_TAUS for b in BERS]
        print("%-6s|%9.0f%9.0f%9.0f |%9.0f%9.0f%9.0f |" % (k, *row))


if __name__ == "__main__":
    main()



