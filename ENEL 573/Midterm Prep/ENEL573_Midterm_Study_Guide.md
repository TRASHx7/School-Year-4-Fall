---
title: "ENEL 573 Computer Networks: Midterm Study Guide"
subtitle: "Fall 2026 · Chapters 1 to 3.5 · Monday Oct 26, 12:00 to 12:50 PM, ENA 101"
---

# ENEL 573 Midterm Study Guide

**Built from:** lecture slides (Ch. 1, 2, 3), HW Assignments 1 to 3, the Sample Midterm, the Practice Questions, the Project 1 and 2 manuals, and Kurose & Ross, *Computer Networking: A Top-Down Approach* (9th ed.).

> **Exam facts (from the course announcements)**
>
> * 50 minutes, closed book, **3 written-response problems**, each with several sub-parts.
> * Non-programmable scientific calculator allowed. Bring your UCID card and a pen.
> * Coverage: **Ch. 1** (network edge, network core, packet vs circuit switching), **Ch. 2** (network analysis and queueing theory), **Ch. 3 up to the end of 3.5** (error detection/correction, retransmission, MAC protocols). Link-layer addressing/ARP (3.6) is **not** on the midterm.
> * Formulas: you are **not** expected to memorize derivations. You **must** know the M/M/1 results and anything at the homework level. Any "complex" formula (for example M/M/1/N blocking) will be given on the exam.

---

## 0. What the exam actually looks like

The sample midterm was built almost entirely from problems you have already seen. Use that as your main hint.

| Sample midterm problem | Topic | Where it came from |
|---|---|---|
| P1 (a to d) | Circuit vs packet switching, binomial probability | Textbook Ch. 1 **P8**, HW1 **P4**, slide 1-36 |
| P2 (1 to 3) | M/M/1 minimum service rate | **Identical** to HW2 **P3** and lecture slide 2-47 |
| P3.1 | CSMA/CD backoff wait time (K × 512 bit times) | Practice **P2(b)**, textbook Ch. 6 **P17** |
| P3.2 | CRC check at the receiver | Practice **P3(a)** |

**Takeaway:** if you can redo every HW problem (HW1 to HW3), every Practice Question, and the sample midterm without notes, you are in very good shape. Section 6 lists the textbook problems that match.

### Tonight's priority checklist (most points per hour first)

1. [ ] M/M/1 formulas (Section 2.4): write them from memory, then redo HW2 P2 and P3.
2. [ ] CRC long division (sender **and** receiver) and 2D parity (HW2 P4).
3. [ ] Delay problems: store-and-forward, message vs packet switching, multi-hop pipelining (HW1 P1, P2, P5; HW2 P1; Practice P4).
4. [ ] ALOHA throughput formulas and the HW3 probability questions; CSMA/CD backoff and collision-detection time.
5. [ ] Stop-and-wait utilization and pipelining window (Practice P1 a to c).
6. [ ] Circuit vs packet switching binomial question (Sample P1).
7. [ ] Concept short answers (Section 7) once you are tired of computing.

---

## 1. Chapter 1: Introduction

### 1.1 What is the Internet?

* **"Nuts and bolts" view:** billions of connected **hosts/end systems**, **communication links** (fiber, copper, radio, satellite) with a **bandwidth** (transmission rate, bps), and **packet switches** (routers, link-layer switches, base stations/APs) that forward packets. The Internet is a **network of networks**, loosely hierarchical.
* **Service view:** an infrastructure that provides services to distributed applications (Web, VoIP, email, games). It offers reliable delivery or "best effort" (unreliable) delivery.
* **Protocol:** defines the **format** and **order** of messages exchanged between entities, and the **actions** taken on transmission/receipt (e.g., TCP, IP, HTTP, Ethernet). Standards: RFCs from the IETF.

### 1.2 Network edge

* **End systems (hosts)** run applications at the edge.
  * **Client/server:** client requests service from an always-on server (Web, email).
  * **Peer-to-peer:** minimal or no dedicated servers.
* **Access networks** connect end systems to the first (edge) router. Always ask: *what bandwidth? shared or dedicated?*

| Access technology | Key facts |
|---|---|
| Dial-up modem | Existing phone line, up to 56 kbps, cannot phone and surf at the same time, not "always on" |
| DSL | Existing phone line to the central office (**dedicated** line), DSLAM; frequency split: 0 to 4 kHz voice, 4 to 50 kHz upstream, 50 kHz to 1 MHz downstream; asymmetric |
| Cable (HFC) | Cable TV infrastructure, hybrid fiber coax, asymmetric; homes **share** the link to the router (unlike DSL) |
| Ethernet | Companies/universities; 10 Mbps to 100 Gbps; shared medium uses **CSMA/CD** |
| Wireless | WLAN (802.11 WiFi) via access point; wide-area cellular (LTE, NB-IoT, LoRaWAN) |

* **Physical media:** *guided* (twisted pair, coax, fiber) vs *unguided* (radio).
  * Twisted pair: Cat 3 (10 Mbps), Cat 5 (100 Mbps), Cat 5e (1 Gbps), Cat 6 (10 Gbps).
  * Coax: baseband (single channel) or broadband (multiple channels, HFC).
  * Fiber: light pulses, very high speed, **low error rate**, immune to EM noise, repeaters far apart.
  * Radio: no wire, affected by reflection, obstruction, interference. Types: terrestrial microwave, WiFi LAN, cellular, satellite (10 to 100 Mbps, long end-to-end delay; geosynchronous vs low-altitude).

### 1.3 Network core: packet switching vs circuit switching

**Packet switching**

* Message is broken into **packets** (header + payload + trailer). Header: source/destination addresses, sequence number. Trailer: error-check bits.
* Each packet uses the **full link rate**; no reservation. Resources used on demand → **statistical multiplexing** (no fixed timing pattern).
* **Store-and-forward:** a node must receive the *entire* packet before it can transmit it on the next link.
* Congestion → packets **queue** (delay) and may be **dropped** (loss) when the buffer is full.
* **Pipelining gain:** splitting a message into small packets lets different links work in parallel, reducing total delivery time.

**Circuit switching**

* End-to-end resources (link bandwidth, switch capacity) **reserved** for the call; **call setup** required; dedicated, no sharing (idle pieces are wasted).
* Link divided into "pieces" by **FDM** (frequency bands) or **TDM** (time slots in a revolving frame).
* **"Circuit-like" (guaranteed) performance:** constant data rate and constant end-to-end delay because resources are reserved along the path.
* No store-and-forward: bits stream through the switches.

