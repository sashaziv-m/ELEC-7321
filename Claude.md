# Claude.md — Repository Summary

## Overview

This is **Aleksandar Zivkovic's** working repository for the **Advanced Networking course (ELEC-E7321)** at **Aalto University**. It combines a personal GitHub repo with the official course materials.

## Repository Structure

```
ELEC-7321/
├── README.md                    # Personal course overview & links
├── Claude.md                    # This file
├── AdvancedNetworking/          # Course materials (cloned from PasiSa/AdvancedNetworking)
│   ├── _articles/               # Course lecture content (Jekyll markdown)
│   │   ├── intro.md             # Course introduction
│   │   ├── socket-basics.md     # Socket programming fundamentals
│   │   ├── server-sockets.md    # Server programming & concurrency
│   │   ├── congestion.md        # Congestion control algorithms
│   │   ├── web.md               # Web evolution & QUIC protocol
│   │   ├── linux-tcpip.md       # Linux networking internals
│   │   ├── udp.md               # UDP protocol
│   │   └── wireshark.md         # Wireshark usage guide
│   ├── assignments/             # Programming assignments (Rust templates)
│   │   ├── task-cli/            # ✅ Assignment 1: TCP client (IMPLEMENTED)
│   │   ├── task-udp/            # Assignment: UDP programming
│   │   ├── task-srv/            # Assignment: Server programming
│   │   ├── task-quic/           # Assignment: QUIC protocol
│   │   └── task-tun/            # Assignment: Tunneling
│   ├── examples/                # Code examples in C and Rust
│   ├── tools/                   # Build/test/export scripts
│   ├── _config.yml              # Jekyll site configuration
│   └── ...                      # Jekyll layouts, includes, assets, etc.
```

## Development Environment

- **Ubuntu VM** at `192.168.64.4` (user: `ubuntu`, pass: `ubuntu`)
  - Rust toolchain installed — used for compiling and running assignments
  - Same git repo cloned at `/home/ubuntu/ELEC-7321/`
  - Mininet environment for network emulation
- **Local Mac** for editing code
- **Git remote**: `github.com:sashaziv-m/ELEC-7321.git` (SSH on VM, HTTPS locally)

### Workflow

1. Edit code locally or on the VM
2. **SCP** files to the VM or push/pull via git
3. **Build** on the VM: `cargo build` in the assignment directory
4. **Run** inside Mininet topology (e.g., `simple_topo.py`)

## Course Topics

1. Network programming basics (sockets, TCP, UDP)
2. Server programming (concurrency, high-performance architecture)
3. Congestion control algorithms
4. Web evolution & QUIC transport protocol
5. Linux networking internals
6. Software-Defined Networking (SDN)
7. Datacenter networking
8. IoT & challenged networks

## Assignments

All assignments use **Rust** templates (Cargo projects) and run inside a **Mininet** emulated network with `adnet-agent` as the server at `10.0.0.3:12345`.

| Assignment | Description | Status |
|------------|-------------|--------|
| `task-cli` | TCP client — connect, send keyword, read response, report stats | ✅ Done |
| `task-udp` | UDP programming | ⬜ Not started |
| `task-srv` | Server programming | ⬜ Not started |
| `task-quic` | QUIC protocol | ⬜ Not started |
| `task-tun` | Tunneling | ⬜ Not started |

## Key Files

- **`install.sh`** (parent dir): Installs Mininet, OpenFlow, Open vSwitch, POX controller, Wireshark, and dependencies. Supports Ubuntu/Debian/Fedora/CentOS/macOS.
- **`AdvancedNetworking/assignments/task-cli/src/main.rs`**: Implemented TCP client that accepts a keyword via CLI, connects to `adnet-agent`, sends `TASK-CLI <keyword>`, reads all data, and reports total bytes, last 8 characters, and transfer duration.

## Mininet Topology

Assignments use `simple_topo.py` with configurable link properties:

```bash
sudo aalto/simple_topo.py --delay=200ms              # Long delay
sudo aalto/simple_topo.py --delay=50ms --bw=0.1       # Slow transmitter
sudo aalto/simple_topo.py --delay=200ms --loss=10      # Lossy link
```

- `lh1` (10.0.0.1) — client host
- `rh1` (10.0.0.3) — server host running `adnet-agent` on port 12345
