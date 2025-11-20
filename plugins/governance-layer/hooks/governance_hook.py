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
import urllib.request
import urllib.error
from datetime import datetime

# Configuration
AUDIT_LOG_PATH = os.path.expanduser("~/.claude/governance_audit.log")
SIEM_URL = os.environ.get("GOVERNANCE_SIEM_URL")

# Setup logging
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=AUDIT_LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_to_siem(log_entry):
    """
    Sends the log entry to a configured SIEM via HTTP POST.
    """
    if not SIEM_URL:
        return

    try:
        data = json.dumps(log_entry).encode('utf-8')
        req = urllib.request.Request(SIEM_URL, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=2) as response:
            pass # Success
    except Exception as e:
        # Log failure to local log but don't crash
        logging.error(f"SIEM Logging Failed: {str(e)}")

def log_audit(event_type, details, risk_level="LOW", decision="ALLOWED"):
    """
    Logs an audit event to the tamper-proof (simulated) log and optional SIEM.
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
    Simple regex-based PII detection.
    Includes Email, SSN, Credit Card, Employee ID, Internal Projects.
    """
    if not isinstance(text, str):
        return False, text

    patterns = [
        (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[REDACTED_EMAIL]"),
        (r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_SSN]"),
        (r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED_CREDIT_CARD]"),
        (r"\bEMP-\d{5}\b", "[REDACTED_EMPLOYEE_ID]"),
        (r"\bPROJ-[A-Z]{3,}\b", "[REDACTED_PROJECT_CODE]")
    ]

    redacted_text = text
    found_pii = False

    for pattern, replacement in patterns:
        if re.search(pattern, redacted_text):
            redacted_text = re.sub(pattern, replacement, redacted_text)
            found_pii = True

    return found_pii, redacted_text

def classify_risk(text):
    """
    Classify risk based on keywords.
    """
    if not isinstance(text, str):
        return "LOW"

    high_risk_keywords = ["confidential", "secret", "hr decision", "medical diagnosis", "financial advice"]
    for keyword in high_risk_keywords:
        if keyword.lower() in text.lower():
            return "HIGH"
    return "LOW"

def request_user_approval(risk_level):
    """
    Attempts to prompt the user via /dev/tty for HITL approval.
    Returns True if approved, False otherwise.
    """
    try:
        # Only works if attached to a terminal
        if not os.path.exists("/dev/tty"):
            return False

        with open("/dev/tty", "r+") as tty:
            tty.write(f"\n\033[1;33m[Governance] WARN: Output classified as {risk_level} Risk.\033[0m\n")
            tty.write("[Governance] Do you confirm you have reviewed it? [y/N]: ")
            response = tty.readline().strip().lower()
            return response == 'y'
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

    # Requirement: Log original and redacted input
    log_audit("INPUT_CHECK", {
        "session_id": session_id,
        "original_prompt": prompt,
        "redacted_prompt": redacted_prompt,
        "has_pii": has_pii
    }, risk_level=risk)

    if has_pii:
        # We cannot modify the prompt in UserPromptSubmit via stdout easily based on known docs.
        # Rejection is the safest compliant path if we can't guarantee modification.
        # However, we will print the redacted version to stderr for user awareness
        # and BLOCK the request to prevent leakage.
        print(f"Governance Alert: PII detected. \nOriginal: {prompt}\nRedacted would be: {redacted_prompt}", file=sys.stderr)
        print("Blocking request due to PII Policy.", file=sys.stderr)
        sys.exit(1)

    if risk == "HIGH":
        # HITL Workflow
        approved = request_user_approval(risk)

        if approved:
            log_audit("HITL_APPROVAL", {"session_id": session_id, "risk": risk, "approved": True})
            # Allow to proceed
            sys.exit(0)
        else:
            # Block
            print("Governance Alert: HIGH RISK Use Case detected (HR/Finance/etc).", file=sys.stderr)
            print("Compliance Policy: Automated processing of High Risk inputs requires Human-in-the-Loop approval.", file=sys.stderr)
            print("Operation Blocked by Governance Layer (Approval Denied or Unavailable).", file=sys.stderr)
            log_audit("HITL_APPROVAL", {"session_id": session_id, "risk": risk, "approved": False}, decision="BLOCKED")
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
    risk = classify_risk(content)

    log_audit("TOOL_OUTPUT_CHECK", {
        "session_id": session_id,
        "tool_name": tool_name,
        "has_pii": has_pii,
        "content_snippet": content[:200] # Log snippet
    })

    if has_pii:
        print("Governance Alert: Tool output contains PII! Data has been logged.", file=sys.stderr)
        # We can't block past action, but we log it.

    if risk == "HIGH":
        # For tool output, we might want HITL before showing it?
        # PostToolUse usually happens after tool execution but before Agent sees it?
        # Or before User sees it?
        # Docs on hooks are sparse, assuming passive monitoring for PostToolUse unless we can block the return value.
        pass

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