| Item | Circuit switching | Packet switching |
|---|---|---|
| Dedicated path | Yes | No |
| Bandwidth available | Fixed | Dynamic |
| Potentially wasted bandwidth | Yes | No |
| Store-and-forward | No | Yes |
| Call setup | Yes | Not needed |
| When can congestion occur | At setup time (call blocked) | On every packet |
| Charging | Per minute | Per packet |
| Each packet follows the same route | Yes | No |

> **Why packet switching supports more users (slide 1-36):** 1 Mbps link, each user needs 100 kbps when active, active 10% of the time. Circuit switching: 10 users. Packet switching with 35 users: P(more than 10 active) ≈ 0.0004. Great for **bursty** data. Circuit switching is better for **steady, long-lived** traffic (e.g., constant-rate streaming, telephone) that needs guaranteed rate/delay.

**Recognizing multiplexing from a capture (Practice P1d):** a strict repeating pattern of owners (A, B, A, B with fixed positions, empty slots when idle) suggests **TDM**; irregular order (e.g., "A A A" back-to-back) means **statistical multiplexing**.

**Internet structure:** tier-1 ISPs (global, peer with each other for free) and large content providers (Google, Akamai) at the center; tier-2 (regional) ISPs pay tier-1 providers and may peer at **IXPs**; tier-3/local ISPs are the access networks.

### 1.4 The way networks work: layering

* **Layering** gives modularity: each layer provides a service to the layer above using the service of the layer below. Layers can be changed independently; heterogeneous systems can interoperate ("open systems").
* **Protocol stack** = set of layers and protocols. **Peer-to-peer protocol** = layer N at source talks to layer N at destination (conceptually) using the lower layers. **Interface** = services a layer provides to the layer above.

| OSI layer | Function |
|---|---|
| 7 Application | Common services: file transfer, directory, virtual terminal |
| 6 Presentation | Compression, security (encryption), format conversion |
| 5 Session | Set up and supervise connections between end systems |
| 4 Transport | End-to-end delivery; may retransmit erroneous packets |
| 3 Network | Route packets from source to destination across many links |
| 2 Data link | Reliable transfer between nodes on the **same physical link** |
| 1 Physical | Raw bit stream over the channel |

* Layers 1 to 3: network support. Layers 5 to 7: user support. Layer 4 links the two.
* **TCP/IP 5-layer stack:** application (HTTP, SMTP, FTP), transport (TCP, UDP), network (IP, routing), link (Ethernet, WiFi MAC), physical.
* **Encapsulation names:** message (application) → **segment** (transport, adds $H_t$) → **datagram** (network, adds $H_n$) → **frame** (link, adds $H_l$ and trailer).
* Switches are layer-2 devices (examine link headers); routers are layer-3 devices (examine network headers). Both are store-and-forward.

### 1.5 Performance: delay, loss, throughput

$$d_{nodal} = d_{proc} + d_{queue} + d_{trans} + d_{prop}$$

| Delay | Formula / meaning |
|---|---|
| Processing $d_{proc}$ | Check bit errors, choose output link; typically under a millisecond |
| Queueing $d_{queue}$ | Waiting for the output link; depends on congestion |
| Transmission $d_{trans}$ | $L/R$: time to **push** all $L$ bits onto a link of rate $R$ |
| Propagation $d_{prop}$ | $d/s$: time for one bit to **travel** a link of length $d$ at speed $s$ (about $2\text{ to }3\times10^8$ m/s) |

* **Caravan analogy:** toll booth service time = transmission delay; driving time between booths = propagation delay. The first bit can reach the next router before the last bit has left the current one (if $d_{prop} < d_{trans}$).
* **Traffic intensity** $La/R$ ($a$ = average packet arrival rate in packets/s). $La/R \approx 0$: small queueing delay. $La/R \to 1$: delay grows very large. $La/R > 1$: queue grows without bound. (This is exactly $\rho = \lambda/\mu$ from Chapter 2.)
* **Loss:** a packet arriving at a full buffer is dropped; may be retransmitted by the previous node, the source, or not at all.
* **Throughput:** rate (bits/s) at which bits are delivered. End-to-end throughput = rate of the **bottleneck link**: $\min(R_1, R_2, \dots)$. With $M$ connections fairly sharing a backbone link $R$: $\min(R_s, R_c, R/M)$.
* **Traceroute:** sends 3 probes to each router on the path and measures round-trip times; `*` = no reply.

> **Key Chapter 1 formulas**
>
> * One packet, $N$ store-and-forward links of rate $R$: $\; d_{end\text{-}end} = N\dfrac{L}{R}$ (plus $\sum d_{prop}$, $\sum d_{proc}$)
> * $P$ packets back-to-back over $N$ equal links: $\; (N + P - 1)\dfrac{L}{R}$ (+ propagation)
> * $P$ packets over links with different rates: $\; \displaystyle\sum_{i}\frac{L}{R_i} + (P-1)\frac{L}{R_{min}}$
> * Message switching (whole file $F$ as one message) over $N$ links: $\; N\dfrac{F}{R}$
> * Circuit switching with $k$ FDM/TDM channels: rate per call $R/k$; time $= t_{setup} + \dfrac{F}{R/k} + d_{prop}$
> * Circuit-switched users: $N = \lfloor R / r_{user} \rfloor$. Packet switching with $M$ users, each active w.p. $p$:
>   $P(\text{exactly } n \text{ active}) = \binom{M}{n}p^n(1-p)^{M-n}$, $\;P(\text{more than } N) = 1 - \sum_{k=0}^{N}\binom{M}{k}p^k(1-p)^{M-k}$
> * Bandwidth-delay product $R \cdot d_{prop}$ = max bits "in flight" on the link; width of one bit $= s/R$ meters.

### 1.6 Chapter 1 worked examples

**E1. HW1 P2 (30 Mbit MP3, 10 Mbps links, 10,000 km, $s = 2\times10^8$ m/s).**

1. $d_{trans} = 30\times10^6 / 10\times10^6 = 3$ s.
2. $d_{prop} = 10^7 / (2\times10^8) = 0.05$ s, so end-to-end $= 3.05$ s.
3. Bits sent when the first bit arrives $= R \cdot d_{prop} = 10^7 \times 0.05 = 500{,}000$ bits.
4. Two links (5,000 km each), one store-and-forward router: $2(3) + 2(0.025) = 6.05$ s.
5. Three 10-Mbit packets, 2 links: $(3 + 2 - 1)(1\text{ s}) + 0.05 = 4.05$ s.
6. 10 FDM channels → 1 Mbps per channel: $30 + 0.05 = 30.05$ s.

