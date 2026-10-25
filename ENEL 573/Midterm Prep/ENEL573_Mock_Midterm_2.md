---
title: "ENEL 573 Computer Networks: Mock Midterm Exam 2"
---

# ENEL 573 Computer Networks: Mock Midterm Exam 2 (Fall 2026)

**Name:** ______________________ **UCID:** ____________________ **Score:** ________ / 100

> **Instructions.** 50 minutes. Closed book. Non-programmable calculator allowed. Three problems; show your work and justify each answer. Unless stated otherwise: 1 Mbps = $10^6$ bits/s, 1 KB = 1000 bytes, and ignore packet headers.
>
> **Formula provided (M/M/1/N):** for an M/M/1 queue that holds at most $N$ packets, $P_n = \dfrac{1-\rho}{1-\rho^{N+1}}\rho^n$ for $0 \le n \le N$, and the blocking probability is $P_B = P_N$.

## Problem 1 (30 points): Packet-switched network

Consider the packet-switched network below. S1 and S2 are store-and-forward link-layer switches with large buffers. Ignore processing, propagation, and queueing delays except for the waiting caused by the link rates themselves.

```
                 20 Mbps
           +---------------- Host C
           |
Host A ---[S1]---------------[S2]---------------- Host B
  10 Mbps         5 Mbps       |       2 Mbps
                               |
                               +---------------- Host D
                                    8 Mbps
```

Links: A to S1 = 10 Mbps, S1 to C = 20 Mbps, S1 to S2 = 5 Mbps, S2 to D = 8 Mbps, S2 to B = 2 Mbps.

Host A **broadcasts** a **500 KB** file to Hosts B, C and D using a fixed packet size of **2 KB**. The transmission of packet 1 starts at time 0.

1. **(9 points)** When does each of Hosts C, D and B completely receive the **first** packet?
2. **(9 points)** When do Host C and Host D completely receive the **entire file**? Identify the bottleneck link on each path.
3. **(6 points)** When does Host B completely receive the entire file?
4. **(6 points)** Compute the average throughput (in Mbps) seen by Host B and by Host C. Which host gets better throughput and why?

<div class="pagebreak"></div>

## Problem 2 (35 points): TDM vs statistical multiplexing

A **64 kbps** communication line is shared by **8 sessions**. Each session generates Poisson traffic at **3 packets/s**. Packet lengths are exponentially distributed with mean **2,000 bits**.

1. **(10 points)** The line is divided into **8 equal-capacity TDM channels**, one per session. For each session, find the average number of packets waiting in the queue, the average number in the system, and the average delay per packet.

2. **(10 points)** The line is instead used with **statistical multiplexing** (all sessions share one queue served at 64 kbps). Find the average number in the queue, the average number in the system, and the average delay per packet, for the whole system **and** per session.

3. **(5 points)** By what factor does the average delay change from part 1 to part 2? Explain why, using the M/M/1 delay formula.

4. **(10 points)** In the statistical multiplexing case, the router can hold **at most 4 packets** in total (including the one being transmitted). Using the formula provided, find the blocking (loss) probability and the throughput of the line in packets/s.

<div class="pagebreak"></div>

## Problem 3 (35 points): Link layer

1. **(12 points)** A sender uses **two-dimensional even parity**. The 12 data bits $D = 0110\ 1110\ 0101$ are arranged as **3 rows of 4 bits** (one row per group of 4).
   a. Compute the row parity bits, the column parity bits, and the corner bit.
   b. The receiver gets the data $D' = 0110\ 1100\ 0101$ with the **same** parity bits. Is there an error? If so, how does the receiver find and correct it?
   c. Give an example of a 2-bit error that 2D parity **detects but cannot correct**, and explain why.

2. **(15 points)** Two nodes 3,000 km apart are connected by a **100 Mbps** fiber link (propagation speed $2 \times 10^8$ m/s). Data frames are **1,500 bytes**; ACK frames are negligibly short. The nodes use **stop-and-wait**.
   a. Find the link utilization and the maximum throughput (in bits/s) when there are no errors.
   b. Now each frame **or** its ACK is corrupted with probability $p = 0.2$ (timeout = round-trip time). Find the average number of transmissions per frame and the new maximum throughput.
   c. To keep the link fully busy with **Go-Back-N** (no errors), how many frames must the sender be allowed to have outstanding? What is the minimum number of sequence-number bits?

