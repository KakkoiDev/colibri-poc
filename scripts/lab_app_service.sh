#!/bin/sh
# Install or remove the GLM lab app as a macOS login service (LaunchAgent).
#   sh scripts/lab_app_service.sh install     # start at login, restart if it stops
#   sh scripts/lab_app_service.sh uninstall   # stop it and remove the LaunchAgent
# Only touches ~/Library/LaunchAgents/dev.kakkoi.glm-lab.plist. Logs: results/lab-app/server.log
set -eu
LABEL=dev.kakkoi.glm-lab
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"
case "${1:-}" in
install)
  mkdir -p "$ROOT/results/lab-app" "$HOME/Library/LaunchAgents"
  cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>$ROOT/.venv/bin/python</string><string>$ROOT/lab_app/server.py</string>
  </array>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$ROOT/results/lab-app/server.log</string>
  <key>StandardErrorPath</key><string>$ROOT/results/lab-app/server.log</string>
</dict></plist>
PL
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  launchctl bootstrap "$DOMAIN" "$PLIST"
  echo "Installed: http://127.0.0.1:8766 starts at login (log: results/lab-app/server.log)"
  ;;
uninstall)
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed the login service"
  ;;
*) echo "usage: $0 install|uninstall" >&2; exit 2 ;;
esac
