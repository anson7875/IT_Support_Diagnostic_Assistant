# Diagnostic Knowledge Base Design

**Document Version:** 1.1  
**Project:** IT Support Diagnostic & Case Management System  
**Document Type:** Technical Design  
**Status:** Approved for Schema Validation

---

## 1. Purpose

This document defines the structure, data standards, diagnostic workflow model, and validation requirements for the project's Diagnostic Knowledge Base.

The Knowledge Base will provide structured diagnostic information for three initial technical categories:

- PC Hardware
- Windows Operating System
- Networking

The system will use deterministic Python logic to interpret diagnostic results and determine the next appropriate action.

The Knowledge Base must support consistent diagnostic workflows without requiring workflow-specific Python code.

## 2. Design Principles

The Knowledge Base must follow these principles:

1. **Structured Data:** Diagnostic information must follow a consistent and predefined structure.
2. **Modularity:** Hardware, Windows, and Networking workflows must be maintained separately.
3. **Reusability:** Different diagnostic workflows should reuse common data structures.
4. **Traceability:** Every diagnostic conclusion must be supported by recorded observations or evidence.
5. **Explainability:** Every diagnostic step must explain its purpose, procedure, and expected results.
6. **Safety First:** Safety conditions must override normal diagnostic progression.
7. **Extensibility:** New diagnostic categories and workflows should be added without redesigning the entire system.
8. **Validation:** Invalid or incomplete workflows must be detected before execution.

## 3. Knowledge Base Structure

The Knowledge Base will use JSON files to store diagnostic workflows.

Proposed directory structure:

```text
knowledge_base/
├── hardware_rules.json
├── windows_rules.json
└── network_rules.json
```

Each JSON file will contain multiple diagnostic workflows belonging to its respective category.

All three files must follow the same underlying data structure.

## 4. Diagnostic Workflow Model

A diagnostic workflow represents a structured sequence of diagnostic steps used to investigate a specific IT incident.

Each workflow must contain the following information:

| Field | Description |
|---|---|
| workflow_id | Unique workflow identifier |
| workflow_name | Name of the diagnostic workflow |
| category | Technical category |
| description | Description of the issue being investigated |
| version | Workflow version |
| initial_step_id | Identifier of the first diagnostic step |
| steps | Collection of diagnostic steps |
| references | Related technical references |

### 4.1 Workflow Categories

The initial supported categories are:

- `hardware`
- `windows`
- `network`

### 4.2 Workflow Identification

Every workflow must have a unique `workflow_id`.

Example:

- `HW-001`: PC does not power on.
- `WIN-001`: Windows startup failure.
- `NET-001`: No internet connectivity.

Workflow identifiers must remain unique across the entire Knowledge Base.

## 5. Diagnostic Step Model

Each workflow consists of multiple diagnostic steps.

Every diagnostic step must contain the following information:

| Field | Description |
|---|---|
| step_id | Unique step identifier within the workflow |
| title | Diagnostic step title |
| objective | Purpose of the diagnostic step |
| instructions | Step-by-step procedure |
| test_type | Type of diagnostic test |
| expected_results | Expected observations or results |
| safety_requirements | Safety precautions |
| result_transitions | Rules determining the next action |
| reference_ids | Related technical references |
| max_visits | Maximum permitted executions of this step |

### 5.1 Test Types

The system should support different types of diagnostic tests, including:

- `visual_inspection`
- `physical_check`
- `command_execution`
- `system_information`
- `performance_check`
- `hardware_test`
- `user_confirmation`

Different test types may produce different observations.

For example:

- A network test may produce packet loss and response time.
- A disk test may produce drive health information.
- A Windows diagnostic command may produce command output and an exit code.
- A visual inspection may produce a user-reported observation.

The system must preserve these observations without forcing every test into the same data format.

## 6. Diagnostic Result Model

Diagnostic results represent the outcome of an individual diagnostic step.

The following standard result codes must be supported:

| Result Code | Description |
|---|---|
| `normal` | The test result is within the expected condition |
| `abnormal` | The test result indicates an unexpected condition |
| `inconclusive` | Available information is insufficient to determine the outcome |
| `not_performed` | The test was not carried out |
| `unable_to_perform` | The test could not be completed |

### 6.1 Result and Workflow Status Separation

The system must distinguish between:

**Test Result**

Describes the outcome of an individual diagnostic test.

Examples:

- `normal`
- `abnormal`
- `inconclusive`

**Workflow Status**

Describes the overall state of the diagnostic session.

Supported workflow statuses:

- `active`
- `paused`
- `completed`
- `escalated`
- `safety_stop`

A test result must not directly represent the overall workflow status.

