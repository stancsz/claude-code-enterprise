# AI Risk Assessment Tool (ISO 42001 8.2)

## Instructions
Perform this assessment before deploying the AI System for a new use case.

## Part 1: Use Case Definition
*   **Intended Purpose:** [Describe what the AI will do]
*   **Target Users:** [Who will use it?]
*   **Deployment Environment:** [Dev/Test/Prod]

## Part 2: Impact Assessment (EU AI Act)
*   Does the system interact with safety components of products? [Yes/No]
*   Is the system used for biometric identification? [Yes/No]
*   Is the system used in Critical Infrastructure? [Yes/No]
*   Is the system used in Education/Vocational Training? [Yes/No]
*   Is the system used in Employment/Workers Management? [Yes/No]
*   Is the system used in Essential Private/Public Services? [Yes/No]
*   Is the system used in Law Enforcement? [Yes/No]
*   Is the system used in Migration/Asylum/Border Control? [Yes/No]
*   Is the system used in Justice/Democratic Processes? [Yes/No]

**Result:** If ANY of the above are YES, the system is **HIGH RISK**.

## Part 3: Risk Matrix
Identify potential risks and rate them (Low/Medium/High).

| Risk ID | Description | Probability | Severity | Mitigation Strategy | Residual Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| R1 | Data Leakage (PII) | Medium | High | Automated Input Filter (Redaction) | Low |
| R2 | Hallucination (Code) | High | Medium | Human Review of Code, Tests | Low |
| R3 | Bias in Output | Low | Medium | Prompt Engineering, Bias Testing | Low |
| R4 | Malicious Use | Low | High | Audit Logs, User Access Control | Low |

## Part 4: Approval
*   **Assessor:** ___________________
*   **Date:** ___________________
*   **Approver:** ___________________
