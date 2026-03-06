# Task-QUIC Assignment Report

## Advanced Networking Course (ELEC-E7321)

---

## Setup

- **Implementation**: Cloudflare quiche v0.24.5
- **Topology**: `aalto/simple_topo.py --bw=1 --delay=200ms --loss=5`
  - 1 Mbps bottleneck, 200 ms one-way delay (400 ms RTT), 5% random packet loss
- **Files served**: `file-A.txt`, `file-B.txt`, `file-C.txt` — each 102 400 bytes (100 KiB)
- **Server**: `quiche-server` on rh1 (`10.0.0.3:4433` UDP)
- **Client**: `quiche-client` on lh1 (`10.0.0.1`)

---

## Script Notes

### `setup_quic.sh`

**`cargo build` (not `--examples`)**

In quiche v0.24.5 the repository is a Cargo workspace. `quiche-server` and
`quiche-client` are defined as `[[bin]]` targets inside the `apps/` workspace
member, not as `[[example]]` targets. `cargo build --examples` only builds
`[[example]]` entries and produces no server or client binary. Plain
`cargo build` builds all workspace members including `apps/`, placing both
binaries in `target/debug/`.

**`head -c 102400` instead of `head -c 100K`**

GNU `head` on Linux accepts `100K` as shorthand for 102 400, but the behaviour
is not portable across shell versions. Using the explicit byte count removes
the ambiguity.

### `run_experiment.py`

**Subprocess + stdin pattern (no topology reimplementation)**

Follows the same approach as `run_tests.py`: the official `aalto/simple_topo.py`
is launched via `subprocess.run` and CLI commands are piped to its stdin.
This avoids reimplementing the topology and keeps both scripts consistent.

**QLOGDIR inlined per command**

Each line sent to the Mininet CLI runs in its own subshell. An
`export QLOGDIR=...` in one line is not visible in the next. The variable is
therefore inlined directly in each command:

```
rh1 QLOGDIR=/path quiche-server ...
lh1 QLOGDIR=/path quiche-client ...
```

**Two experiments with labelled artefacts**

The assignment requires a default run and a priority run. Each experiment
writes its own `capture-{label}.pcap`, `server-{label}.log`, and
`client-{label}.log` so the two runs do not overwrite each other. Qlog files
are renamed with `archive_qlogs(label)` after each run.

**Client stdout suppressed**

`quiche-client` writes downloaded file contents to stdout. Redirecting stdout
to `/dev/null` keeps the log readable; only diagnostic stderr is captured.

---

## Question 1 — What does Wireshark reveal as unencrypted in QUIC?

QUIC encrypts nearly all payload, but certain fields remain visible:

| Field | Visible? |
|-------|----------|
| QUIC version | Yes — long-header packets |
| Destination Connection ID (DCID) | Yes — all packets |
| Source Connection ID (SCID) | Yes — long-header packets only |
| Packet type (Initial, Handshake, 1-RTT …) | Yes — header flags |
| Retry token | Yes — Initial long header |
| Packet number | No — header protection applied |
| Payload frames | No — AEAD encrypted |

**Exception — Initial packets**: QUIC derives encryption keys for Initial
packets from the client's DCID using a publicly specified KDF (RFC 9001 §5.2).
Wireshark implements this derivation and therefore fully decrypts Initial
packets, revealing the TLS `ClientHello`/`ServerHello` and `CRYPTO` frames.
Handshake and 1-RTT packets use session-specific keys Wireshark cannot derive
without a key log file (SSLKEYLOGFILE), so those payload frames remain opaque.

In practice a capture shows:
- Packet type and connection IDs for every datagram
- Full TLS handshake content inside Initial-packet CRYPTO frames
- Encrypted blobs for all Handshake and 1-RTT application data

---

## Question 2 — TCP retransmission ambiguity

