---
title: "ENEL 573 Computer Networks: Mock Midterm Exam 1"
---

# ENEL 573 Computer Networks: Mock Midterm Exam 1 (Fall 2026)

**Name:** ______________________ **UCID:** ____________________ **Score:** ________ / 100

> **Instructions.** 50 minutes. Closed book. Non-programmable calculator allowed. Three problems; show your work and justify each answer. Unless stated otherwise: 1 Mbps = $10^6$ bits/s, 1 KB = 1000 bytes, and ignore packet headers.
>
> Suggested timing: Problem 1 about 17 min, Problem 2 about 17 min, Problem 3 about 16 min.

## Problem 1 (35 points): Switching and delay

Host A sends a **4 Mbit** file to Host B. The path consists of **three links** joined by **two store-and-forward routers**. Every link has transmission rate $R = 2$ Mbps and length 1,500 km, and the propagation speed is $2 \times 10^8$ m/s. Ignore processing and queueing delays.

a. **(8 points)** Suppose **message switching** is used: the whole file is sent as a single message. What is the end-to-end delay (from when A starts sending until B has received the entire file)?

b. **(10 points)** Now suppose **packet switching** is used and the file is divided into **1,000 packets of 4,000 bits** each, sent back-to-back. How long until B has received the entire file? Compare with part (a) and explain the difference in one or two sentences.

c. **(7 points)** Now suppose the network is **circuit switched**. Each link uses **TDM with 8 slots per frame**, and the call is given one slot on every link. Setting up the circuit takes **400 ms** before any data is sent. How long does it take from the start of circuit setup until B has the entire file?

d. **(10 points)** Separately, suppose a 2 Mbps link is shared by users who each require **250 kbps** when active and are active only **15%** of the time.
   i. How many users can be supported with circuit switching?
   ii. With packet switching and **30** users, write an expression for the probability that **more than 8** users are active at the same time, and evaluate it. What does this tell you about packet switching?

<div class="pagebreak"></div>

## Problem 2 (35 points): Queueing at a router

Packets arrive at a router's output link according to a **Poisson process** with rate $\lambda = 100$ packets/s. Packet lengths are **exponentially distributed** with mean **1,000 bytes**. The output link rate is **1 Mbps** and the buffer is infinite (model the link as an M/M/1 queue).

1. **(6 points)** Find the service rate $\mu$ (packets/s), the link utilization $\rho$, and the fraction of time the link is idle.

2. **(12 points)** Find the average number of packets in the system $E[N]$, the average number waiting in the buffer $E[N_q]$, the average total delay $W$, and the average waiting time in the buffer $T_q$. Verify one of your answers with Little's Law.

3. **(7 points)** What is the probability that **at least 4 packets are waiting in the buffer** (not counting the packet being transmitted)?

4. **(10 points)** The operator wants the average total delay per packet to be **at most 10 ms** with the same arrival rate. What is the minimum link rate (in Mbps) that achieves this?

<div class="pagebreak"></div>

## Problem 3 (30 points): Link layer

1. **(10 points)** A sender uses CRC with generator $G = 1011$. The data to send is $D = 11010011$. Compute the CRC bits $R$ and write the complete transmitted bit string. Show your division.

2. **(10 points)** Nodes A and B are at the two ends of a **2 km** shared **100 Mbps** Ethernet segment using CSMA/CD. The propagation speed is $2 \times 10^8$ m/s.
   a. In the worst case, how long after A starts transmitting does A detect a collision?
   b. What is the minimum frame length (in bits) that guarantees A is still transmitting when it detects a collision? Why does this matter?
   c. After its **3rd** collision, an adapter chooses $K$ uniformly from $\{0, 1, \dots, 7\}$ and waits $K \times 512$ bit times. What is the longest it can wait (in seconds)?

