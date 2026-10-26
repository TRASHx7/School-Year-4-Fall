# ENEL 573 HW Assignment 3 (Fall 2026): Worked Solutions

Notation follows the Chapter 3 lecture slides (5-70 to 5-73) and the Chapter 2 probability review:

| Symbol | Meaning (as defined in lecture) |
|---|---|
| $L$ | packet length (bits) |
| $R$ | transmission rate (bps) |
| $X = L/R$ | packet transmission time = one time slot |
| $S$ | throughput: average # successful packet transmissions per $X$ sec |
| $G$ | load: average # transmission attempts (new + retransmissions) per $X$ sec |
| $\lambda$ | Poisson arrival rate (packets/sec) |

Key lecture results:

- Pure ALOHA (vulnerable period $2X$): $S = G\,e^{-2G}$, $S_{max} = \frac{1}{2e} = 0.184$ at $G = 0.5$
- Slotted ALOHA (vulnerable period $X$): $S = G\,e^{-G}$, $S_{max} = \frac{1}{e} = 0.368$ at $G = 1$
- Poisson: $P(k \text{ arrivals in } t) = \frac{(\lambda t)^k}{k!}e^{-\lambda t}$
- Geometric: if each trial succeeds with probability $p$, then $P(\text{first success on trial } k) = (1-p)^{k-1}p$ and $E[\text{trials}] = 1/p$

---

## Problem 1 (40 points)

### (a) Maximum number of users $N$ on a 56 kbps pure ALOHA channel

Given: $R = 56$ kbps, $L = 1000$ bits, each user generates packets at Poisson rate $\lambda = \frac{1}{100} = 0.01$ packets/sec.

**Step 1: Slot (packet transmission) time**

$$X = \frac{L}{R} = \frac{1000}{56\,000} = 17.857 \text{ ms}$$

**Step 2: Throughput in packets per $X$ sec**

In steady state, every newly generated packet must eventually get through, so the throughput $S$ equals the total new-packet arrival rate measured per $X$ seconds:

$$S = N\lambda X = N(0.01)(0.017857) = \frac{N}{5600}$$

**Step 3: Apply the pure ALOHA limit**

Pure ALOHA cannot exceed $S_{max} = \frac{1}{2e} = 0.184$:

$$\frac{N}{5600} \le 0.184 \quad\Rightarrow\quad N \le 5600 \times 0.184 = 1030.4$$

$$\boxed{N_{max} = 1030 \text{ users}}$$

(Check in bps: usable capacity $= 0.184 \times 56\,000 = 10\,304$ bps; each user needs $1000/100 = 10$ bps; $10\,304/10 = 1030$ users.)

### (b) Total channel load for 10,000 stations on slotted ALOHA

Given: 10,000 stations, 18 requests/hour each, slot $X = 125\ \mu$s.

**Step 1: Total request rate**

$$\lambda = 10\,000 \times \frac{18}{3600} = 50 \text{ requests/sec}$$

**Step 2: Slots per second**

$$\frac{1}{X} = \frac{1}{125 \times 10^{-6}} = 8000 \text{ slots/sec}$$

**Step 3: Load per slot**

$$G = \lambda X = \frac{50}{8000} = \boxed{G \approx 0.00625 \text{ requests/slot}}$$

This is a very lightly loaded channel. As noted in lecture, for small $G$ we have $S \approx G$ (here $S = Ge^{-G} = 0.00625\,e^{-0.00625} \approx 0.00621$), so retransmissions are negligible and the total load is approximately the new-request load.

---

## Problem 2 (30 points)

Given: total attempts (new + retransmissions) $= 50$ requests/sec, slot $X = 40$ ms.

The load per slot is

$$G = 50 \times 0.040 = 2 \text{ attempts/slot}$$

### (a) Probability of success on the first attempt

A slotted ALOHA transmission succeeds when no other packet is transmitted in the same slot (vulnerable period $X$). With Poisson attempts of mean $G$ per slot:

$$P(\text{success}) = P(0 \text{ other arrivals in } X) = \frac{G^0}{0!}e^{-G} = e^{-G} = e^{-2}$$

$$\boxed{P(\text{success}) = e^{-2} \approx 0.135}$$

### (b) Probability of exactly $k$ collisions and then a success

Each attempt collides with probability $1 - e^{-G}$ and succeeds with probability $e^{-G}$, independently. Exactly $k$ collisions followed by one success (geometric distribution, $k+1$ trials):

$$\boxed{P(k \text{ collisions, then success}) = \left(1 - e^{-G}\right)^k e^{-G} = \left(1 - e^{-2}\right)^k e^{-2} \approx (0.865)^k (0.135)}$$

For example, $k = 0$: $0.135$; $k = 1$: $0.117$.

### (c) Expected number of transmission attempts

Using the hint (average attempts over throughput) with $S = Ge^{-G}$:

$$E[\text{attempts}] = \frac{G}{S} = \frac{G}{G\,e^{-G}} = e^{G} = e^{2}$$

$$\boxed{E[\text{attempts}] = e^2 \approx 7.39}$$

Check with the geometric distribution from Chapter 2: number of trials $n = k + 1$ with success probability $p = e^{-G}$ gives $E[n] = 1/p = e^{G} = 7.39$. Same answer.

---

## Problem 3 (30 points)

Three nodes A, B, C; each transmits in every slot with probability $p$, independently.

A given node succeeds in a slot only if it transmits and the other two do not:

$$P(\text{A succeeds in a slot}) = p(1-p)^2$$

### (a) Node A succeeds for the first time in slot 4

A must fail in slots 1, 2, 3 and succeed in slot 4 (geometric distribution with success probability $p(1-p)^2$):

$$\boxed{P = \left[1 - p(1-p)^2\right]^3 \, p(1-p)^2}$$

### (b) Some node (A, B, or C) succeeds in slot 2

The three single-node success events are mutually exclusive (only one node can succeed in a slot), so add them:

$$\boxed{P(\text{some node succeeds in a slot}) = 3p(1-p)^2}$$

(The slot number does not matter, since slots are independent.)

### (c) The first success occurs in slot 4

Slots 1, 2, 3 must have no success (idle or collision) and slot 4 must have a success:

$$\boxed{P = \left[1 - 3p(1-p)^2\right]^3 \, 3p(1-p)^2}$$

---

## Answer Summary

| Problem | Answer |
|---|---|
| 1(a) | $N_{max} = 1030$ users |
| 1(b) | $G = 0.00625$ requests/slot |
| 2(a) | $e^{-2} \approx 0.135$ |
| 2(b) | $(1-e^{-2})^k e^{-2} \approx (0.865)^k(0.135)$ |
| 2(c) | $e^{2} \approx 7.39$ attempts |
| 3(a) | $[1 - p(1-p)^2]^3\,p(1-p)^2$ |
| 3(b) | $3p(1-p)^2$ |
| 3(c) | $[1 - 3p(1-p)^2]^3\,3p(1-p)^2$ |
