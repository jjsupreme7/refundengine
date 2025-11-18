#!/bin/bash
# Setup script to configure the agent scheduler to run automatically on macOS

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PLIST_FILE="com.refundengine.scheduler.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
DEST_PLIST="$LAUNCH_AGENTS_DIR/$PLIST_FILE"

echo -e "${BLUE}=== Refund Engine Agent Scheduler - Auto-Start Setup ===${NC}\n"

# Create LaunchAgents directory if it doesn't exist
if [ ! -d "$LAUNCH_AGENTS_DIR" ]; then
    echo "Creating LaunchAgents directory..."
    mkdir -p "$LAUNCH_AGENTS_DIR"
fi

# Copy plist file
echo "Installing launch agent..."
cp "$PLIST_FILE" "$DEST_PLIST"

# Set correct permissions
chmod 644 "$DEST_PLIST"

# Unload if already loaded
if launchctl list | grep -q "com.refundengine.scheduler"; then
    echo "Stopping existing scheduler service..."
    launchctl bootout gui/$(id -u)/com.refundengine.scheduler 2>/dev/null || true
fi

# Load the launch agent
echo "Starting scheduler service..."
launchctl bootstrap gui/$(id -u) "$DEST_PLIST"
launchctl kickstart -k gui/$(id -u)/com.refundengine.scheduler

echo -e "\n${GREEN}✓ Agent scheduler configured successfully!${NC}\n"
echo "The scheduler will now:"
echo "  • Start automatically when you log in"
echo "  • Restart automatically if it crashes"
echo "  • Run agents from 1am-8am Pacific time"
echo ""
echo "To check status:"
echo "  launchctl list | grep refundengine"
echo ""
echo "To view logs:"
echo "  tail -f agents/scheduler.log"
echo "  tail -f agents/scheduler.error.log"
echo ""
echo "To stop the service:"
echo "  launchctl bootout gui/\$(id -u)/com.refundengine.scheduler"
echo ""
echo "To start the service again:"
echo "  launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/$PLIST_FILE"
echo "  launchctl kickstart -k gui/\$(id -u)/com.refundengine.scheduler"
