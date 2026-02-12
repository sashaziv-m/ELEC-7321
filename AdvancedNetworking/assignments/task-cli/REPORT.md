# Task-CLI Assignment Report

## Advanced Networking Course (ELEC-E7321)

---

## Common Results (All Scenarios)

| Item | Value |
|------|-------|
| **Keyword** | `helloworld` |
| **Total bytes received** | 92,345 |
| **Last 8 characters** | `WlyK8jdp` |

These values were identical across all four scenarios, confirming correct and complete TCP delivery.

---

## Scenario Results

### Scenario 1: Long Delay

**Parameters:** `sudo aalto/simple_topo.py --delay=200ms`

| Metric | Value |
|--------|-------|
| **Bottleneck link** | delay=200ms, no bw limit, no loss |
| **Transfer duration** | 1.245 seconds |
| **Round-trips** | *Requires Wireshark analysis* |
| **Retransmissions** | *Requires Wireshark analysis* |

**Analysis:** With 200ms one-way delay (400ms RTT) and no bandwidth constraint, TCP's congestion window grows quickly during slow start. The transfer completes in ~1.2s, suggesting the congestion window reaches a sufficiently large size within a few RTTs to transfer all 92KB of data.

---

### Scenario 2: Slow Transmitter

**Parameters:** `sudo aalto/simple_topo.py --delay=50ms --bw=0.1`

| Metric | Value |
|--------|-------|
| **Bottleneck link** | delay=50ms, bw=100kbps, no loss |
| **Transfer duration** | 7.658 seconds |
| **Round-trips** | *Requires Wireshark analysis* |
| **Retransmissions** | *Requires Wireshark analysis* |

**Analysis:** The 100kbps bottleneck is the dominant factor. At 100kbps, transferring 92,345 bytes = 738,760 bits takes a minimum of ~7.4 seconds for raw data alone. The measured 7.658s is close to this theoretical minimum, indicating that the bandwidth limit — not the 50ms delay — is the bottleneck. TCP likely experiences some retransmission timeouts as the congestion window exceeds the bandwidth-delay product (BDP = 100kbps × 100ms RTT ≈ 1,250 bytes).

---

### Scenario 3: Lossy Link

**Parameters:** `sudo aalto/simple_topo.py --delay=200ms --loss=10`

| Metric | Value |
|--------|-------|
| **Bottleneck link** | delay=200ms, no bw limit, loss=10% |
| **Transfer duration** | 3.647 seconds |
| **Round-trips** | *Requires Wireshark analysis* |
| **Retransmissions** | *Requires Wireshark analysis* |

**Analysis:** The 10% loss rate significantly impacts TCP performance compared to Scenario 1 (from 1.2s to 3.6s — roughly 3× slower). Loss triggers TCP's congestion control: each lost packet causes either fast retransmit (3 duplicate ACKs) or retransmission timeout (RTO). With 400ms RTT, each RTO penalty is substantial. TCP's congestion window shrinks after each loss event, reducing throughput. Despite the losses, TCP reliably delivers all 92,345 bytes.

---

### Scenario 4: Survival

**Parameters:** `sudo aalto/simple_topo.py --delay=500ms --bw=0.05 --loss=5 --queue=10`

| Metric | Value |
|--------|-------|
| **Bottleneck link** | delay=500ms, bw=50kbps, loss=5%, queue=10 packets |
| **Transfer duration** | 16.032 seconds |
| **Round-trips** | *Requires Wireshark analysis* |
| **Retransmissions** | *Requires Wireshark analysis* |

**Survival parameters rationale:**
- **500ms delay**: Very high latency makes RTT 1 second, causing long RTO timers
- **50kbps bandwidth**: Half the speed of Scenario 2, severely limiting throughput
- **5% packet loss**: Adds retransmissions on top of bandwidth constraints
- **Queue size 10 packets**: Small buffer increases tail-drop probability under congestion

**Analysis:** This is an extremely challenging scenario combining all impairments. The BDP is only ~6,250 bytes (50kbps × 1s RTT). With 5% loss and a 10-packet queue, TCP frequently experiences both loss-induced congestion window reductions and queue overflow drops. The 16s transfer time (vs. ~14.8s theoretical minimum at 50kbps) shows TCP manages to keep the link reasonably utilized despite the adversarial conditions.

---

## Summary Table

| Scenario | Delay | Bandwidth | Loss | Queue | Duration |
|----------|-------|-----------|------|-------|----------|
| 1. Long delay | 200ms | unlimited | 0% | 20 | **1.245s** |
| 2. Slow transmitter | 50ms | 100kbps | 0% | 20 | **7.658s** |
| 3. Lossy link | 200ms | unlimited | 10% | 20 | **3.647s** |
| 4. Survival | 500ms | 50kbps | 5% | 10 | **16.032s** |

> **Note:** Round-trip counts and retransmission counts require Wireshark packet capture analysis on the rh1-eth0 interface during each scenario. The above durations were measured programmatically by the `task-cli` client.

---

## Test Environment

- **VM**: Ubuntu 22.04 (aarch64) at 192.168.64.4
- **Mininet**: Official course installation at `/home/ubuntu/mininet-dev/mininet/`
- **Topology**: `aalto/simple_topo.py` (dumbbell: lh1/lh2 — r1 — r2 — rh1/rh2)
- **Server**: `adnet-agent` on rh1 (10.0.0.3:12345)
- **Client**: `task-cli` on lh1 (10.0.0.1)