**E2. HW2 P1 (message segmentation, 3 links of 1.5 Mbps, 7.5 Mbit message).**

* No segmentation: $7.5\times10^6/1.5\times10^6 = 5$ s per hop, total $3 \times 5 = 15$ s.
* 5,000 packets of 1,500 bits: 1 ms per packet per hop. First packet reaches switch 1 at 1 ms; second packet fully at switch 1 at 2 ms. Whole file: $(5000 + 3 - 1)(1\text{ ms}) = 5.002$ s, about 3 times faster.
* Drawbacks of segmentation: header overhead per packet, packets must be sequenced and reassembled, more processing, more chance one packet is lost.

**E3. HW1 P1 (two nodes between A and B ⇒ 3 links, $M = 15$ MB, $C = 12$ Mbps).**

* Message switching: $3 \times \dfrac{8M}{C} = 3 \times \dfrac{120\times10^6}{12\times10^6} = 30$ s.
* Packet switching with $L = 9600$ bits: $P = 120\times10^6/9600 = 12{,}500$ packets; $(P + 2)\dfrac{L}{C} = 12{,}502 \times 0.8\text{ ms} = 10.0016$ s.

**E4. HW1 P3 / textbook P6 (where is the bit?).** At $t = d_{trans}$ the last bit has just left Host A. If $d_{prop} > d_{trans}$, the first bit is in the link, $s \cdot d_{trans}$ meters from A. If $d_{prop} < d_{trans}$, the first bit has already reached B. Setting $d_{prop} = d_{trans}$: $m = Ls/R$ (e.g., $L = 1000$, $R = 284$ kbps, $s = 2.5\times10^8$ gives $m \approx 880$ km).

**E5. HW1 P5 (two links, $d_{proc} = 1$ ms, 1,000 bytes, 1 Mbps, 4,000 km + 1,000 km, $s = 2.5\times10^8$).**
$d = \dfrac{L}{R_1} + \dfrac{d_1}{s_1} + d_{proc} + \dfrac{L}{R_2} + \dfrac{d_2}{s_2} = 8 + 16 + 1 + 8 + 4 = 37$ ms.

**E6. Practice P4 (broadcast through switches, 100 KB file, 1 KB packets).** A to S1 = 10 Mbps, S1 to S2 = 10 Mbps, S1 to D = 1 Mbps, S2 to C = 2 Mbps, S2 to B = 4 Mbps. One 1 KB packet takes 0.8 ms on 10 Mbps, 2 ms on 4 Mbps, 4 ms on 2 Mbps, 8 ms on 1 Mbps.

* First packet at D: $0.8 + 8 = 8.8$ ms. At C: $0.8 + 0.8 + 4 = 5.6$ ms. At B: $0.8 + 0.8 + 2 = 3.6$ ms.
* Whole file at C: $5.6 + 99 \times 4 = 401.6$ ms. At B: $3.6 + 99 \times 2 = 201.6$ ms.
* Throughput: C ≈ 249 KB/s, B ≈ 496 KB/s. B is better because its bottleneck (4 Mbps) is faster than C's (2 Mbps).
* **Trap:** after the first packet, packets arrive every $L/R_{min}$, where $R_{min}$ is the slowest link on the path, which is not always the last link.

**E7. Sample P1 (2 Mbps link, users need 300 kbps, active 12%).** (a) $\lfloor 2000/300 \rfloor = 6$ users. (b) $p = 0.12$. (c) $\binom{M}{n}(0.12)^n(0.88)^{M-n}$. (d) $P(\ge 7) = 1 - \sum_{k=0}^{6}\binom{M}{k}(0.12)^k(0.88)^{M-k}$.

---

## 2. Chapter 2: Network Analysis and Queueing Theory

### 2.1 Why model networks?

* "Analyze first, build later": a model is a mathematical abstraction that keeps only the relevant details.
* Uses: **evaluate** performance (average waiting time, throughput, loss probability from buffer overflow) and **improve** it (choose a service rate for a tolerable delay, size a buffer for a target loss probability).
* **Randomness at the source:** random data generation (web browsing), voice on/off talk spurts, variable video frame sizes. **Randomness in the network:** changing wireless channels, congestion (statistical multiplexing), contention among users. **Buffers** absorb this randomness.

### 2.2 Probability review

* $P(E) = \lim_{n\to\infty} n(E)/n$ (relative frequency).
* Conditional: $P(E \mid F) = \dfrac{P(E \cap F)}{P(F)}$. Joint: $P(E\cap F) = P(E\mid F)P(F)$. Independent: $P(A \cap B) = P(A)P(B)$.
* **Total probability** (for a partition $E_1,\dots,E_n$): $P(A) = \sum_i P(A\mid E_i)P(E_i)$.
* CDF $F(x) = P(X \le x)$; pdf $f(x) = dF/dx$; pmf $p(x_i) = P(X = x_i)$.
* $E[X] = \sum x_i p(x_i)$ or $\int x f(x)dx$; $\text{Var}(X) = E[X^2] - (E[X])^2$.

| Distribution | pmf / pdf | Mean | Variance | Network use |
|---|---|---|---|---|
| Binomial$(n,p)$ | $\binom{n}{k}p^k(1-p)^{n-k}$ | $np$ | $np(1-p)$ | # active users; # bit errors in a packet |
| Geometric$(p)$ | $(1-p)^{k-1}p,\; k\ge1$ | $1/p$ | $(1-p)/p^2$ | # transmissions until first success |
| Poisson$(\lambda)$ | $\dfrac{\lambda^k e^{-\lambda}}{k!}$ | $\lambda$ | $\lambda$ | # arrivals in a unit interval |
| Exponential$(\lambda)$ | $\lambda e^{-\lambda x},\; x\ge0$; CDF $1 - e^{-\lambda x}$ | $1/\lambda$ | $1/\lambda^2$ | inter-arrival and service times |

**Examples from the slides**

