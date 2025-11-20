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

# Configuration
AUDIT_LOG_PATH = os.path.expanduser("~/.claude/governance_audit.log")

# Setup logging
os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=AUDIT_LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_audit(event_type, details, risk_level="LOW", decision="ALLOWED"):
    """
    Logs an audit event to the tamper-proof (simulated) log.
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
    return entry

def check_pii(text):
    """
    Simple regex-based PII detection.
    """
    if not isinstance(text, str):
        return False, text

    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ssn_pattern = r"\d{3}-\d{2}-\d{4}"

    redacted_text = text
    found_pii = False

    if re.search(email_pattern, text):
        redacted_text = re.sub(email_pattern, "[REDACTED_EMAIL]", redacted_text)
        found_pii = True

    if re.search(ssn_pattern, text):
        redacted_text = re.sub(ssn_pattern, "[REDACTED_SSN]", redacted_text)
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
        # Requirement: Block automated output until human supervisor approves.
        # Since we don't have a supervisor UI, we must BLOCK HIGH RISK prompts in this automated tool.
        print("Governance Alert: HIGH RISK Use Case detected (HR/Finance/etc).", file=sys.stderr)
        print("Compliance Policy: Automated processing of High Risk inputs requires Human-in-the-Loop approval.", file=sys.stderr)
        print("Operation Blocked by Governance Layer.", file=sys.stderr)
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
        "content_snippet": content[:200] # Log snippet
    })

    if has_pii:
        print("Governance Alert: Tool output contains PII! Data has been logged.", file=sys.stderr)
        # We can't block past action, but we log it.

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
