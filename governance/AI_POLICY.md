# AI Policy (ISO/IEC 42001 5.2)

## 1. Purpose
This policy defines the principles and requirements for the responsible use of the Enterprise Claude Code AI System. It is designed to ensure compliance with ISO/IEC 42001 and the EU AI Act.

## 2. Scope
This policy applies to all users, developers, and deployers of this AI System within the organization.

## 3. AI Principles
*   **Human-Centricity:** The AI System shall support human autonomy and decision-making.
*   **Transparency:** Users must be informed when they are interacting with an AI.
*   **Safety & Security:** The system must operate safely and securely, preventing harm to data and infrastructure.
*   **Fairness:** The system shall be monitored for bias and discrimination.

## 4. Risk Appetite
*   **Prohibited Uses:** The system shall not be used for:
    *   Social scoring.
    *   Real-time remote biometric identification in public spaces.
    *   Generation of CSAM or malicious software.
*   **High-Risk Uses:** Use cases involving HR decisions, critical infrastructure, or financial advice require explicit "Human-in-the-Loop" approval and enhanced logging.

## 5. Governance Controls
*   **Input Filtering:** All inputs must be screened for PII and proprietary data.
*   **Output Guardrails:** All outputs must be verified for safety before execution (via PreToolUse hooks).
*   **Audit Trails:** All interactions must be logged in the centralized audit log.

## 6. Roles and Responsibilities
*   **AI System Owner:** Responsible for overall compliance.
*   **Risk Reviewer:** Responsible for reviewing high-risk audit logs.
*   **User:** Responsible for adhering to this policy during use.

## 7. Policy Review
This policy shall be reviewed annually or upon significant system updates.