* Packet of $n$ bits, bit error probability $p_B$: $P(\text{no error}) = (1-p_B)^n$; $P(\text{exactly one}) = n p_B(1-p_B)^{n-1}$; $P(\text{packet corrupted}) = 1 - (1-p_B)^n$.
* Stop-and-wait, loss probability $p_E$: $P(\text{need exactly 3 transmissions}) = p_E^2(1-p_E)$; average transmissions $= \dfrac{1}{1-p_E}$.
* **Memoryless property** (exponential only): $P(X > x + t \mid X > t) = P(X > x)$.
* Bank example (time in bank exponential, mean 10 min, $\mu = 1/10$): $P(X > 15) = e^{-1.5} \approx 0.223$. Given still there after 10 min, $P(X > 15 \mid X > 10) = P(X > 5) = e^{-0.5} \approx 0.607$.
* **Poisson process** with rate $\lambda$: number of arrivals in an interval of length $t$ is Poisson with mean $\lambda t$: $P(X(t) = k) = \dfrac{e^{-\lambda t}(\lambda t)^k}{k!}$. Inter-arrival times are i.i.d. exponential($\lambda$), because $P(\tau \le s) = 1 - P(\text{no arrival in } s) = 1 - e^{-\lambda s}$.
* **Generating exponential samples (Project 1):** inverse transform. If $U \sim U(0,1)$, then $X = -\dfrac{1}{\lambda}\ln(1 - U)$ (equivalently $-\ln U/\lambda$) is exponential($\lambda$).

### 2.3 Queueing basics

* Single-server queue: arrivals → buffer → server (the transmission link). Service time is proportional to packet length.
* Multi-server: an arrival goes to any empty server.
* **Kendall notation A/S/C/K:** A = arrival process, S = service time distribution, C = number of servers, K = max number in the system (buffer + servers, infinite if omitted). **M** = Markovian (Poisson arrivals / exponential times, memoryless). G = general.
  * M/M/1: Poisson arrivals, exponential service, 1 server, infinite buffer.
  * M/M/1/N: same, at most $N$ in the system. M/M/m: $m$ servers. M/M/m/m: $m$ servers, no waiting room. G/G/1: general.

### 2.4 The M/M/1 queue (KNOW THIS COLD)

**Setup.** Arrival rate $\lambda$ (Poisson), service rate $\mu$ (exponential, mean service time $1/\mu$), $\rho = \lambda/\mu < 1$ for stability.

**Derivation outline.** Birth-death chain on states $0, 1, 2, \dots$ ($\lambda$ up, $\mu$ down). Balance (flow in = flow out):
$\lambda P_0 = \mu P_1$ and $(\lambda + \mu)P_n = \lambda P_{n-1} + \mu P_{n+1}$ for $n \ge 1$. This gives $P_n = \rho^n P_0$; normalizing $\sum P_n = 1$ gives $P_0 = 1 - \rho$.

> | Quantity | Result |
> |---|---|
> | Utilization (P server busy) | $\rho = \lambda/\mu$ |
> | P(system empty / server idle) | $P_0 = 1 - \rho$ |
> | P(exactly $n$ in system) | $P_n = (1-\rho)\rho^n$ |
> | P(at least $n$ in system) | $P(N \ge n) = \rho^n$ |
> | Avg number in system | $L = E[N] = \dfrac{\rho}{1-\rho} = \dfrac{\lambda}{\mu - \lambda}$ |
> | Avg number waiting in queue | $E[N_q] = \dfrac{\rho^2}{1-\rho} = \dfrac{\lambda^2}{\mu(\mu-\lambda)}$ |
> | Avg time in system | $W = \dfrac{1}{\mu - \lambda}$ |
> | Avg waiting time in queue | $T_q = W_q = \dfrac{\rho}{\mu - \lambda} = \dfrac{\lambda}{\mu(\mu-\lambda)}$ |
> | Relationship | $W = T_q + \dfrac{1}{\mu}$ |
>
> **Little's Law** (any stable system): $E[N] = \lambda W$ and $E[N_q] = \lambda T_q$.

* **Units:** if packets have mean length $\bar L$ bits and the link is $C$ bps, then $\mu = C/\bar L$ packets/s. Keep $\lambda$ and $\mu$ in the **same** units.
* **"Queue" wording trap:** "at least 20 people **in the queue**" (waiting) means at least 21 **in the system**: $P(N \ge 21) = \rho^{21}$. "Queue length" in the sample solution means $E[N_q]$.
* **Example 2.2 (scaling):** multiply both $\lambda$ and $\mu$ by $k$: $L = \dfrac{k\lambda}{k\mu - k\lambda} = \dfrac{\lambda}{\mu-\lambda}$ is unchanged, but $W = \dfrac{1}{k(\mu - \lambda)}$ is $k$ times smaller. This is why **statistical multiplexing beats TDM/FDM**: one fast shared queue beats $k$ slow dedicated queues.

### 2.5 M/M/1/N (finite buffer): formula likely provided on the exam

* At most $N$ packets in the system; arrivals that find the system full are **blocked (dropped)**.
* $P_n = \dfrac{1-\rho}{1-\rho^{N+1}}\rho^n$ for $0 \le n \le N$ (valid for any $\rho \ne 1$, even $\rho > 1$). If $\rho = 1$: $P_n = \dfrac{1}{N+1}$.
* **Blocking probability** $P_B = P_N = \dfrac{(1-\rho)\rho^N}{1-\rho^{N+1}}$.
* **Throughput** $= \lambda(1 - P_B) = \mu(1 - P_0)$.

### 2.6 Networks of M/M/1 queues

* Each router $i$ is an M/M/1 queue with total arrival rate $\lambda_i$ = sum of all flows $\gamma_j$ passing through it (assume independence).
* $E[N_i] = \dfrac{\lambda_i}{\mu_i - \lambda_i}$; total $E[N] = \sum_i \dfrac{\lambda_i}{\mu_i - \lambda_i}$.
* Average end-to-end delay (Little): $E[T] = \dfrac{E[N]}{\lambda}$, where $\lambda = \sum_j \gamma_j$ is the total **external** arrival rate.
* Example: $\gamma_1 = 10$, $\gamma_2 = 5$, $\gamma_3 = 5$ packets/s, all $\mu_i = 30$; $\lambda_1 = \gamma_1 + \gamma_2 = 15$, $\lambda_2 = \gamma_1+\gamma_2+\gamma_3 = 20$, $\lambda_3 = \gamma_1+\gamma_3 = 15$. $E[N] = 1 + 2 + 1 = 4$, $E[T] = 4/20 = 0.2$ s.

### 2.7 Chapter 2 worked examples

**E8. HW2 P3 = Sample P2 ($\lambda = 15$/hr, find minimum $\mu$).**