3. **(10 points)** A slotted ALOHA channel serves a very large population. Transmission attempts (new and retransmitted) form a Poisson process with an average of $G = 0.5$ attempts per slot.
   a. What is the throughput $S$ (successful frames per slot)?
   b. What fraction of slots are idle? What fraction contain a collision?
   c. On average, how many transmission attempts does a frame need before it gets through?
   d. If the channel used **pure** ALOHA at the same load $G = 0.5$, what would the throughput be? Briefly explain why it is lower.

<div class="pagebreak"></div>

# Solutions: Mock Midterm 1

## Problem 1

**Useful numbers.** Propagation per link: $d_{prop} = \dfrac{1.5\times10^6\text{ m}}{2\times10^8\text{ m/s}} = 7.5$ ms, so over 3 links $= 22.5$ ms.

**a. Message switching.** One link takes $d_{trans} = \dfrac{4\times10^6}{2\times10^6} = 2$ s. Each router must receive the whole message before forwarding (store-and-forward), so

$$T = 3 \times 2\text{ s} + 3 \times 7.5\text{ ms} = 6 + 0.0225 = \mathbf{6.0225\text{ s}}.$$

**b. Packet switching.** Per packet per link: $\dfrac{4000}{2\times10^6} = 2$ ms. With $P = 1000$ packets over $N = 3$ links:

$$T = (P + N - 1)\frac{L}{R} + 3d_{prop} = (1000 + 2)(2\text{ ms}) + 22.5\text{ ms} = 2.004 + 0.0225 = \mathbf{2.0265\text{ s}}.$$

About 3 times faster than (a). This is the **pipelining gain**: while one packet is on link 2, the next is already on link 1, so all three links work in parallel instead of waiting for the whole file at each router.

**c. TDM circuit switching.** The circuit gets $\dfrac{2\text{ Mbps}}{8} = 250$ kbps. Transmission time $= \dfrac{4\times10^6}{250\times10^3} = 16$ s. There is no store-and-forward in a circuit (bits flow straight through the switches), so propagation is counted once along the path:

$$T = 0.4 + 16 + 0.0225 = \mathbf{16.4225\text{ s}}.$$

**d.**
i. $N = \lfloor 2000/250 \rfloor = \mathbf{8}$ users.

ii. Each user is active with $p = 0.15$ independently, so the number active is Binomial(30, 0.15):

$$P(X > 8) = 1 - \sum_{k=0}^{8}\binom{30}{k}(0.15)^k(0.85)^{30-k}.$$

Terms for $k = 0, \dots, 8$: 0.0076, 0.0404, 0.1034, 0.1703, 0.2028, 0.1861, 0.1368, 0.0828, 0.0420 (sum ≈ 0.9722), so

$$P(X > 8) \approx 1 - 0.9722 = \mathbf{0.028}.$$

Packet switching supports **30** users (vs 8 with circuit switching) while the link is overloaded less than 3% of the time: statistical multiplexing exploits the burstiness of users.

## Problem 2

1. $\mu = \dfrac{C}{\bar L} = \dfrac{10^6}{8000} = \mathbf{125}$ packets/s. $\rho = \dfrac{100}{125} = \mathbf{0.8}$. Idle fraction $P_0 = 1 - \rho = \mathbf{0.2}$ (20%).

2.
$$E[N] = \frac{\rho}{1-\rho} = \frac{0.8}{0.2} = \mathbf{4}\text{ packets}, \qquad E[N_q] = \frac{\rho^2}{1-\rho} = \frac{0.64}{0.2} = \mathbf{3.2}\text{ packets}$$
$$W = \frac{1}{\mu - \lambda} = \frac{1}{25} = \mathbf{40\text{ ms}}, \qquad T_q = \frac{\rho}{\mu - \lambda} = \frac{0.8}{25} = \mathbf{32\text{ ms}}$$
Check with Little's Law: $\lambda W = 100 \times 0.04 = 4 = E[N]$ ✓ and $\lambda T_q = 100 \times 0.032 = 3.2 = E[N_q]$ ✓. Also $W = T_q + 1/\mu = 32 + 8 = 40$ ms ✓.

