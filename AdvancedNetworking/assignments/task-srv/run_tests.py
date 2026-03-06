#!/usr/bin/env python3
"""
Automated test runner for task-srv assignment.
Runs the server in the Mininet topology using aalto/simple_topo.py via subprocess.
"""

import time
import subprocess

from mininet.clean import cleanup
from mininet.log import setLogLevel

SIMPLE_TOPO = '/home/ubuntu/mininet-dev/mininet/aalto/simple_topo.py'
ADNET_AGENT = '/home/ubuntu/adnet-agent/target/debug/adnet-agent'
TASK_SRV    = '/home/ubuntu/ELEC-7321/AdvancedNetworking/assignments/task-srv/target/debug/task-srv'
KEYWORD     = 'helloworld'


def run_scenario(name, topo_args, desc):
    print(f'\n{"=" * 70}')
    print(f'  {name}')
    print(f'  {desc}')
    print(f'{"=" * 70}\n')

    cleanup()
    time.sleep(1)

    topo_cmd = ['python3', SIMPLE_TOPO] + topo_args

    srv_log = '/tmp/task-srv.log'
    commands = [
        f'rh1 {ADNET_AGENT} &',
        'sh sleep 2',
        # Run server in background — it never exits on its own
        f'lh1 {TASK_SRV} {KEYWORD} > {srv_log} 2>&1 &',
        'sh sleep 90',
        f'lh1 cat {srv_log}',
        'lh1 pkill task-srv',
        'rh1 pkill adnet-agent',
        'sh sleep 1',
        'exit',
    ]

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

        print('[*] === STDOUT ===')
        for line in proc.stdout.splitlines():
            print(f'    {line}')

        if proc.stderr:
            print('[*] === STDERR (filtered) ===')
            for line in proc.stderr.splitlines():
                if any(s in line for s in ['*** ', 'mininet>', 'containsKey']):
                    continue
                if line.strip():
                    print(f'    {line}')

        print(f'\n[*] Exit code: {proc.returncode}')

    except subprocess.TimeoutExpired:
        print(f'[!] TIMEOUT: {name} exceeded 5 minutes')
    except Exception as e:
        print(f'[!] ERROR: {e}')

    cleanup()
    time.sleep(2)


def main():
    setLogLevel('warning')

    print('=' * 70)
    print('  TASK-SRV Test Runner')
    print(f'  Keyword:     {KEYWORD}')
    print(f'  adnet-agent: {ADNET_AGENT}')
    print(f'  task-srv:    {TASK_SRV}')
    print('=' * 70)

    run_scenario(
        'Main scenario',
        ['--delay=50ms', '--bw=0.5'],
        'Bottleneck: delay=50ms, bw=500kbps',
    )

    print('\n' + '=' * 70)
    print('  ALL SCENARIOS COMPLETE')
    print('=' * 70)


if __name__ == '__main__':
    main()