1. Idle at least 10%: $P_0 = 1 - \rho \ge 0.1 \Rightarrow \lambda/\mu \le 0.9 \Rightarrow \mu \ge 15/0.9 = 16.67$/hr.
2. $E[N_q] = \dfrac{\lambda^2}{\mu(\mu-\lambda)} \le 10 \Rightarrow 225 \le 10\mu^2 - 150\mu \Rightarrow \mu^2 - 15\mu - 22.5 \ge 0 \Rightarrow \mu \ge \dfrac{15 + \sqrt{315}}{2} = 16.374$/hr (slides round to 16.375).
3. At least 20 in queue = at least 21 in system: $\rho^{21} \le 0.5 \Rightarrow \rho \le 0.5^{1/21} = e^{\ln(0.5)/21} = 0.96753 \Rightarrow \mu \ge 15/0.96753 = 15.50$/hr.
4. Overall minimum to satisfy **all** three: the largest, $\mu \ge 16.67$/hr.

**E9. HW2 P2 (50 kbps line, 10 sessions, 150 packets/min each, mean 1000 bits).** Per session $\lambda = 2.5$ packets/s.

* (i) **TDM**, 10 channels of 5 kbps: $\mu = 5$ packets/s, $\rho = 0.5$. $E[N_q] = 0.5$, $E[N] = 1$, $W = 1/(5 - 2.5) = 0.4$ s per session.
* (ii) **Statistical multiplexing**, one 50 kbps queue: $\lambda = 25$, $\mu = 50$, $\rho = 0.5$. Whole system: $E[N_q] = 0.5$, $E[N] = 1$, $W = 1/25 = 0.04$ s. Per session (by Little): $E[N] = 2.5 \times 0.04 = 0.1$, $E[N_q] = 0.05$.
* Same $\rho$, but delay is **10 times smaller** with statistical multiplexing (Example 2.2 with $k = 10$).

**E10. M/M/1/N.** $\rho = 0.5$, $N = 3$: $P_B = \dfrac{0.5 \times 0.125}{1 - 0.0625} = 0.0667$; throughput $= 0.933\lambda$.

---

## 3. Chapter 3: Data Link Layer (3.1 to 3.5)

### 3.1 Services

* Nodes = hosts and routers; links = channels between adjacent nodes; layer-2 packet = **frame** (encapsulates a datagram).
* Services: **framing**, **link access** (MAC for shared media), **reliable delivery** between adjacent nodes (mostly on high-error wireless links; rarely on fiber), **flow control**, **error detection**, **error correction**.
* Why both link-level and end-to-end reliability? Link-level recovery is faster/local on noisy links; end-to-end is still needed for losses inside routers/the network.
* Implemented in the **network adapter (NIC)**: hardware + software + firmware. Sender encapsulates and adds error-check bits; receiver checks errors, extracts the datagram.

### 3.2 Framing

* Why frames: big blocks have a higher error probability, only small pieces need retransmission, and small frames stop one node hogging a shared medium.
* **Fixed-size** framing: hard to resynchronize after bit loss. **Variable-size**: byte count or flags.
* **Byte count:** header field gives the frame length; if the count is corrupted the receiver loses sync.
* **Flag + bit stuffing:** frames start and end with flag `01111110`. Sender inserts a `0` after every five consecutive `1`s in the data. Receiver: after five `1`s, next bit `0` → remove it (stuffed); next bits `10` → flag; next bits `11` → error.
  * Example: data `0111111111100` → stuffed `011111011111000` (a 0 inserted after each run of five 1s).

### 3.3 Error detection and correction

* Errors from noise/interference; BER (e.g., $10^{-6}$). **Single-bit** vs **burst** errors (two or more bits, not necessarily consecutive). Bursts are more likely: bits affected = rate × noise duration (1/100 s of noise hits 10 bits at 1 kbps, 10,000 bits at 1 Mbps).
* **Detection** (low overhead, retransmit on error; fine on fiber/copper) vs **correction** (FEC, more overhead; used on noisy wireless links). More redundancy = better detection but more overhead. Detection is never 100% reliable.
* Frame of $m$ data bits + $r$ redundant bits = $n$ bits.

**Single parity check**

* **Even parity:** parity bit makes the total number of 1s even. **Odd parity:** makes it odd.
* Detects **all odd numbers** of bit errors (so all single-bit errors); misses all even numbers. Overhead $1/(k+1)$.
* For $N_b$ bits with bit error probability $P_b$: $P_1 = (1-P_b)^{N_b}$ (no error); $P_2 = \sum_{i=1}^{\lfloor N_b/2\rfloor}\binom{N_b}{2i}P_b^{2i}(1-P_b)^{N_b-2i}$ (undetected); $P_3 = 1 - P_1 - P_2$ (detected).
* Frame of $n$ bytes, each with its own parity bit: $P_{f1} = P_1^n$; $P_{f2} = \sum_{i=1}^{n}\binom{n}{i}P_2^i(1-P_2)^{n-i}$; $P_{f3} = 1 - P_{f1} - P_{f2}$.

**Two-dimensional parity**

* Arrange data as $n$ rows × $m$ columns; add one parity bit per row, one per column, and one corner bit: $mn + m + n + 1$ total bits.
* **Corrects any single-bit error** (the failing row and column intersect at the bad bit). **Detects** any 2 or 3 errors. Some 4-bit patterns (rectangle corners) are **undetectable**.

**E11. HW2 P4.**

* `11010111` has six 1s: even parity bit **0**, odd parity bit **1**. `10001010` has three 1s: even parity bit **1**, odd parity bit **0**.
* 2D even parity of `11010010 11100011 00111011` (3 × 8):

| Row | Data | Row parity |
|---|---|---|
| 1 | 1 1 0 1 0 0 1 0 | 0 |
| 2 | 1 1 1 0 0 0 1 1 | 1 |
| 3 | 0 0 1 1 1 0 1 1 | 1 |
| Column parity | 0 0 0 0 1 0 1 0 | **0** (corner) |

* Received `11010010 11110011 00111011`: row 2 parity fails (six 1s, expected odd) and column 4 parity fails (three 1s). The single error is at **row 2, column 4**; flip it back to 0. 2D parity detects and corrects this single-bit error.

**Cyclic Redundancy Check (CRC)**

