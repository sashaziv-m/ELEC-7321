#!/usr/bin/env python3
"""
Experiment runner for task-quic assignment.

Follows the same pattern as run_tests.py: pipes Mininet CLI commands to
aalto/simple_topo.py via subprocess stdin — no topology reimplementation.

Two experiments:
  default  — three files with no priority hints
  priority — file-C.txt at urgency 0 (highest); A and B at urgency 3;
             all streams marked incremental so all start immediately.

Artefacts (qlogs, pcaps, logs) are written to QUICHE_DIR.
"""

import os
import glob
import time
import subprocess

from mininet.clean import cleanup
from mininet.log import setLogLevel

SIMPLE_TOPO = '/home/ubuntu/mininet-dev/mininet/aalto/simple_topo.py'
QUICHE_DIR  = '/home/ubuntu/ELEC-7321/AdvancedNetworking/assignments/task-quic/quiche'
SERVER_BIN  = os.path.join(QUICHE_DIR, 'target/debug/quiche-server')
CLIENT_BIN  = os.path.join(QUICHE_DIR, 'target/debug/quiche-client')
CERT        = os.path.join(QUICHE_DIR, 'apps/src/bin/cert.crt')
KEY         = os.path.join(QUICHE_DIR, 'apps/src/bin/cert.key')

SERVER_ADDR = '10.0.0.3'
SERVER_PORT = 4433

EXPERIMENTS = [
    {
        'label': 'default',
        'topo_args': ['--bw=1', '--delay=200ms', '--loss=5'],
        'urls': [
            f'https://{SERVER_ADDR}:{SERVER_PORT}/file-A.txt',
            f'https://{SERVER_ADDR}:{SERVER_PORT}/file-B.txt',
            f'https://{SERVER_ADDR}:{SERVER_PORT}/file-C.txt',
        ],
        'priority': False,
    },
    {
        'label': 'priority',
        'topo_args': ['--bw=1', '--delay=200ms', '--loss=5'],
        'urls': [
            f'https://{SERVER_ADDR}:{SERVER_PORT}/file-A.txt?u=3&i',
            f'https://{SERVER_ADDR}:{SERVER_PORT}/file-B.txt?u=3&i',
            f'https://{SERVER_ADDR}:{SERVER_PORT}/file-C.txt?u=0&i',
        ],
        'priority': True,
    },
]


def archive_qlogs(label):
    """Rename *.sqlog files from the last run to include the experiment label."""
    for f in glob.glob(os.path.join(QUICHE_DIR, '*.sqlog')):
        basename = os.path.basename(f)
        if label in basename:
            continue
        new_name = os.path.join(QUICHE_DIR, f'{label}-{basename}')
        os.rename(f, new_name)
        print(f'[*] Saved qlog: {os.path.basename(new_name)}')


def run_experiment(exp):
    label     = exp['label']
    topo_args = exp['topo_args']
    urls      = exp['urls']
    priority  = exp['priority']

    print(f'\n{"=" * 70}')
    print(f'  Experiment: {label}')
    print(f'  Topology:   {" ".join(topo_args)}')
    print(f'{"=" * 70}\n')

    cleanup()
    time.sleep(1)

    pcap       = os.path.join(QUICHE_DIR, f'capture-{label}.pcap')
    server_log = os.path.join(QUICHE_DIR, f'server-{label}.log')
    client_log = os.path.join(QUICHE_DIR, f'client-{label}.log')

    priority_flag = '--send-priority-update' if priority else ''
    urls_str      = ' '.join(f'"{u}"' for u in urls)

    # Each line is one Mininet CLI command.
    # QLOGDIR is inlined per-command — environment variables do not persist
    # across separate CLI invocations (each runs in its own subshell).
    commands = [
        f'rh1 tshark -i rh1-eth0 -w {pcap} &',
        'sh sleep 1',
        (f'rh1 QLOGDIR={QUICHE_DIR} {SERVER_BIN}'
         f' --cert {CERT} --key {KEY}'
         f' --listen 0.0.0.0:{SERVER_PORT} --root {QUICHE_DIR}'
         f' > {server_log} 2>&1 &'),
        'sh sleep 2',
        # Redirect stdout to /dev/null (file contents) and stderr to log
        (f'lh1 QLOGDIR={QUICHE_DIR} {CLIENT_BIN}'
         f' --no-verify {priority_flag} {urls_str}'
         f' > /dev/null 2> {client_log}'),
        'rh1 pkill tshark',
        'rh1 pkill quiche-server',
        'sh sleep 1',
        'exit',
    ]

    topo_cmd  = ['python3', SIMPLE_TOPO] + topo_args
    cmd_input = '\n'.join(commands) + '\n'

    print(f'[*] Starting topology: {" ".join(topo_cmd)}')

    try:
        proc = subprocess.run(
            topo_cmd,
            input=cmd_input,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if os.path.exists(client_log):
            print('\n[*] === client log ===')
            with open(client_log) as f:
                print(f.read())

        if proc.stderr:
            print('[*] === stderr (filtered) ===')
            for line in proc.stderr.splitlines():
                if any(s in line for s in ['*** ', 'mininet>', 'containsKey']):
                    continue
                if line.strip():
                    print(f'    {line}')

        archive_qlogs(label)
        print(f'\n[*] Exit code: {proc.returncode}')

    except subprocess.TimeoutExpired:
        print(f'[!] TIMEOUT: experiment "{label}" exceeded 5 minutes')
    except Exception as e:
        print(f'[!] ERROR: {e}')

    cleanup()
    time.sleep(2)


def main():
    setLogLevel('warning')

    print('=' * 70)
    print('  TASK-QUIC Experiment Runner')
    print(f'  quiche dir : {QUICHE_DIR}')
    print(f'  topology   : {SIMPLE_TOPO}')
    print('=' * 70)

    for exp in EXPERIMENTS:
        run_experiment(exp)

    print('\n' + '=' * 70)
    print('  ALL EXPERIMENTS COMPLETE')
    print(f'  Artefacts saved to: {QUICHE_DIR}')
    print('  Upload *.sqlog files to https://qvis.quictools.info/ for analysis')
    print('=' * 70)


if __name__ == '__main__':
    main()
