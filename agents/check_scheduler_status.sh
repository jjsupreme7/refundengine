#!/bin/bash
# Quick script to check the status of the agent scheduler

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Agent Scheduler Status ===${NC}\n"

# Check if running as launchd service
if launchctl list | grep -q "com.refundengine.scheduler"; then
    echo -e "${GREEN}✓ LaunchAgent installed and loaded${NC}"
    launchctl list | grep refundengine
else
    echo -e "${RED}✗ LaunchAgent not loaded${NC}"
fi

echo ""

# Check if process is running
if ps aux | grep -v grep | grep -q "agents/scheduler.py"; then
    echo -e "${GREEN}✓ Scheduler process running${NC}"
    ps aux | grep -v grep | grep "agents/scheduler.py" | awk '{print "  PID: " $2 ", Started: " $9}'
else
    echo -e "${RED}✗ Scheduler process not running${NC}"
fi

echo ""

# Check recent logs
if [ -f "agents/scheduler.log" ]; then
    echo "Recent log entries (last 10 lines):"
    echo "---"
    tail -10 agents/scheduler.log | sed 's/^/  /'
else
    echo "No log file found"
fi

echo ""

# Check for errors
if [ -f "agents/scheduler.error.log" ] && [ -s "agents/scheduler.error.log" ]; then
    echo -e "${RED}⚠ Errors detected:${NC}"
    echo "---"
    tail -10 agents/scheduler.error.log | sed 's/^/  /'
fi
