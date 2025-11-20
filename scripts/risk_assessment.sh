#!/bin/bash
# Enterprise AI Risk Assessment Tool
# Verifies that the Governance Layer is active and properly configured.

echo "Starting Enterprise Risk Assessment..."
echo "Timestamp: $(date)"
echo "------------------------------------------------"

# 1. Check Plugin Installation
REPO_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )
PLUGIN_PATH="$REPO_ROOT/plugins/governance-layer"

# We verify the Python script is present
if [ -f "$PLUGIN_PATH/hooks/governance_hook.py" ]; then
    echo "[PASS] Governance Plugin files detected."
else
    echo "[FAIL] Governance Plugin files missing."
    exit 1
fi

# 2. Check Configuration
CONFIG_PATH="$HOME/.claude/governance_config.json"
if [ -f "$CONFIG_PATH" ]; then
    echo "[PASS] User Configuration found at $CONFIG_PATH"
else
    echo "[WARN] No user configuration found. Using defaults (Internal Mode)."
fi

# 3. Check Audit Log
LOG_PATH="$HOME/.claude/governance_audit.log"
if [ -f "$LOG_PATH" ]; then
    echo "[PASS] Audit Log exists."
    # Check recency
    if [ "$(find "$LOG_PATH" -mtime -1)" ]; then
        echo "[PASS] Audit Log has recent activity."
    else
        echo "[WARN] Audit Log is stale (no activity in last 24h)."
    fi
else
    echo "[FAIL] No Audit Log found. Governance may not be active."
fi

# 4. Verification of Wrapper Usage
if [ -z "$CLAUDE_ENTERPRISE_GOVERNANCE_ACTIVE" ]; then
    echo "[WARN] This script is not running under the wrapper environment."
    echo "       Ensure you run './bin/claude-enterprise' to enforce compliance."
else
    echo "[PASS] Wrapper environment detected."
fi

echo "------------------------------------------------"
echo "Risk Assessment Complete."
