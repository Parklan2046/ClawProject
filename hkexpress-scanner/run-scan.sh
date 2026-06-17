#!/bin/bash
# HKExpress Price Scanner - Cron Wrapper
# Randomly delays by 0-15 minutes to avoid detection patterns

set -e

SLEEP=$((RANDOM % 900))
echo "[$(date)] Sleeping ${SLEEP}s before scan..."
sleep "$SLEEP"

cd /opt/hkexpress-scanner
exec /opt/hkexpress-scanner/venv/bin/python /opt/hkexpress-scanner/main.py scan
