#!/usr/bin/env python3
"""
Governance Hook for Claude Code Enterprise.
Handles UserPromptSubmit (PII/Risk), PreToolUse (Guardrails), PostToolUse (Output Scan), and SessionStart (Audit Init).
"""

import json
import sys
import os
import re
import argparse
import logging
from datetime import datetime
import urllib.request
import urllib.error

# Configuration
AUDIT_LOG_PATH = os.path.expanduser("~/.claude/governance_audit.log")
CONFIG_PATH = os.path.expanduser("~/.claude/governance_config.json")

# Load Config
CONFIG = {
    "audit_endpoint": "",
    "audit_token": "",
    "pii_patterns": {},
    "high_risk_keywords": ["confidential", "secret", "hr decision", "medical diagnosis", "financial advice"],
    "hitl_mode": "block" # 'block' or 'interactive'
}

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r') as f:
            user_config = json.load(f)
            CONFIG.update(user_config)
    except Exception as e:
        pass # Fallback to default

# Setup logging
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=AUDIT_LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_to_siem(entry):
    """
    Sends log entry to SIEM endpoint if configured.
    """
    url = CONFIG.get("audit_endpoint")
    if not url:
        return

    token = CONFIG.get("audit_token")
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"

    try:
        req = urllib.request.Request(url, data=json.dumps(entry).encode('utf-8'), headers=headers, method='POST')
        urllib.request.urlopen(req, timeout=2) # Short timeout to avoid blocking flow
    except Exception:
        pass # Fail silently for SIEM logging, rely on local log

def log_audit(event_type, details, risk_level="LOW", decision="ALLOWED"):
    """
    Logs an audit event to the tamper-proof (simulated) log and SIEM.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "risk_level": risk_level,
        "decision": decision,
        "details": details,
        "model_version": os.environ.get("CLAUDE_MODEL_VERSION", "unknown"),
    }
    logging.info(json.dumps(entry))
    send_to_siem(entry)
    return entry

def check_pii(text):
    """
    Regex-based PII detection with dynamic patterns.
    """
    if not isinstance(text, str):
        return False, text

    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "ssn": r"\d{3}-\d{2}-\d{4}"
    }
    # Add user patterns
    patterns.update(CONFIG.get("pii_patterns", {}))

    redacted_text = text
    found_pii = False

    for name, pattern in patterns.items():
        try:
            if re.search(pattern, redacted_text):
                redacted_text = re.sub(pattern, f"[REDACTED_{name.upper()}]", redacted_text)
                found_pii = True
        except re.error:
            continue # Skip invalid regex

    return found_pii, redacted_text

def classify_risk(text):
    """
    Classify risk based on keywords.
    """
    if not isinstance(text, str):
        return "LOW"

    keywords = CONFIG.get("high_risk_keywords", [])
    for keyword in keywords:
        if keyword.lower() in text.lower():
            return "HIGH"
    return "LOW"

def prompt_hitl_approval():
    """
    Attempts to interactively ask for approval.
    """
    try:
        # Open tty directly to bypass stdin redirection from hook
        with open("/dev/tty", "r+") as tty:
            print("\n\033[93m[GOVERNANCE] High Risk Prompt Detected.\033[0m", file=tty)
            print("Do you confirm you have reviewed it and authorize this action? [y/N]: ", end="", file=tty)
            response = tty.readline().strip().lower()
            if response == 'y':
                return True
            return False
    except Exception:
        return False

def handle_session_start(data):
    """
    Initialize session audit.
    """
    log_audit("SESSION_START", {"session_id": data.get("session_id")})
    print("Governance Layer Active: Session Audited.", file=sys.stderr)
    sys.exit(0)

def handle_user_prompt(data):
    """
    Intercepts UserPromptSubmit.
    Redacts PII and checks risk.
    """
    prompt = data.get("prompt", "")
    session_id = data.get("session_id")

    has_pii, redacted_prompt = check_pii(prompt)
    risk = classify_risk(prompt)

    log_audit("INPUT_CHECK", {
        "session_id": session_id,
        "original_prompt": prompt,
        "redacted_prompt": redacted_prompt,
        "has_pii": has_pii
    }, risk_level=risk)

    if has_pii:
        print(f"Governance Alert: PII detected. \nOriginal: {prompt}\nRedacted would be: {redacted_prompt}", file=sys.stderr)
        print("Blocking request due to PII Policy.", file=sys.stderr)
        sys.exit(1)

    if risk == "HIGH":
        mode = CONFIG.get("hitl_mode", "block")
        if mode == "interactive":
             if prompt_hitl_approval():
                 log_audit("HITL_APPROVAL", {"session_id": session_id}, risk_level="HIGH", decision="APPROVED")
                 sys.exit(0) # Allow
             else:
                 log_audit("HITL_DENIAL", {"session_id": session_id}, risk_level="HIGH", decision="DENIED")
                 print("Operation Denied by User.", file=sys.stderr)
                 sys.exit(1)
        else:
            # Block mode
            print("Governance Alert: HIGH RISK Use Case detected.", file=sys.stderr)
            print("Compliance Policy: High Risk inputs are blocked in this mode.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)

def handle_pre_tool_use(data):
    """
    Intercepts PreToolUse.
    """
    tool_name = data.get("tool_name")
    tool_input = data.get("tool_input")
    session_id = data.get("session_id")

    log_audit("TOOL_USE", {
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input
    })

    if tool_name == "Bash" and "rm -rf /" in str(tool_input):
        print("Governance Block: Dangerous command blocked.", file=sys.stderr)
        sys.exit(2) # Block

    sys.exit(0)

def handle_post_tool_use(data):
    """
    Intercepts PostToolUse.
    """
    tool_name = data.get("tool_name")
    tool_result = data.get("tool_result")
    session_id = data.get("session_id")

    content = ""
    if isinstance(tool_result, dict):
        content = str(tool_result.get("content", ""))
    else:
        content = str(tool_result)

    has_pii, redacted = check_pii(content)

    log_audit("TOOL_OUTPUT_CHECK", {
        "session_id": session_id,
        "tool_name": tool_name,
        "has_pii": has_pii,
        "content_snippet": content[:200]
    })

    if has_pii:
        print("Governance Alert: Tool output contains PII! Data has been logged.", file=sys.stderr)

    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", required=True, help="Hook event type")
    args = parser.parse_args()

    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            sys.exit(0)
        data = json.loads(raw_input)
    except Exception:
        sys.exit(0)

    if args.event == "SessionStart":
        handle_session_start(data)
    elif args.event == "UserPromptSubmit":
        handle_user_prompt(data)
    elif args.event == "PreToolUse":
        handle_pre_tool_use(data)
    elif args.event == "PostToolUse":
        handle_post_tool_use(data)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