When TCP retransmits a segment it reuses the **same sequence number**. If an
ACK arrives for that sequence number, the sender cannot tell whether the ACK
was triggered by the **original** transmission or the **retransmission**.

This corrupts RTT estimation: if the ACK came from a delayed original, the
sample under-estimates the true RTT; if it came from the retransmission, it
over-estimates. Either way the retransmission timeout (RTO) is miscalibrated.

**Karn's algorithm** (Karn & Partridge, 1987) resolves this by discarding
RTT samples taken from any retransmitted segment. The cost is that RTT
information is unavailable during loss episodes — exactly when accurate
estimates are most needed.

---

## Question 3 — Does QUIC suffer from retransmission ambiguity?

**No.** QUIC eliminates retransmission ambiguity by design.

QUIC packet numbers are **strictly monotonically increasing** (RFC 9000 §12.3):
every new packet — including one carrying retransmitted data — receives a
**fresh, unique packet number**. ACKs reference packet numbers directly, so the
sender always knows precisely which transmission is being acknowledged.

The separation between *packet numbers* (transport identifiers) and *stream
offsets* (data positions) is key:
- The **stream offset** identifies where bytes belong in the data stream and is
  the same in the original and retransmission.
- The **packet number** identifies which packet the receiver acknowledges, and
  is always new.

QUIC can therefore update smoothed RTT even from retransmitted packets.

---

## Question 4 — Recognising retransmitted data in qlog / qvis

RFC 9000 §13.3: when the sender declares a packet lost (ACK gap or PTO
expiry), it retransmits the **frames** in a **new packet** with a new packet
number.

In qlog / qvis:
- **Sequence diagram**: retransmission appears as a new arrow (new packet
  number) whose `STREAM` frame `offset` overlaps a previously sent frame.
- **qlog events**: `transport:packet_sent` entries where the contained
  `STREAM` frame has the same `stream_id` and `offset` as an earlier event.
- **qvis Multiplexing tab**: repeated byte-range coverage on a stream
  indicates a loss and retransmission.

The `recovery:packet_lost` event in qlog directly precedes the corresponding
retransmission `transport:packet_sent` event, making the cause-and-effect
chain explicit.

---

## Question 5 — How does quiche-server handle concurrency?

`quiche-server` uses a **single-threaded event-driven** architecture over UDP.

- A **single UDP socket** is bound to `0.0.0.0:4433`. All clients send
  datagrams to the same socket.
- **`mio::Poll`** provides non-blocking event notification. When the socket
  becomes readable the server calls `recv_from` in a loop to drain all pending
  datagrams before yielding back to `poll`.
- Incoming datagrams are demultiplexed by **Destination Connection ID (DCID)**
  into a `HashMap<ConnectionId, Connection>`. Each `Connection` maintains full
  cryptographic and flow-control state for one QUIC connection.
- All connections are serviced in the **same thread**, avoiding synchronisation
  overhead.

This contrasts with `task-srv`'s per-client thread model: instead of one
thread per connection, one thread services all connections via event iteration.

---

## Question 6 — Stream IDs used for the three files

RFC 9000 §2.1: stream IDs are 62-bit integers; the two least-significant bits
encode type:

| Bit 0 (initiator) | Bit 1 (direction) | Type | IDs |
|---|---|---|---|
| 0 (client) | 0 (bidi) | Client-init bidi | 0, 4, 8, 12 … |
| 1 (server) | 0 (bidi) | Server-init bidi | 1, 5, 9, 13 … |
| 0 (client) | 1 (uni)  | Client-init uni  | 2, 6, 10, 14 … |
| 1 (server) | 1 (uni)  | Server-init uni  | 3, 7, 11, 15 … |

HTTP/3 request streams are client-initiated bidirectional (bits `00`) because
the client opens each request and the server replies on the same stream:

| File | Stream ID |
|------|-----------|
| file-A.txt | **0** |
| file-B.txt | **4** |
| file-C.txt | **8** |
| (hypothetical fourth file) | **12** |