3. At least 4 waiting in the buffer means at least 5 in the system (4 waiting + 1 in service):
$$P(N \ge 5) = \sum_{n=5}^{\infty}(1-\rho)\rho^n = \rho^5 = 0.8^5 = \mathbf{0.328}.$$

4. Need $W = \dfrac{1}{\mu - \lambda} \le 0.01$ s, so $\mu - 100 \ge 100$, giving $\mu \ge 200$ packets/s. Link rate $C = \mu \bar L \ge 200 \times 8000 = \mathbf{1.6\text{ Mbps}}$. (Check: $\rho = 0.5$, $W = 1/100 = 10$ ms.)

## Problem 3

**1. CRC.** $G = 1011$ has 4 bits, so $r = 3$: append three zeros and divide `11010011000` by `1011` (modulo-2):

| Step | Window | Leading bit | XOR with | Result | Keep last 3 bits, bring down next |
|---|---|---|---|---|---|
| 1 | 1101 | 1 | 1011 | 0110 | 110 + **0** = 1100 |
| 2 | 1100 | 1 | 1011 | 0111 | 111 + **0** = 1110 |
| 3 | 1110 | 1 | 1011 | 0101 | 101 + **1** = 1011 |
| 4 | 1011 | 1 | 1011 | 0000 | 000 + **1** = 0001 |
| 5 | 0001 | 0 | 0000 | 0001 | 001 + **0** = 0010 |
| 6 | 0010 | 0 | 0000 | 0010 | 010 + **0** = 0100 |
| 7 | 0100 | 0 | 0000 | 0100 | 100 + **0** = 1000 |
| 8 | 1000 | 1 | 1011 | 0011 | no bits left: **R = 011** |

Transmitted frame: $\langle D, R\rangle$ = **`11010011 011`**. (Check: dividing `11010011011` by `1011` leaves remainder `000`.)

**2. CSMA/CD.** $t_{prop} = \dfrac{2000}{2\times10^8} = 10\ \mu$s; bit time $= 1/(100\times10^6) = 10$ ns.

a. Worst case: B starts transmitting just before A's first bit reaches it; B's signal then needs another $t_{prop}$ to get back to A. A detects the collision after $2t_{prop} = \mathbf{20\ \mu s}$.

b. A must still be transmitting at $2t_{prop}$: $L/R \ge 2t_{prop}$, so $L \ge 100\times10^6 \times 20\times10^{-6} = \mathbf{2000\text{ bits}}$ (250 bytes). If frames were shorter, A could finish sending before the collision reaches it, wrongly assume success, and never abort/retransmit.

c. Longest wait: $K = 7$: $7 \times 512 \times 10\text{ ns} = \mathbf{35.84\ \mu s}$. (Average wait with $K$ uniform on 0..7: $3.5 \times 5.12 = 17.92\ \mu$s.)

**3. Slotted ALOHA at $G = 0.5$.**

a. $S = Ge^{-G} = 0.5e^{-0.5} = \mathbf{0.303}$ frames/slot.

b. Idle: $P(0 \text{ attempts}) = e^{-0.5} = \mathbf{0.607}$. Success: 0.303. Collision: $1 - 0.607 - 0.303 = \mathbf{0.090}$.

c. A given attempt succeeds if no other attempt is in its slot: probability $e^{-G}$. The number of attempts is geometric, so the mean is $\dfrac{G}{S} = e^{G} = e^{0.5} = \mathbf{1.65}$ attempts.

d. Pure ALOHA: $S = Ge^{-2G} = 0.5e^{-1} = \mathbf{0.184}$ (this happens to be pure ALOHA's maximum, $1/(2e)$). It is lower because in pure ALOHA a frame can collide with any frame that **starts within one frame time before or after it** (vulnerable period $2X$), while slotting limits collisions to frames in the **same slot** (vulnerable period $X$).
