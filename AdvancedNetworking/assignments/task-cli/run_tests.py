#!/usr/bin/env python3
"""
Automated test runner for task-cli assignment.
Runs all 4 scenarios using the Mininet Python API AND the official aalto simple_topo.
"""

import sys
import os
import time
import subprocess

# Add the mininet aalto directory to the path so we can import the topology
sys.path.insert(0, "/home/ubuntu/mininet-dev/mininet/aalto")

from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.clean import cleanup

# Paths
ADNET_AGENT = "/home/ubuntu/adnet-agent/target/debug/adnet-agent"
TASK_CLI = "/home/ubuntu/ELEC-7321/AdvancedNetworking/assignments/task-cli/target/debug/task-cli"
KEYWORD = "helloworld"

# Import the official topology module
import simple_topo as st

SCENARIOS = [
    {
        "name": "Scenario 1: Long delay",
        "args": ["--delay=200ms"],
        "desc": "Bottleneck: delay=200ms, no bw limit, no loss",
    },
    {
        "name": "Scenario 2: Slow transmitter",
        "args": ["--delay=50ms", "--bw=0.1"],
        "desc": "Bottleneck: delay=50ms, bw=100kbps",
    },
    {
        "name": "Scenario 3: Lossy link",
        "args": ["--delay=200ms", "--loss=10"],
        "desc": "Bottleneck: delay=200ms, loss=10%",
    },
    {
        "name": "Scenario 4: Survival",
        "args": ["--delay=500ms", "--bw=0.05", "--loss=5", "--queue=10"],
        "desc": "Bottleneck: delay=500ms, bw=50kbps, loss=5%, queue=10",
    },
]


def run_scenario(scenario):
    """Run a single test scenario using the official simple_topo CLI."""
    name = scenario["name"]
    args = scenario["args"]
    desc = scenario["desc"]

    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"  {desc}")
    print(f"{'='*70}\n")

    # Clean up any previous Mininet state
    cleanup()
    time.sleep(1)

    # Build the command to start simple_topo.py non-interactively
    # We'll use subprocess to start the official topo, then inject commands
    topo_cmd = ["python3", "/home/ubuntu/mininet-dev/mininet/aalto/simple_topo.py"] + args

    print(f"[*] Starting topology: {' '.join(topo_cmd)}")

    # Start Mininet with the topology, piping commands to its stdin
    # We'll send commands to start adnet-agent, wait, then run task-cli
    commands = []
    commands.append(f"rh1 {ADNET_AGENT} &")      # Start server in background
    commands.append("sh sleep 2")                  # Wait for server to start
    commands.append(f"lh1 {TASK_CLI} {KEYWORD}")   # Run client
    commands.append("sh sleep 1")                  # Brief pause
    commands.append("exit")                        # Exit Mininet

    cmd_input = "\n".join(commands) + "\n"

    try:
        proc = subprocess.run(
            topo_cmd,
            input=cmd_input,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per scenario
        )

        print("[*] === STDOUT ===")
        # Filter for interesting lines
        for line in proc.stdout.split("\n"):
            print(f"    {line}")

        if proc.stderr:
            print("[*] === STDERR (filtered) ===")
            for line in proc.stderr.split("\n"):
                # Skip noisy Mininet debug lines
                if any(skip in line for skip in ["*** ", "mininet>", "containsKey"]):
                    continue
                if line.strip():
                    print(f"    {line}")

        print(f"\n[*] Exit code: {proc.returncode}")

    except subprocess.TimeoutExpired:
        print(f"[!] TIMEOUT: {name} exceeded 5 minutes")
    except Exception as e:
        print(f"[!] ERROR: {e}")

    # Cleanup
    cleanup()
    time.sleep(2)


def main():
    setLogLevel("warning")

    print("=" * 70)
    print("  TASK-CLI Assignment Test Runner")
    print(f"  Keyword: {KEYWORD}")
    print(f"  adnet-agent: {ADNET_AGENT}")
    print(f"  task-cli: {TASK_CLI}")
    print("=" * 70)

    results = []
    for scenario in SCENARIOS:
        run_scenario(scenario)

    print("\n" + "=" * 70)
    print("  ALL SCENARIOS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