* Generator $G$ has $r + 1$ bits (degree $r$, first and last bit 1); both sides know $G$.
* **Sender:** append $r$ zeros to $D$, divide by $G$ with **modulo-2 (XOR, no carries/borrows)** division; the $r$-bit remainder is $R$. Send $\langle D, R\rangle$, which is exactly divisible by $G$.
* **Receiver:** divide the whole received string by $G$. Remainder all zeros → accept; nonzero → **error detected**.
* Division rules: if the leading bit of the current window is 1, XOR with $G$; if 0, XOR with zeros (i.e., just shift). Drop the leading bit each step.
* Properties: detects **all single-bit errors**, **all burst errors of length $\le r$**, all double-bit errors if $G$ is chosen well, all odd numbers of errors if $G$ has factor $(x+1)$. Undetectable: error polynomials $E(x)$ that are multiples of $G(x)$. CRC-16 detects 100% of bursts up to 16 bits, 99.997% of 17-bit bursts. Easy in hardware (shift register + XOR).
* Polynomial view: `110001` $= x^5 + x^4 + 1$.

**E12. CRC sender (slide example):** $D = 101110$, $G = 1001$ ($r = 3$), so divide `101110` + `000` = `101110000` by `1001`. Work 4 bits at a time:

| Step | Current 4-bit window | Leading bit | XOR with | Result | Keep last 3 bits, bring down next bit |
|---|---|---|---|---|---|
| 1 | 1011 | 1 | 1001 | 0010 | 010 + **1** = 0101 |
| 2 | 0101 | 0 | 0000 | 0101 | 101 + **0** = 1010 |
| 3 | 1010 | 1 | 1001 | 0011 | 011 + **0** = 0110 |
| 4 | 0110 | 0 | 0000 | 0110 | 110 + **0** = 1100 |
| 5 | 1100 | 1 | 1001 | 0101 | 101 + **0** = 1010 |
| 6 | 1010 | 1 | 1001 | 0011 | no bits left: $R$ = **011** |

Transmitted: `101110 011`. (Slide example 2: $D = 1100$, $G = 1011$ gives $R = 010$.)

**E13. CRC receiver (Sample P3.2):** received `1010110`, $G = 10011$. Dividing gives remainder `1001` ≠ 0, so the frame was **not** received correctly.

### 3.4 Retransmission (ARQ) and flow control

ARQ goal: deliver data **without errors, in order, without duplicates**. Tools: error detection, **ACKs**, **timeouts**, **sequence numbers**.

**Stop-and-wait (= Alternating Bit Protocol, ABP; Project 2)**

* Send one frame, wait for ACK. No ACK before timeout → resend. Timeout must exceed the round-trip time.
* Lost **ACK** → sender resends → receiver would get a **duplicate**, so frames need sequence numbers (1 bit, mod 2).
* **Premature timeout / delayed ACK** → ACKs must be numbered too (1 bit). ACK carries the **next expected** sequence number.
* **Piggybacking:** in two-way traffic put the ACK in the header of a data frame to save overhead.

**Stop-and-wait throughput** ($t_I = L/C$ data frame time, $\tau$ = one-way propagation, $t_A$ = ACK time)

$$t_T = t_I + 2\tau + t_A, \qquad \lambda_{max} = \frac{1}{t_T}\text{ frames/s}, \qquad U = \frac{t_I}{t_T}$$

* With frame **or** ACK error probability $p$ (timeout = $t_T$): the number of attempts is geometric, average time per success $t_v = \dfrac{t_T}{1-p}$, so $\lambda_{max} = \dfrac{1-p}{t_T}$. Average transmissions $= \dfrac{1}{1-p}$.
* Slide examples (1500-byte data and ACK, 1 Mbps, $t_I = t_A = 12$ ms): land line 100 km → $t_T = 25$ ms, $U = 48\%$, 0.48 Mbps. Satellite 71,600 km → $t_T = 503.4$ ms, $U = 2.4\%$, 24 kbps. Stop-and-wait wastes long or fast links.

**Pipelining (sliding window)**

* Allow up to $W$ un-ACKed frames in flight. To keep the link 100% busy: $W \ge \dfrac{t_T}{t_I} = \dfrac{t_I + 2\tau + t_A}{t_I}$. Otherwise $U = \dfrac{W t_I}{t_T}$.
* **Go-Back-N:** sender window up to $2^m - 1$ ($m$ sequence bits); one timer (oldest un-ACKed); receiver window = 1 (no out-of-order buffering, cumulative ACK of next expected frame); on timeout or full window, **resend all** outstanding frames. Poor on noisy links.
* **Selective Repeat:** receiver window > 1 buffers out-of-order frames; a **NAK** (or individual timer) triggers retransmission of only the missing frame. (Textbook: window $\le 2^{m-1}$.)
* **Flow control:** receiver slows the sender by delaying ACKs, negotiating window size at setup, or changing window size during the session.

**E14. Practice P1 (Earth to Mars, 54.6 million km, 1.5 KB frames, 10 Mbps, $c = 3\times10^8$).**

* $t_I = 12{,}000/10^7 = 1.2$ ms. $\tau = 5.46\times10^{10}/3\times10^8 = 182$ s. Copy one frame ≈ 182.0012 s.
* Max frames before waiting for an ACK: $\dfrac{t_I + 2\tau}{t_I} = \dfrac{364.0012}{0.0012} \approx 303{,}334$ frames.

### 3.5 Multiple access (MAC) protocols

* **Point-to-point** (PPP) vs **broadcast** (shared Ethernet, WiFi, satellite). Two simultaneous transmissions → **collision** at the receiver. The MAC protocol is a distributed algorithm deciding who transmits; coordination must use the channel itself.
* **Ideal MAC** (rate $R$): one node sends at $R$; $M$ nodes average $R/M$ each; fully decentralized (no master, no clock sync); simple.

| Class | Examples | Notes |
|---|---|---|
| Channel partitioning | TDMA, FDMA, CDMA | Fixed share $R/N$; idle slots/bands wasted; no collisions; common in cellular |
| Random access | Pure ALOHA, slotted ALOHA, CSMA, CSMA/CD, CSMA/CA | Full rate $R$, collisions possible, need detection + random backoff |
| Taking turns | Polling, token passing | Polling: master invites slaves (overhead, latency, single point of failure). Token: token overhead, latency, token loss |

**ALOHA analysis** ($X = L/R$ = frame time; $G$ = attempts per $X$ (new + retransmissions, Poisson); $S$ = successes per $X$)

