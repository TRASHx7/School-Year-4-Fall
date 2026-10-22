import math, random, time
import matplotlib.pyplot as plt

L = 12000            # average packet length (bits)
C = 1_000_000        # link transmission rate (bits/s) = 1 Mbps
OBS_FACTOR = 5       # observer rate alpha = 5 * lambda
T_START = 1000       # first simulation time to try (s)
ARRIVAL, DEPARTURE, OBSERVER = "A", "D", "O"

def exponential(rate):
    """Inverse method: X = -ln(1 - U) / rate, U ~ U(0,1)."""
    return -math.log(1.0 - random.random()) / rate

def build_event_list(lam, T):
    """Create all arrival, departure and observer events in [0, T] and sort them by time."""
    events = []
    t, last_departure = 0.0, 0.0
    while True:
        t += exponential(lam)                       # a) next arrival (Poisson, rate lambda)
        if t > T:
            break
        events.append((t, ARRIVAL))
        service_time = exponential(1.0 / L) / C     # b) length (bits) / C (bits/s)
        start = max(t, last_departure)              # wait if the server is still busy
        last_departure = start + service_time
        if last_departure <= T:                     # keep only events inside [0, T]
            events.append((last_departure, DEPARTURE))

    alpha, t = OBS_FACTOR * lam, 0.0                # c) observers (Poisson, rate alpha)
    while True:
        t += exponential(alpha)
        if t > T:
            break
        events.append((t, OBSERVER))

    events.sort(key=lambda e: e[0])                 # time-ordered DES list
    return events

def simulate(rho, T):
    """Run one M/M/1 simulation and return (E[N], P_IDLE)."""
    lam = rho * C / L                               # rho = lambda * L / C
    Na = Nd = No = 0                                # arrivals, departures, observations
    sum_packets = idle_count = 0
    for _, kind in build_event_list(lam, T):        # process events in time order
        if kind == ARRIVAL:
            Na += 1
        elif kind == DEPARTURE:
            Nd += 1
        else:                                       # observer: record the queue state
            No += 1
            n_in_system = Na - Nd
            sum_packets += n_in_system
            if n_in_system == 0:
                idle_count += 1
    return sum_packets / No, idle_count / No        # E[N], P_IDLE

def stable_simulation(rho, tol=0.05, max_k=10):
    """Run for T, 2T, 3T, ... until E[N] and P_IDLE change by less than 5% between runs.
    Two passes in a row are required, so one lucky agreement is not enough near rho = 1."""
    prev = simulate(rho, T_START)
    passes = 0
    for k in range(2, max_k + 1):
        cur = simulate(rho, k * T_START)
        diffs = [abs(c - p) / p for c, p in zip(cur, prev)]
        passes = passes + 1 if max(diffs) < tol else 0
        if passes == 2:
            break
        prev = cur
    return cur, k * T_START, max(diffs)

def main():
    random.seed(time.time())
    rhos = [round(0.25 + 0.1 * i, 2) for i in range(8)]   # 0.25, 0.35, ..., 0.95
    print(f"M/M/1 simulation: L = {L} bits, C = {C} bps, "
          f"observer rate = {OBS_FACTOR} x lambda")
    print(f"{'rho':>5} {'E[N] sim':>9} {'E[N] th':>9} {'err%':>6} {'Pidle sim':>10} "
          f"{'Pidle th':>9} {'err%':>6} {'T(s)':>6} {'diff%':>6}")

    results = []
    for rho in rhos:
        (EN, P_idle), T_used, diff = stable_simulation(rho)
        EN_th, Pidle_th = rho / (1 - rho), 1 - rho          # M/M/1 theory
        results.append((rho, EN, EN_th, P_idle, Pidle_th))
        en_err = abs(EN - EN_th) / EN_th * 100
        pi_err = abs(P_idle - Pidle_th) / Pidle_th * 100
        print(f"{rho:5.2f} {EN:9.4f} {EN_th:9.4f} {en_err:6.2f} {P_idle:10.4f} "
              f"{Pidle_th:9.4f} {pi_err:6.2f} {T_used:6d} {diff * 100:6.2f}")

    r = [x[0] for x in results]
    for col_sim, col_th, ylabel, th_label, title in (
            (1, 2, "E[N] (packets)", r"Theory $\rho/(1-\rho)$",
             r"E[N] vs $\rho$ (M/M/1)"),
            (3, 4, r"$P_{IDLE}$", r"Theory $1-\rho$",
             r"$P_{IDLE}$ vs $\rho$ (M/M/1)")):
        plt.figure(figsize=(7, 4.5))
        plt.plot(r, [x[col_sim] for x in results], "o-", label="Simulation")
        plt.plot(r, [x[col_th] for x in results], "s--", label=th_label)
        plt.title(title)
        plt.xlabel(r"Utilization $\rho$")
        plt.ylabel(ylabel)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
    plt.show()                               

if __name__ == "__main__":
    main()
