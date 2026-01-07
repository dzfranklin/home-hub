#!/bin/bash
set -e

echo "Installing aranet4-monitor service..."
mkdir -p ~/.config/systemd/user
cp aranet4-monitor.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable aranet4-monitor.service
systemctl --user restart aranet4-monitor.service
echo "Service installed and started"
echo "Check status with: systemctl --user status aranet4-monitor"
echo "View logs with: journalctl --user -u aranet4-monitor -f"
