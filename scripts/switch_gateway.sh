#!/usr/bin/env bash
# ==============================================================================
#  Dynamic Gateway Switcher for Cisco TRex Benchmarking
#  Author: bratiska6-pixel
#  License: Apache-2.0
# ==============================================================================

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: sudo $0 <PORT0_GATEWAY_IP> <PORT1_GATEWAY_IP>"
    echo "Example: sudo $0 192.168.1.1 172.10.1.1"
    exit 1
fi

P0_GW="$1"
P1_GW="$2"
TREX_CFG="/etc/trex_cfg.yaml"

echo "[*] Updating TRex default gateways to Port 0: ${P0_GW}, Port 1: ${P1_GW}..."

cat <<EOF > "${TREX_CFG}"
- version: 2
  interfaces: ['03:00.0', '0b:00.0']
  port_info:
      - ip: 192.168.1.2
        default_gw: ${P0_GW}
      - ip: 172.10.1.2
        default_gw: ${P1_GW}

  platform:
      master_thread_id: 0
      latency_thread_id: 1
      dual_if:
        - socket: 0
          threads: [2, 3]
EOF

echo "[*] Restarting trex-engine.service..."
systemctl restart trex-engine.service
sleep 3

echo "[+] TRex service restarted successfully with new gateways."