IDs increment by 4 because each step preserves the two type bits.

*(HTTP/3 also opens unidirectional control streams automatically: client
control on 2, QPACK encoder on 6, QPACK decoder on 10; server mirrors on 3,
7, 11.)*

---

## Question 7 — Congestion control and recovery metrics in qlog

The `recovery:metrics_updated` event is emitted whenever any of the following
change:

| Metric | Description |
|--------|-------------|
| `bytes_in_flight` | Unacknowledged bytes currently in the network |
| `congestion_window` (cwnd) | Sender's current congestion window in bytes |
| `smoothed_rtt` | EWMA of measured RTT |
| `latest_rtt` | Most recent RTT sample |
| `min_rtt` | Minimum observed RTT (baseline) |
| `rtt_variance` | Variance of RTT samples |
| `ssthresh` | Slow-start threshold |

Additional recovery events:

| Event | Meaning |
|-------|---------|
| `recovery:packet_lost` | Loss declared for a specific packet |
| `recovery:loss_timer_set` / `_cancelled` | PTO / loss-detection timer changes |
| `transport:packet_sent` / `_received` | Sent/received packet with per-frame breakdown |

In qvis the "Congestion" chart plots `cwnd`, `bytes_in_flight`, and `ssthresh`
on a common timeline, showing slow-start growth, each loss-triggered window
reduction, and recovery phases.

---

## Stream Priority Experiment

### Part A — Default (no priorities)

**Client command:**
```bash
QLOGDIR=. target/debug/quiche-client --no-verify \
  "https://10.0.0.3:4433/file-A.txt" \
  "https://10.0.0.3:4433/file-B.txt" \
  "https://10.0.0.3:4433/file-C.txt"
```

Times are relative to the first data frame received by the client (t=0 = first STREAM frame on stream 4).

| Stream | File | Start (ms) | End (ms) | Duration (ms) |
|--------|------|-----------|---------|--------------|
| 0 | file-A.txt | 6480 | 9318 | 2838 |
| 4 | file-B.txt | 0 | 4442 | 4442 |
| 8 | file-C.txt | 4467 | 11542 | 7075 |

### Part B — With stream priorities (file-C.txt elevated)

RFC 9218 `Priority` parameters:
- `u` — urgency (0 = highest, 7 = lowest; default 3)
- `i` — incremental flag: server interleaves bytes from this stream with
  others of the same urgency, so all transfers start immediately

**Client command:**
```bash
QLOGDIR=. target/debug/quiche-client --no-verify --send-priority-update \
  "https://10.0.0.3:4433/file-A.txt?u=3&i" \
  "https://10.0.0.3:4433/file-B.txt?u=3&i" \
  "https://10.0.0.3:4433/file-C.txt?u=0&i"
```

Times are relative to the first data frame received by the client (t=0 = first STREAM frame on stream 4).

| Stream | File | Priority | Start (ms) | End (ms) | Duration (ms) |
|--------|------|----------|-----------|---------|--------------|
| 0 | file-A.txt | u=3, i | 2121 | 2818 | 697 |
| 4 | file-B.txt | u=3, i | 0 | 2961 | 2961 |
| 8 | file-C.txt | u=0, i | 1215 | 2015 | 800 |

---

## Test Environment

- **VM**: Ubuntu 22.04 (aarch64) at 192.168.65.2
- **Mininet**: `/home/ubuntu/mininet-dev/mininet/`
- **quiche**: v0.24.5 at `assignments/task-quic/quiche/`
- **Topology**: dumbbell (lh1/lh2 — r1 — r2 — rh1/rh2), bw=1 Mbps,
  delay=200 ms, loss=5%
- **Capture**: tshark on `rh1-eth0` → `capture-*.pcap`
- **qlogs**: `*.sqlog` in `assignments/task-quic/quiche/`
