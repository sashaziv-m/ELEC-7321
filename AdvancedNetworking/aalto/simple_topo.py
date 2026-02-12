#!/usr/bin/env python3

"""
simple_topo.py — Mininet topology for the Advanced Networking course (ELEC-E7321)

Creates a simple dumbbell topology with:
  - 2 hosts on the left side:  lh1 (10.0.0.1), lh2 (10.0.0.2)
  - 2 hosts on the right side: rh1 (10.0.0.3), rh2 (10.0.0.4)
  - 2 routers (r1, r2) connected by a bottleneck link

The bottleneck link between r1 and r2 has configurable delay, bandwidth,
packet loss, and queue size via command-line arguments.

Usage:
  sudo aalto/simple_topo.py --delay=200ms
  sudo aalto/simple_topo.py --delay=50ms --bw=0.1
  sudo aalto/simple_topo.py --delay=200ms --loss=10
  sudo aalto/simple_topo.py --delay=200ms --loss=10 --queue=20
"""

import argparse
import sys

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import dumpNodeConnections


class LinuxRouter(Node):
    """A Linux node configured as an IP router (IP forwarding enabled)."""

    def config(self, **params):
        super().config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


class SimpleTopo(Topo):
    """
    Dumbbell topology:

        lh1 ──┐                ┌── rh1
              r1 ──bottleneck── r2
        lh2 ──┘                └── rh2

    Left subnet:  10.0.0.0/24   (lh1 = .1, lh2 = .2)
    Right subnet: 10.0.0.0/24   (rh1 = .3, rh2 = .4)
    Router link:  10.0.1.0/24   (r1 = .1, r2 = .2)
    """

    def build(self, delay="10ms", bw=None, loss=0, queue=None):
        # --- Routers ---
        r1 = self.addNode("r1", cls=LinuxRouter, ip="10.0.1.1/24")
        r2 = self.addNode("r2", cls=LinuxRouter, ip="10.0.1.2/24")

        # --- Left hosts ---
        lh1 = self.addHost(
            "lh1", ip="10.0.0.1/24", defaultRoute="via 10.0.0.254"
        )
        lh2 = self.addHost(
            "lh2", ip="10.0.0.2/24", defaultRoute="via 10.0.0.254"
        )

        # --- Right hosts ---
        rh1 = self.addHost(
            "rh1", ip="10.0.0.3/24", defaultRoute="via 10.0.0.253"
        )
        rh2 = self.addHost(
            "rh2", ip="10.0.0.4/24", defaultRoute="via 10.0.0.253"
        )

        # --- Host-to-router links (no impairment) ---
        self.addLink(lh1, r1, intfName2="r1-eth1",
                     params2={"ip": "10.0.0.254/24"})
        self.addLink(lh2, r1, intfName2="r1-eth2",
                     params2={"ip": "10.0.0.254/24"})
        self.addLink(rh1, r2, intfName2="r2-eth1",
                     params2={"ip": "10.0.0.253/24"})
        self.addLink(rh2, r2, intfName2="r2-eth2",
                     params2={"ip": "10.0.0.253/24"})

        # --- Bottleneck link (configurable impairment) ---
        link_opts = {
            "delay": delay,
            "loss": loss,
            "use_htb": True,
        }
        if bw is not None:
            link_opts["bw"] = bw
        if queue is not None:
            link_opts["max_queue_size"] = queue

        self.addLink(
            r1, r2,
            intfName1="r1-eth0", intfName2="r2-eth0",
            params1={"ip": "10.0.1.1/24"},
            params2={"ip": "10.0.1.2/24"},
            cls=TCLink,
            **link_opts,
        )


def run(args):
    """Build, start the network, enter CLI, then clean up."""
    setLogLevel("info")

    topo = SimpleTopo(
        delay=args.delay,
        bw=args.bw,
        loss=args.loss,
        queue=args.queue,
    )
    net = Mininet(topo=topo, link=TCLink)
    net.start()

    # Add static routes so left hosts can reach right hosts and vice-versa
    r1 = net["r1"]
    r2 = net["r2"]
    r1.cmd("ip route add 10.0.0.3/32 via 10.0.1.2")
    r1.cmd("ip route add 10.0.0.4/32 via 10.0.1.2")
    r2.cmd("ip route add 10.0.0.1/32 via 10.0.1.1")
    r2.cmd("ip route add 10.0.0.2/32 via 10.0.1.1")

    info("\n*** Topology\n")
    info("    lh1 (10.0.0.1) ──┐                   ┌── rh1 (10.0.0.3)\n")
    info("                     r1 ── bottleneck ── r2\n")
    info("    lh2 (10.0.0.2) ──┘                   └── rh2 (10.0.0.4)\n")
    info("\n")
    info(f"*** Bottleneck: delay={args.delay}")
    if args.bw is not None:
        info(f", bw={args.bw} Mbps")
    if args.loss > 0:
        info(f", loss={args.loss}%")
    if args.queue is not None:
        info(f", queue={args.queue}")
    info("\n\n")

    dumpNodeConnections(net.hosts)

    info("\n*** Testing connectivity\n")
    net.pingAll()

    info("\n*** Entering Mininet CLI (type 'exit' or Ctrl-D to quit)\n\n")
    CLI(net)
    net.stop()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simple dumbbell topology for Advanced Networking course"
    )
    parser.add_argument(
        "--delay",
        type=str,
        default="10ms",
        help="One-way propagation delay on the bottleneck link (e.g. 200ms)",
    )
    parser.add_argument(
        "--bw",
        type=float,
        default=None,
        help="Bandwidth limit on the bottleneck link in Mbps (e.g. 0.1 for 100kbps)",
    )
    parser.add_argument(
        "--loss",
        type=float,
        default=0,
        help="Packet loss rate on the bottleneck link in %% (e.g. 10 for 10%%)",
    )
    parser.add_argument(
        "--queue",
        type=int,
        default=None,
        help="Max queue size (packets) on the bottleneck link",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args)