| | Pure ALOHA | Slotted ALOHA |
|---|---|---|
| Transmit when | Any time | Only at slot starts (needs clock sync) |
| Vulnerable period | $2X$ | $X$ |
| Throughput | $S = Ge^{-2G}$ | $S = Ge^{-G}$ |
| Maximum | $\dfrac{1}{2e} \approx 0.184$ at $G = 0.5$ | $\dfrac{1}{e} \approx 0.368$ at $G = 1$ |
| Finite $N$ nodes, prob $p$ | $Np(1-p)^{2(N-1)}$ | $Np(1-p)^{N-1}$, best $p = 1/N$ |

* **Why slotted beats pure (Practice P3b):** in pure ALOHA a frame collides with any frame that started within $X$ before **or** after it ($2X$ vulnerable window). Slotting forces starts to slot boundaries, so only frames in the same slot collide ($X$ window).
* Slotted ALOHA with Poisson load $G$ per slot: $P(\text{idle}) = e^{-G}$, $P(\text{success}) = Ge^{-G}$, $P(\text{collision}) = 1 - e^{-G} - Ge^{-G}$.
* Probability a given attempt succeeds $= e^{-G}$ (slotted). Probability of exactly $k$ collisions then a success $= (1 - e^{-G})^k e^{-G}$. Expected attempts per success $= G/S = e^{G}$ (pure: $e^{2G}$).
* For small $G$, $S \approx G$; for large $G$, many backlogged users and $S \to 0$.
* **Pure ALOHA receiver (Practice P3c):** wait for a frame; check bit errors; if none, deliver data up and send an ACK; otherwise discard; repeat.

**E15. HW3 P1.** (a) Each user: 1000 bits / 100 s = 10 bps. Max $= 0.184 \times 56{,}000 = 10{,}304$ bps, so $N = 1030$ users. (b) $10{,}000 \times 18 / 3600 = 50$ requests/s; slots/s $= 1/125\,\mu s = 8000$; $G = 50/8000 = 0.00625$ requests/slot.

**E16. HW3 P2 ($G$ = 50 req/s × 40 ms = 2 per slot).** (a) $e^{-2} = 0.135$. (b) $(1 - e^{-2})^k e^{-2} = 0.865^k(0.135)$. (c) $e^{2} \approx 7.39$ attempts.

**E17. HW3 P3 (3 nodes, each transmits w.p. $p$).** One given node succeeds in a slot: $p(1-p)^2$. (a) A's first success in slot 4: $[1 - p(1-p)^2]^3\,p(1-p)^2$. (b) Some node succeeds in slot 2: $3p(1-p)^2$. (c) First success (any node) in slot 4: $[1 - 3p(1-p)^2]^3\,3p(1-p)^2$.

**E18. Practice P5 (Poisson $n$ with mean $\bar n$, each sends w.p. $1/\bar n$).** $P(\text{idle}) = \sum_k (1 - 1/\bar n)^k e^{-\bar n}\bar n^k/k! = e^{-1}$, and $P(\text{success}) = e^{-1}$.

**CSMA family**

