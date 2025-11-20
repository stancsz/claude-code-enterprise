#!/bin/bash
# Periodic Risk Assessment Tool for Claude Code Enterprise
# Checks compliance status, plugin installation, and audit logs.

set -e

echo "============================================================"
echo "Claude Code Enterprise - Quarterly Risk Assessment Tool"
echo "ISO/IEC 42001 & EU AI Act Compliance Check"
echo "============================================================"
echo "Date: $(date)"
echo "User: $(whoami)"
echo "------------------------------------------------------------"

FAILURES=0

# 1. Check Base Installation
if command -v claude &> /dev/null; then
    echo "[PASS] 'claude' command found."
else
    echo "[FAIL] 'claude' command NOT found. Please install @anthropic-ai/claude-code."
    FAILURES=$((FAILURES + 1))
fi

# 2. Check Governance Plugin Directory
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPO_ROOT=$(dirname "$SCRIPT_DIR")
PLUGIN_PATH="$REPO_ROOT/plugins/governance-layer"

if [ -d "$PLUGIN_PATH" ]; then
    echo "[PASS] Governance Plugin directory exists at: $PLUGIN_PATH"
else
    echo "[FAIL] Governance Plugin directory missing."
    FAILURES=$((FAILURES + 1))
fi

# 3. Check Audit Log
AUDIT_LOG=~/.claude/governance_audit.log
if [ -f "$AUDIT_LOG" ]; then
    echo "[PASS] Audit Log found at: $AUDIT_LOG"
    # Check last modification
    LAST_MOD=$(date -r "$AUDIT_LOG" "+%Y-%m-%d %H:%M:%S")
    echo "       Last activity: $LAST_MOD"
else
    echo "[WARN] Audit Log not found at: $AUDIT_LOG. It will be created on first run."
fi

# 4. Check Python Hook Dependencies
HOOK_PATH="$PLUGIN_PATH/hooks/governance_hook.py"
if [ -f "$HOOK_PATH" ]; then
    echo "[PASS] Governance Hook script found."
else
    echo "[FAIL] Governance Hook script missing at: $HOOK_PATH"
    FAILURES=$((FAILURES + 1))
fi

# 5. Configuration Check (Environment Variables)
echo "------------------------------------------------------------"
echo "Configuration Status:"
if [ -z "$GOVERNANCE_SIEM_URL" ]; then
    echo "[INFO] SIEM Integration: Disabled (Set GOVERNANCE_SIEM_URL to enable)"
else
    echo "[PASS] SIEM Integration: Enabled ($GOVERNANCE_SIEM_URL)"
fi

echo "------------------------------------------------------------"
if [ $FAILURES -eq 0 ]; then
    echo "ASSESSMENT RESULT: COMPLIANT"
    echo "The Governance Layer appears to be correctly installed and configured."
    exit 0
else
    echo "ASSESSMENT RESULT: NON-COMPLIANT ($FAILURES failures)"
    echo "Please review the errors above and take corrective action."
    exit 1
fi
