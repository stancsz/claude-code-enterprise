# Post-Market Monitoring (EU AI Act)

## Continuous Monitoring Plan

### 1. Metrics to Monitor
*   **Performance Drift:** Decrease in code acceptance rate (via `claude` feedback data).
*   **Safety Incidents:** Number of "Governance Block" events triggered by the hooks.
*   **User Complaints:** Number of `/bug` reports related to governance or safety.

### 2. Data Collection
*   **Mechanism:** The `governance_audit.log` file collects all relevant events.
*   **Aggregation:** Logs should be aggregated weekly by the Risk Reviewer.

### 3. Incident Reporting
*   **Serious Incidents:** Any incident resulting in breach of fundamental rights or critical infrastructure damage must be reported to the relevant national authority within 15 days.
*   **Malfunction:** Significant malfunctions must be reported to the AI System Owner immediately.

### 4. Feedback Loop
*   Insights from monitoring shall be used to update the Risk Assessment and AI Policy.
