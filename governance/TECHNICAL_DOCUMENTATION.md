# Technical Documentation (EU AI Act)

## 1. System Description
*   **Name:** Claude Code Enterprise Edition
*   **Version:** [Version]
*   **Purpose:** Agentic coding tool with governance layer.
*   **Modality:** Text/Code Generation.

## 2. Architecture
*   **Core Model:** Anthropic Claude (accessed via API).
*   **Governance Layer:** Plugin-based interceptors (Hooks).
    *   **Input Filter:** Regex-based PII redaction.
    *   **Risk Classifier:** Keyword-based intent classification.
    *   **Audit Log:** Local file-based immutable log.

## 3. Data Governance
*   **Training Data:** The Governance Layer itself is not trained. The underlying model (Claude) training data is managed by Anthropic.
*   **Input Data:** User prompts are processed locally for redaction before transmission.
*   **Retention:** Audit logs are retained for [X] years.

## 4. Testing and Validation
*   **Accuracy:** Validated via unit tests of the governance hooks.
*   **Robustness:** Tested against adversarial prompts (jailbreak attempts).
*   **Cybersecurity:** Static analysis of plugin code; dependency scanning.

## 5. Human Oversight
*   **Measures:**
    *   "Human-in-the-loop" for tool execution (users must approve actions).
    *   High-risk warnings displayed to users.
    *   Post-hoc audit reviews.

## 6. Change Management
*   All changes to the Governance Layer must go through the Change Control Board.