For example, an abnormal test result does not automatically mean that the diagnostic workflow is completed or that the root cause has been confirmed.

### 6.2 Diagnostic Observations

Each diagnostic test should support structured observations.

Observations may include:

- Text descriptions
- Numeric measurements
- Command outputs
- Error messages
- Device information
- User responses
- File or image references

The system should preserve the original observation data where possible.

A normalized result code may be used for workflow branching, while detailed observations provide the technical evidence needed for further analysis.

## 7. Result Transition Model

The diagnostic engine must determine the next action based on the recorded test result and the workflow's transition rules.

Supported transition actions:

| Action | Description |
|---|---|
| `next_step` | Continue to another diagnostic step |
| `request_more_information` | Request additional information from the user |
| `pause` | Temporarily stop the diagnostic workflow |
| `complete` | Complete the diagnostic workflow |
| `escalate` | Refer the incident to a qualified technician |

### 7.1 Transition Rules

Each diagnostic step must define the appropriate transition for its supported result codes.

Example:

| Result | Action |
|---|---|
| `normal` | `next_step` |
| `abnormal` | `next_step` |
| `inconclusive` | `request_more_information` |
| `not_performed` | `pause` |
| `unable_to_perform` | `escalate` |

The actual transition depends on the specific diagnostic workflow.

### 7.2 Missing Transition Handling

If a diagnostic result does not have a valid transition rule:

1. The engine must not guess the next diagnostic step.
2. The workflow must be paused safely.
3. The system must record the missing transition condition.
4. The issue must be available for investigation by the developer or administrator.

Invalid transitions must never cause uncontrolled workflow progression.

## 8. Evidence Management

Evidence is information collected during the diagnostic process.

Evidence must be recorded separately from diagnostic conclusions.

### 8.1 Evidence Types

Supported evidence types may include:

- `user_report`
- `visual_observation`
- `command_output`
- `system_information`
- `measurement`
- `error_message`
- `log_record`
- `test_result`

### 8.2 Evidence Record

Each evidence record should contain:

| Field | Description |
|---|---|
| evidence_id | Unique evidence identifier |
| incident_id | Related incident |
| workflow_id | Related workflow |
| step_id | Diagnostic step that produced the evidence |
| evidence_type | Type of evidence |
| description | Evidence description |
| raw_value | Original observation or result |
| recorded_at | Date and time of recording |
| source | Origin of the evidence |

### 8.3 Multiple Evidence Records

A single diagnostic step may produce multiple evidence records.

For example, a network connectivity test may record:

- IP address
- Default gateway
- Ping response
- Packet loss
- DNS resolution result

The diagnostic session must be able to associate multiple evidence records with the same diagnostic step.

Evidence must not be overwritten when a diagnostic step is repeated.

## 9. Diagnostic Findings and Root Cause

The system must distinguish between possible causes and verified findings.

Supported finding statuses:

| Status | Description |
|---|---|
| `possible` | A potential cause identified from the reported symptoms |
| `suspected` | A potential cause supported by preliminary observations |
| `evidence_supported` | A cause supported by relevant diagnostic evidence |
| `confirmed` | A cause explicitly verified through sufficient evidence |

### 9.1 Root Cause Confirmation Rules

An abnormal diagnostic result alone must not automatically establish a confirmed root cause.

A finding should only be marked as `confirmed` when:

1. Relevant diagnostic evidence has been collected.
2. The evidence supports the proposed cause.
3. Contradictory observations have been considered.
4. The confirmation basis is documented.
5. The confirmation is recorded by an authorized diagnostic process or technician.

The system must preserve the distinction between:

- User-reported symptoms
- Diagnostic observations
- Test results
- Possible causes
- Evidence-supported findings
- Confirmed root causes

## 10. Safety Control Model

Safety controls have priority over normal diagnostic workflow transitions.

Supported safety control states:

- `active`
- `paused`
- `completed`
- `escalated`
- `safety_stop`

### 10.1 Safety Stop Conditions

The diagnostic engine must immediately stop normal diagnostic progression when a serious safety condition is identified.

Examples include:

- Swollen battery
- Smoke
- Burning smell
- Visible electrical damage
- Unsafe power conditions

The system must provide an appropriate safety warning and escalation instruction.

### 10.2 Safety Override

Safety rules must override ordinary result transitions.

For example:

If a user reports a burning smell during a hardware diagnostic workflow, the system must not continue to the next hardware test simply because the previous test returned `normal`.

The workflow must enter `safety_stop`.

A safety stop is a workflow control state, not a normal diagnostic result code.

## 11. Workflow Validation Rules

Before a workflow can be loaded or executed, it must pass structural validation.

The validation process must check:

