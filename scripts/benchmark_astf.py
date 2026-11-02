#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cisco TRex ASTF Automated Benchmark Runner for NGFW / Firewall Devices.
Author: bratiska6-pixel
License: Apache-2.0
"""

import sys
import os
import time
import json
import argparse
import subprocess

# Add TRex interactive client path if available
DEFAULT_TREX_PATHS = [
    '/opt/trex/current/automation/trex_control_plane/interactive',
    '/opt/trex/v3.08/automation/trex_control_plane/interactive',
    '/opt/trex/v3.07/automation/trex_control_plane/interactive',
]
for p in DEFAULT_TREX_PATHS:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.append(p)

try:
    from trex.astf.api import ASTFClient
except ImportError:
    print("[ERROR] Cisco TRex ASTF Python library not found.")
    print("Ensure TRex is installed in /opt/trex/ or set PYTHONPATH to interactive library.")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Automated TRex ASTF Benchmark for Firewalls")
    parser.add_argument("--server", default="127.0.0.1", help="TRex server IP address (default: 127.0.0.1)")
    parser.add_argument("--profile", default="astf/http_simple.py", help="ASTF profile path relative to TRex root")
    parser.add_argument("--mult", type=int, default=100, help="Traffic multiplier factor (default: 100)")
    parser.add_argument("--duration", type=int, default=15, help="Test duration in seconds (default: 15)")
    parser.add_argument("--trex-path", default="/opt/trex/v3.08", help="Base directory of TRex installation")
    parser.add_argument("--output", default="benchmark_result.json", help="Output JSON path")
    return parser.parse_args()


def run_benchmark(server, profile_rel, mult, duration, trex_path):
    prof_path = os.path.join(trex_path, profile_rel)
    if not os.path.exists(prof_path):
        # Fallback to local or relative path
        if os.path.exists(profile_rel):
            prof_path = profile_rel
        else:
            raise FileNotFoundError(f"ASTF Profile not found: {prof_path}")

    print(f"[*] Connecting to Cisco TRex ASTF on {server}:4500...")
    client = ASTFClient(server=server)
    client.connect()

    print("[*] Acquiring context and clearing stats...")
    client.acquire(force=True)
    client.clear_stats()

    print(f"[*] Loading and compiling profile: {prof_path}")
    client.load_profile(prof_path)

    print(f"[*] Resolving ARP with Target Firewall...")
    try:
        client.resolve(retries=3)
    except Exception as e:
        print(f"  [!] ARP Warning: {e}")

    print(f"[*] Starting ASTF traffic: Multiplier=x{mult}, Duration={duration}s...")
    client.start(mult=mult, duration=duration)

    samples = []
    start_time = time.time()
    
    # Collect telemetry samples every 1.5s
    while time.time() - start_time < duration + 4:
        time.sleep(1.5)
        try:
            st = client.get_stats()
            tx_bps = st.get(0, {}).get('tx_bps', 0)
            rx_bps = st.get(0, {}).get('rx_bps', 0)
            p1_rx = st.get(1, {}).get('rx_bps', 0)
            global_st = st.get('global', {})
            tx_cps = global_st.get('tx_cps', 0)
            active_flows = global_st.get('active_flows', 0)

            sample = {
                'elapsed': round(time.time() - start_time, 1),
                'cps': round(tx_cps, 1),
                'rx_mbps': round(rx_bps / 1e6, 2),
                'tx_mbps': round(tx_bps / 1e6, 2),
                'p1_rx_mbps': round(p1_rx / 1e6, 2),
                'active_flows': active_flows
            }
            samples.append(sample)
            print(f"  [{sample['elapsed']}s] CPS: {sample['cps']:<8} | RX: {sample['rx_mbps']:<8} Mbps | Active Flows: {sample['active_flows']}")

            if not client.is_traffic_active() and len(samples) > 2:
                break
        except Exception as e:
            print(f"  [!] Polling warning: {e}")

    # Gracefully stop
    try:
        if client.is_traffic_active():
            client.acquire(force=True)
            client.stop()
    except Exception:
        pass

    try:
        client.disconnect()
    except Exception:
        pass

    max_cps = max([s['cps'] for s in samples]) if samples else 0
    max_rx = max([s['rx_mbps'] for s in samples]) if samples else 0
    max_tx = max([s['tx_mbps'] for s in samples]) if samples else 0

    return {
        'profile': profile_rel,
        'mult': mult,
        'duration': duration,
        'max_cps': max_cps,
        'max_rx_mbps': max_rx,
        'max_tx_mbps': max_tx,
        'samples': samples
    }


def main():
    args = parse_args()
    print("=" * 60)
    print(" Cisco TRex ASTF Automated Firewall Benchmark")
    print("=" * 60)
    try:
        result = run_benchmark(
            server=args.server,
            profile_rel=args.profile,
            mult=args.mult,
            duration=args.duration,
            trex_path=args.trex_path
        )
        print("\n" + "=" * 60)
        print(f" RESULTS SUMMARY: {args.profile} (mult=x{args.mult})")
        print(f" Peak CPS:        {result['max_cps']} conn/sec")
        print(f" Peak Throughput: {result['max_rx_mbps']} Mbps")
        print("=" * 60)

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[+] Saved metrics to {args.output}")

    except Exception as e:
        print(f"\n[FATAL] Benchmark failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