* **CSMA:** listen before talking; if busy wait (or back off), if idle transmit. Collisions still happen because of **propagation delay** (vulnerable period $\approx t_{prop}$). A collision wastes the whole frame time. If $t_{prop} > X$, no gain over ALOHA.
* **CSMA/CD (Ethernet, IEEE 802.3):** (1) wait until idle; (2) transmit and **listen while transmitting**; (3) on collision **abort**, wait a random backoff, go to (1). Wastes only the detection time instead of the whole frame.
  * Worst-case collision detection time $= 2t_{prop}$ (B starts just before A's first bit arrives).
  * **Minimum frame size:** to be sure a collision is seen while still transmitting, $L/R \ge 2t_{prop}$ (Ethernet: 512 bits = 64 bytes).
  * **Backoff:** wait $K \times 512$ bit times, bit time $= 1/R$. Binary exponential backoff (textbook): after the $n$th collision choose $K$ uniformly from $\{0, 1, \dots, 2^n - 1\}$ (cap $n$ at 10).
  * Textbook efficiency: $\dfrac{1}{1 + 5t_{prop}/t_{trans}}$ (goes to 1 as $t_{prop} \to 0$ or frames get long).
* **CSMA/CA (802.11 WiFi):** exchange **RTS / CTS / DATA / ACK**. Short control frames make collisions cheap; RTS/CTS gives "virtual" carrier sense against the **hidden terminal** problem. Less efficient than CSMA/CD. ACKs are needed because a wireless sender cannot detect collisions at the receiver.

**E19. Sample P3.1 / Practice P2b:** $K = 100$ at 100 Mbps: $100 \times 512 \times 10^{-8} = 512\ \mu$s (at 1 Gbps: 51.2 μs).

**E20. Practice P2c:** collision detected after 60 bytes (480 bits) on 10 Mbps, longest ever ⇒ $2t_{prop} = 480$ bit times ⇒ $t_{prop} = 240$ bit times $= 240 \times 10^{-7} = 24\ \mu$s.

**E21. Practice P2a:** 2,500 km fiber at $2.5\times10^8$ m/s, 2 Mbps, 1000 bytes: $t_{prop} = 10$ ms, $t_{trans} = 4$ ms, total 14 ms.

**E22. Practice P1f:** most collisions among {pure ALOHA, slotted ALOHA, CSMA/CD}: **pure ALOHA**.

---

## 4. One-page formula sheet

| Topic | Formula |
|---|---|
| Transmission delay | $d_{trans} = L/R$ |
| Propagation delay | $d_{prop} = d/s$ |
| Nodal delay | $d_{proc} + d_{queue} + d_{trans} + d_{prop}$ |
| $P$ packets, $N$ equal links | $(N + P - 1)L/R + \sum d_{prop}$ |
| Different link rates | $\sum_i L/R_i + (P-1)L/R_{min}$ |
| Traffic intensity | $La/R = \rho$ |
| Bandwidth-delay product | $R \cdot d_{prop}$ |
| Binomial | $\binom{M}{n}p^n(1-p)^{M-n}$ |
| Poisson | $\lambda^k e^{-\lambda}/k!$, process: $(\lambda t)^k e^{-\lambda t}/k!$ |
| Exponential | $f = \lambda e^{-\lambda x}$, $P(X > x) = e^{-\lambda x}$, mean $1/\lambda$ |
| M/M/1 | $P_n = (1-\rho)\rho^n$, $P(N\ge n) = \rho^n$, $L = \rho/(1-\rho)$, $L_q = \rho^2/(1-\rho)$, $W = 1/(\mu-\lambda)$, $W_q = \rho/(\mu-\lambda)$ |
| Little | $L = \lambda W$, $L_q = \lambda W_q$ |
| M/M/1/N | $P_B = (1-\rho)\rho^N/(1-\rho^{N+1})$; throughput $\lambda(1 - P_B)$ |
| Queue network | $E[N] = \sum \lambda_i/(\mu_i - \lambda_i)$, $E[T] = E[N]/\sum\gamma_j$ |
| 2D parity bits | $mn + m + n + 1$ total |
| Stop-and-wait | $t_T = t_I + 2\tau + t_A$, $U = t_I/t_T$, $\lambda_{max} = (1-p)/t_T$ |
| Window to fill pipe | $W \ge t_T/t_I$; GBN window $\le 2^m - 1$ |
| Pure ALOHA | $S = Ge^{-2G}$, max $1/(2e) = 18.4\%$ |
| Slotted ALOHA | $S = Ge^{-G}$, max $1/e = 36.8\%$; idle $e^{-G}$; attempts per success $e^G$ |
| CSMA/CD | detect within $2t_{prop}$; $L_{min} = 2t_{prop}R$; wait $K \cdot 512/R$ |

---

## 5. Common mistakes to avoid

1. **Bits vs bytes.** Multiply bytes by 8. In this course 1 KB = 1000 bytes and 1 Mbps = $10^6$ bps (the practice solutions use 1.5 KB = 12 kbits).
2. **Mixing up transmission and propagation delay.** Transmission depends on $L$ and $R$; propagation depends on distance and speed only.
3. **Forgetting store-and-forward:** each hop adds a full $L/R$ for the first packet. Circuit switching does **not** store-and-forward.
4. **Using the last link as the bottleneck** when a slower link is earlier on the path.
5. **Queue vs system:** "in the queue" excludes the packet in service; $N_q = N - 1$ when busy. Use $E[N_q]$ vs $E[N]$ correctly and translate "at least $k$ in queue" to $N \ge k + 1$.
6. **Unstable queue:** M/M/1 formulas need $\lambda < \mu$. If $\rho \ge 1$ the delay is infinite.
7. **$\lambda$ and $\mu$ in different units** (per hour vs per minute, packets vs bits).
8. **CRC:** append exactly $r$ zeros (one less than the length of $G$) at the sender; do **not** append zeros at the receiver. Use XOR, never subtraction with borrows. The remainder always has $r$ bits.
9. **Parity:** even parity makes the total count of 1s (data + parity) even.
10. **ALOHA $G$:** convert requests/second into requests per slot (multiply by slot length).
11. **CSMA/CD bit time:** $1/R$. 512 bit times at 100 Mbps = 5.12 μs.
12. Answer the "justify" part: the sample marks expect a one-line reason (e.g., "remainder ≠ 0 so error").

---

## 6. Textbook practice (Kurose & Ross, 9th ed.)

| Topic | Problems |
|---|---|
| Delays, store-and-forward, pipelining | Ch. 1 P2, P5, P6, P7, P10, P11, P12, P13 |
| Circuit vs packet switching | Ch. 1 P3, P4, P8, P9 |
| Queueing delay, Little's law | Ch. 1 P13, P14, P15, P16 |
| Throughput, bandwidth-delay | Ch. 1 P20, P21, P23, P25, P27, P28 |
| Parity, CRC | Ch. 6 P1, P2, P5, P6, P7 |
| ALOHA | Ch. 6 P8, P9, P10, P11 |
| CSMA/CD | Ch. 6 P17, P18, P19, review R4, R6 |
| Stop-and-wait / GBN / SR (Section 3.4.2 to 3.4.4) | Ch. 3 P15 (window for 98% utilization), P22 (GBN windows), P23 (SR window vs sequence space) |

Quick answers for self-checking: Ch. 6 P5 ($D = 1010101010$, $G = 10011$) gives $R = 0100$. Ch. 6 P8: $p^* = 1/N$, efficiency $\to 1/e$. Ch. 6 R6: after the 5th collision $P(K = 4) = 1/32$; $K = 4$ at 10 Mbps is $4 \times 512 \times 0.1\ \mu s = 204.8\ \mu$s.

---

## 7. Concept self-test (cover the answers)

1. **Packet vs circuit switching: which allows more users and why?** Packet switching, through statistical multiplexing: bursty users rarely all transmit at once, so capacity is shared on demand.
2. **What is "circuit-like" behavior?** Guaranteed performance (constant rate, constant delay) from resources reserved along the path.
3. **Name the four delay components.** Processing, queueing, transmission, propagation.
4. **What happens as traffic intensity approaches 1?** Average queueing delay grows without bound.
5. **What does "M" mean in M/M/1?** Markovian (memoryless): Poisson arrivals and exponential service times.
6. **State Little's law.** $E[N] = \lambda W$ (average number = arrival rate × average time in system).
7. **Why does statistical multiplexing give lower delay than TDM at the same load?** Scaling $\lambda$ and $\mu$ by $k$ keeps $L$ fixed but divides $W$ by $k$ (Example 2.2).
8. **What error patterns does single parity miss?** Any even number of bit errors.
9. **What can 2D parity do that single parity cannot?** Locate and correct any single-bit error.
10. **Which bursts does CRC always detect?** All bursts of length $\le r$ (the degree of $G$).
11. **Why does stop-and-wait need sequence numbers?** To detect duplicate frames when an ACK is lost or a timeout is premature (1 bit suffices).
12. **Go-Back-N vs Selective Repeat?** GBN receiver discards out-of-order frames and the sender resends the whole window; SR buffers out-of-order frames and resends only the missing ones.
13. **Three classes of MAC protocols?** Channel partitioning, random access, taking turns.
14. **Why is slotted ALOHA twice as efficient as pure ALOHA?** Vulnerable period drops from $2X$ to $X$.
15. **Why can CSMA still have collisions?** Propagation delay: a node may not yet hear a transmission that has already started.
16. **How long until CSMA/CD detects a collision (worst case)?** $2t_{prop}$.
17. **What problem do RTS/CTS solve?** The hidden terminal problem (and they make collisions cheap).
18. **Why does WiFi use link-layer ACKs but wired Ethernet does not?** Wireless links have high error rates and a sender cannot detect collisions at the receiver (hidden terminals).
19. **Purpose of bit stuffing?** Prevent the flag pattern `01111110` from appearing inside the frame data.
20. **Which layer does each device work at?** Switch: link layer (2). Router: network layer (3). Host: all five.