3. **(8 points)** A group of stations share a **100 kbps pure ALOHA** channel. Each station generates, on average (Poisson), one **500-bit** frame every **50 s**, even if earlier frames have not yet been sent. Using the maximum pure ALOHA utilization of $1/(2e) \approx 18.4\%$, what is the maximum number of stations? About how many could slotted ALOHA support, and why?

<div class="pagebreak"></div>

# Solutions: Mock Midterm 2

## Problem 1

Packet size $L = 2000 \times 8 = 16{,}000$ bits; number of packets $P = 500/2 = 250$.
Per-packet transmission times: 10 Mbps: 1.6 ms; 20 Mbps: 0.8 ms; 5 Mbps: 3.2 ms; 8 Mbps: 2 ms; 2 Mbps: 8 ms.

**1. First packet** (store-and-forward, add each hop's $L/R$):

* C: $1.6 + 0.8 = \mathbf{2.4\text{ ms}}$
* D: $1.6 + 3.2 + 2 = \mathbf{6.8\text{ ms}}$
* B: $1.6 + 3.2 + 8 = \mathbf{12.8\text{ ms}}$

**2. Entire file.** After the first packet arrives, the remaining $P - 1 = 249$ packets arrive one every $L/R_{min}$, where $R_{min}$ is the **slowest link on that path** (packets queue in front of it; faster links after it are never the limit):

$$T_{file} = T_{first} + (P-1)\frac{L}{R_{min}}$$

* C: path rates 10, 20 → bottleneck **A to S1 (10 Mbps)**: $2.4 + 249 \times 1.6 = \mathbf{400.8\text{ ms}}$.
* D: path rates 10, 5, 8 → bottleneck **S1 to S2 (5 Mbps)**, in the middle of the path: $6.8 + 249 \times 3.2 = \mathbf{803.6\text{ ms}}$.
  (Check: packets leave S1 every 3.2 ms; the last one finishes on S1 to S2 at $1.6 + 250 \times 3.2 = 801.6$ ms, then 2 ms on S2 to D.)

**3. Host B:** path rates 10, 5, 2 → bottleneck **S2 to B (2 Mbps)**: $12.8 + 249 \times 8 = \mathbf{2004.8\text{ ms}} \approx 2.005$ s.

**4. Throughput** = file size / time, with file = $500 \times 8 = 4\times10^6$ bits:

* C: $4\times10^6 / 0.4008 \approx \mathbf{9.98\text{ Mbps}}$
* B: $4\times10^6 / 2.0048 \approx \mathbf{2.00\text{ Mbps}}$

Host C gets about 5 times the throughput of B because its bottleneck link (10 Mbps) is 5 times faster than B's (2 Mbps). End-to-end throughput is approximately the bottleneck rate. (D gets ≈ 4.98 Mbps, limited by the 5 Mbps link.)

## Problem 2

**1. TDM.** Each channel: $64/8 = 8$ kbps, so $\mu = 8000/2000 = 4$ packets/s; $\lambda = 3$; $\rho = 0.75$. Per session (each is its own M/M/1 queue):

$$E[N_q] = \frac{\rho^2}{1-\rho} = \frac{0.5625}{0.25} = \mathbf{2.25}, \quad E[N] = \frac{\rho}{1-\rho} = \mathbf{3}, \quad W = \frac{1}{\mu - \lambda} = \frac{1}{4-3} = \mathbf{1\text{ s}}.$$

**2. Statistical multiplexing.** One queue: $\lambda = 8 \times 3 = 24$ packets/s, $\mu = 64000/2000 = 32$ packets/s, $\rho = 0.75$.

Whole system: $E[N_q] = \mathbf{2.25}$, $E[N] = \mathbf{3}$, $W = \dfrac{1}{32 - 24} = \mathbf{0.125\text{ s}}$ (waiting time $T_q = 0.75/8 = 0.094$ s).

Per session (all packets see the same delay; Little's Law with $\lambda_i = 3$): $E[N_i] = 3 \times 0.125 = \mathbf{0.375}$, $E[N_{q,i}] = 3 \times 0.09375 = \mathbf{0.28}$, delay **0.125 s**.

**3.** Delay drops from 1 s to 0.125 s, a factor of **8**. Both $\lambda$ and $\mu$ are multiplied by $k = 8$ while $\rho$ stays 0.75, and
$$W = \frac{1}{k\mu - k\lambda} = \frac{1}{k}\cdot\frac{1}{\mu - \lambda}.$$
With TDM, a session's packet must wait even when the other 7 channels are idle; with statistical multiplexing the full 64 kbps serves whoever has packets, so each packet is transmitted 8 times faster (Example 2.2).

**4. M/M/1/4** with $\rho = 0.75$:

$$P_B = P_4 = \frac{(1-\rho)\rho^4}{1-\rho^5} = \frac{0.25 \times 0.3164}{1 - 0.2373} = \frac{0.0791}{0.7627} \approx \mathbf{0.104}.$$

About 10.4% of packets are dropped. Throughput $= \lambda(1 - P_B) = 24 \times 0.896 \approx \mathbf{21.5}$ packets/s (≈ 43 kbps).
Check: $P_0 = 0.25/0.7627 = 0.328$, and $\mu(1 - P_0) = 32 \times 0.672 = 21.5$ ✓.

## Problem 3

**1a. 2D even parity.**

| | c1 | c2 | c3 | c4 | Row parity |
|---|---|---|---|---|---|
| Row 1 | 0 | 1 | 1 | 0 | **0** |
| Row 2 | 1 | 1 | 1 | 0 | **1** |
| Row 3 | 0 | 1 | 0 | 1 | **0** |
| Column parity | **1** | **1** | **0** | **1** | **1** (corner) |

Corner check: row parities 0, 1, 0 have one 1 → corner 1; column parities 1, 1, 0, 1 have three 1s → corner 1 (consistent).

**1b.** Received row 2 is `1100`: two 1s, but its row parity bit is 1, so **row 2 fails**. Column 3 is now 1, 0, 0: one 1, but its column parity bit is 0, so **column 3 fails**. All other checks pass. The single error is at the intersection, **row 2, column 3**; the receiver flips that bit back from 0 to 1 and recovers `0110 1110 0101` without retransmission.

**1c.** Example: flip **two bits in the same row**, e.g., row 1 c1 and c2 (`0110` → `1010`). Row 1 still has an even number of 1s, so no row check fails, but columns 1 and 2 both fail. The error is **detected**, but the receiver cannot tell which row the two bad bits are in (any row could explain those two failing columns), so it **cannot correct** it. (Similarly, two errors in the same column fail two rows and no column.)

**2. Stop-and-wait.**
$t_I = \dfrac{1500 \times 8}{100\times10^6} = 0.12$ ms; $\tau = \dfrac{3\times10^6}{2\times10^8} = 15$ ms; $t_A \approx 0$; so $t_T = t_I + 2\tau + t_A = 30.12$ ms.

a. $U = \dfrac{t_I}{t_T} = \dfrac{0.12}{30.12} = \mathbf{0.40\%}$. $\lambda_{max} = \dfrac{1}{t_T} = 33.2$ frames/s, i.e., $\dfrac{12{,}000}{0.03012} \approx \mathbf{398\text{ kbps}}$ on a 100 Mbps link.

b. Attempts per frame are geometric with success probability $1 - p = 0.8$: average $\dfrac{1}{1-p} = \mathbf{1.25}$ transmissions. $\lambda_{max} = \dfrac{1-p}{t_T} = \dfrac{0.8}{0.03012} = 26.6$ frames/s ≈ **319 kbps**.

c. The sender must keep transmitting for a whole cycle $t_T$: $W \ge \dfrac{t_T}{t_I} = \dfrac{30.12}{0.12} = \mathbf{251}$ frames. Go-Back-N allows a window of at most $2^m - 1$, so $2^m - 1 \ge 251 \Rightarrow 2^m \ge 252 \Rightarrow m = \mathbf{8}$ bits (window up to 255).

**3. Pure ALOHA.** Each station offers $\dfrac{500\text{ bits}}{50\text{ s}} = 10$ bps. Maximum useful rate $= \dfrac{1}{2e} \times 100{,}000 \approx 18{,}394$ bps, so
$$N_{max} = \left\lfloor\frac{18{,}394}{10}\right\rfloor = \mathbf{1839}\text{ stations}.$$
Slotted ALOHA has maximum $1/e \approx 36.8\%$, about **3678** stations (twice as many), because restricting transmissions to slot boundaries halves the vulnerable period from $2X$ to $X$, so only frames in the same slot collide.
