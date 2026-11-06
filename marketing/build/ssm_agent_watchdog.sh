#!/usr/bin/env bash
# SSM agent watchdog -- self-healing for the recurring agent wedge.
#
# The amazon-ssm-agent (snap) on the GPU/music boxes wedges under heavy SSM
# load (not OOM -- memory is fine; the worker just stops making progress and
# AWS marks the box ConnectionLost). This watchdog detects that locally and
# restarts the snap service before it strands renders.
#
# Detection (checked ON the box, so it works even when AWS-side shows
# ConnectionLost):
#   1. agent process dead          -> restart
#   2. agent log stale > STALE and no active document workers -> restart
#
# Install: copy to /usr/local/sbin/ssm-agent-watchdog.sh (chmod +x), then
#   ( crontab -l | grep -v ssm-agent-watchdog ; \
#     echo "* * * * * /usr/local/sbin/ssm-agent-watchdog.sh >/dev/null 2>&1" ) | crontab -
# Restarts are logged to /var/log/ssm-watchdog.log.
set -uo pipefail

LOG=/var/log/amazon/ssm/amazon-ssm-agent.log
STALE=180

# 1) agent process dead -> restart
if ! pgrep -f 'amazon-ssm-agent' >/dev/null 2>&1; then
  echo "$(date -u +%FT%TZ) watchdog: agent process dead -> restart" >> /var/log/ssm-watchdog.log
  snap restart amazon-ssm-agent.amazon-ssm-agent 2>&1 | tail -2 >> /var/log/ssm-watchdog.log
  exit 0
fi

# 2) log stale + no active document workers -> wedged -> restart
if [ -f "$LOG" ]; then
  now=$(date +%s)
  mtime=$(stat -c %Y "$LOG" 2>/dev/null || echo "$now")
  age=$(( now - mtime ))
  if [ "$age" -gt "$STALE" ] && ! pgrep -f 'ssm-document-worker' >/dev/null 2>&1; then
    echo "$(date -u +%FT%TZ) watchdog: log stale ${age}s, no workers -> restart" >> /var/log/ssm-watchdog.log
    snap restart amazon-ssm-agent.amazon-ssm-agent 2>&1 | tail -2 >> /var/log/ssm-watchdog.log
  fi
fi