1. Required workflow fields are present.
2. Workflow identifiers are unique.
3. Step identifiers are unique within each workflow.
4. The initial step exists.
5. Every transition target references an existing step.
6. Every supported result has an explicitly defined transition.
7. All required step fields are valid.
8. Reference identifiers are valid where references are provided.
9. Safety requirements are defined appropriately.
10. Workflow steps are reachable where required.
11. Invalid or unreachable transition targets are rejected.
12. Cyclic workflows are controlled.

### 11.1 Cycle and Repeated Execution Control

Some diagnostic workflows may legitimately repeat a test.

However, uncontrolled cycles may cause infinite execution.

The system must therefore:

- Detect cycles during workflow validation.
- Define a maximum visit count for repeatable steps.
- Track how many times each step has been executed.
- Prevent execution beyond the configured limit.
- Pause safely when the maximum visit count is reached.

A workflow must not enter an unlimited diagnostic loop.

## 12. Diagnostic Engine Interaction

The Diagnostic Engine is responsible for interpreting the Knowledge Base and managing diagnostic progression.

The expected process is:

1. Receive the incident information.
2. Identify the appropriate diagnostic category.
3. Select a suitable diagnostic workflow.
4. Load and validate the workflow.
5. Present the initial diagnostic step.
6. Collect user responses and test observations.
7. Generate and associate evidence records.
8. Normalize the test result.
9. Check safety conditions.
10. Evaluate the applicable transition rule.
11. Select the next action.
12. Record the diagnostic history.
13. Continue until completion, pause, escalation, or safety stop.

The engine must use deterministic Python logic.

It must not execute arbitrary Python expressions stored in JSON files.

In particular, `eval()` must not be used to interpret Knowledge Base rules.

## 13. Technical References

Each diagnostic workflow should provide relevant technical references where available.

References may include:

- Hardware manufacturer documentation
- Microsoft official documentation
- Network equipment manufacturer documentation
- Operating system technical documentation
- Recognized technical standards

Reference records should contain:

| Field | Description |
|---|---|
| reference_id | Unique reference identifier |
| title | Reference title |
| publisher | Organization or publisher |
| url | Reference URL |
| description | Explanation of the reference |

References should support the technical explanation and verification of diagnostic procedures.

## 14. Initial Workflow Coverage

The initial Knowledge Base should include representative workflows from all three technical categories.

### 14.1 PC Hardware

Initial workflow examples:

- PC does not power on
- PC powers on but no display
- PC fails POST
- RAM detection issue
- Storage device not detected
- Overheating symptoms

### 14.2 Windows

Initial workflow examples:

- Windows startup failure
- Blue Screen of Death (BSOD)
- Unexpected shutdown
- High CPU or memory usage
- Windows Update failure
- Driver-related problems

### 14.3 Networking

Initial workflow examples:

- No internet connectivity
- Wi-Fi connection failure
- Ethernet connection failure
- Incorrect IP configuration
- DNS resolution failure
- Packet loss or high latency

## 15. Schema Validation and Acceptance Criteria

Before implementing the Diagnostic Engine, the Knowledge Base schema must be validated against representative workflows.

The schema validation phase is considered complete when:

1. All three technical categories use a consistent workflow structure.
2. Different diagnostic test types can store their observations.
3. Multiple evidence records can be associated with one diagnostic step.
4. All supported result codes have defined transition behavior.
5. Missing transitions are handled safely.
6. Safety conditions override normal workflow progression.
7. Abnormal results are not automatically treated as confirmed root causes.
8. Invalid workflow references are rejected.
9. Uncontrolled workflow cycles are prevented.
10. The structure can support future diagnostic categories without major redesign.

## 16. Implementation Constraints

The following constraints apply to the MVP:

- Python will implement the diagnostic engine.
- JSON will store the diagnostic Knowledge Base.
- SQLite will store incident records, diagnostic sessions, findings, and evidence metadata.
- Pytest will be used for automated testing.
- Flask will provide the web application interface.
- No external AI API is required for the core diagnostic process.
- Diagnostic decisions must be explainable and reproducible.
- Safety controls must take priority over diagnostic completion.

## 17. Next Development Phase

The next development phase is:

**Phase 2.1 — Finalize and Validate the JSON Knowledge Base Schema**

Planned activities:

1. Review the Version 1.1 Knowledge Base design.
2. Identify any remaining schema gaps.
3. Define the actual JSON structure.
4. Create representative workflow examples.
5. Validate workflows from Hardware, Windows, and Networking.
6. Confirm that the schema supports all required diagnostic behaviors.
7. Prepare the schema for Python implementation.

The project must not proceed to full Diagnostic Engine implementation until the Knowledge Base schema has been sufficiently validated.

---

**End of Document**