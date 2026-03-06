# Task-SRV Assignment Report

## Advanced Networking Course (ELEC-E7321)

---

## Setup

- **Topology**: `sudo aalto/simple_topo.py --delay=50ms --bw=0.5`
  - 500 kbps bottleneck, 50 ms one-way delay (100 ms RTT)
- **Server**: `task-srv` on lh1 (`10.0.0.1:12321`)
- **Client**: `adnet-agent` on rh1 (`10.0.0.3:12345`)
- **Keyword**: `helloworld`

---

## Implementation

Thread-per-client model. The server:

1. Binds a TCP listener on `0.0.0.0:12321`
2. Connects to `adnet-agent` and sends `TASK-SRV helloworld 10.0.0.1:12321`
3. Accepts incoming connections in a loop, spawning a thread for each
4. Each thread reads 5-byte requests (4-byte u32 big-endian byte count + 1-byte fill character), writes the requested bytes, and loops until the client closes the connection

---

## Output

Three concurrent connections were accepted. Each connection received
multiple 5-byte requests. All transfers completed successfully.

```
Wrote 212345 bytes of byte 83
Wrote 205376 bytes of byte 84
Wrote 193091 bytes of byte 75
Wrote 218978 bytes of byte 81
Wrote 219458 bytes of byte 71
Wrote 200104 bytes of byte 65
Wrote 207708 bytes of byte 79
Wrote 208823 bytes of byte 84
Wrote 221872 bytes of byte 66
```

---

## Test Environment

- **VM**: Ubuntu 22.04 (aarch64) at 192.168.65.2
- **Mininet**: `/home/ubuntu/mininet-dev/mininet/`
- **Topology**: dumbbell (lh1/lh2 — r1 — r2 — rh1/rh2), bw=0.5 Mbps, delay=50 ms
