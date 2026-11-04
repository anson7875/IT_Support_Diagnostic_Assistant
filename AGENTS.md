# IT Support Diagnostic & Case Management System

## 1. Project Identity

Project Name:
IT Support Diagnostic & Case Management System

Product Direction:
Hybrid — Professional IT Diagnostic Platform
+ IT Support Learning Platform

Project Type:
A rule-based IT troubleshooting, diagnostic,
case management and technical learning system.

Primary Goal:
Build a professional portfolio project that demonstrates
practical IT Support knowledge, Python programming,
system design, troubleshooting methodology,
and software development skills.

---

## 2. Product Vision

This project must NOT be a simple FAQ website,
static troubleshooting guide, keyword search engine,
or AI chatbot.

It should function as a structured IT diagnostic platform
that guides users through evidence-based troubleshooting.

The system should:

1. Accept natural-language incident descriptions.
2. Extract relevant technical information.
3. Identify the likely problem category.
4. Select an appropriate diagnostic workflow.
5. Present one diagnostic step at a time.
6. Collect test results and observations.
7. Determine the next step using conditional rules.
8. Explain the purpose and technical principles
   behind each diagnostic step.
9. Record diagnostic evidence and test results.
10. Maintain incident history and diagnostic records.
11. Generate professional incident reports.
12. Help users develop practical IT troubleshooting skills.

The system must prioritize diagnostic accuracy,
evidence traceability, safety and usability.

---

## 3. Core Product Differentiation

The system must provide more than a list of possible solutions.

It should distinguish between:

- User-reported symptoms
- System observations
- Diagnostic tests
- Test results
- Possible causes
- Verified findings
- Confirmed root causes
- Applied solutions
- Resolution status

A possible cause must never automatically be presented
as a confirmed root cause.

Diagnostic conclusions must be supported by recorded evidence.

The system should explain:

- Why a test is necessary
- What the test checks
- How to perform the test
- What normal results look like
- What abnormal results may indicate
- What the next diagnostic step should be
- What limitations the test has

---

## 4. Technical Scope

Initial scope: Broad.

### 4.1 PC Hardware

Include:

- Power-related problems
- Boot and POST problems
- No display
- RAM-related problems
- Storage detection and health
- CPU and GPU symptoms
- Cooling and overheating
- Monitor and display connectivity

### 4.2 Windows

Include:

- Windows startup failures
- Blue Screen of Death (BSOD)
- Unexpected shutdowns
- Slow system performance
- High CPU, RAM and disk usage
- Device Manager problems
- Driver issues
- Windows Update problems
- System File Checker (SFC)
- DISM
- Event Viewer

### 4.3 Networking

Include:

- No internet connection
- Ethernet problems
- Wi-Fi problems
- IP configuration
- Default gateway
- DNS resolution
- Network adapter problems
- Packet loss and latency
- ipconfig
- ping
- tracert
- nslookup
- netstat

The knowledge base should be modular so new
diagnostic categories can be added later.

---

## 5. AI Policy

The MVP must NOT depend on external AI APIs.

Core diagnostic decisions must use:

- Python logic
- Structured knowledge
- Rule-based classification
- Conditional diagnostic workflows
- Evidence-based decision making

AI may be considered as an optional enhancement
in a future version.

AI must not replace the core diagnostic engine.

---

## 6. Core Functional Requirements

### 6.1 Incident Input

Users should be able to describe an IT problem
using natural language.

The system should identify relevant information such as:

- Device type
- Symptoms
- Error messages
- Operating system
- Recent changes
- Frequency of occurrence
- Operating conditions

Missing information should be requested when necessary.

### 6.2 Issue Classification

Classify incidents into supported categories:

- Hardware
- Windows
- Networking

Classification should be extensible.

### 6.3 Diagnostic Engine

The diagnostic engine must:

1. Select an appropriate workflow.
2. Present one primary diagnostic step at a time.
3. Collect user responses.
4. Evaluate test results.
5. Apply conditional rules.
6. Determine the next appropriate step.
7. Stop or escalate when necessary.

Avoid presenting users with an overwhelming
list of troubleshooting actions.

### 6.4 Diagnostic Knowledge Base

Diagnostic knowledge should be stored separately
from application logic.

Each diagnostic workflow should support:

- Workflow ID
- Workflow name
- Category
- Description
- Diagnostic steps
- Step instructions
- Expected results
- Abnormal results
- Conditional branching
- Evidence requirements
- Safety warnings
- References

The knowledge base must be maintainable
without rewriting the diagnostic engine.

### 6.5 Evidence Management

Record diagnostic activities and results.

Evidence must be traceable to the relevant
incident and diagnostic step.

Do not treat unverified assumptions as facts.

### 6.6 Incident Management

Support:

- Creating incidents
- Viewing incident details
- Updating incident status
- Recording diagnostic history
- Recording findings
- Recording resolution
- Reviewing previous cases

### 6.7 Incident Reports

Generate structured reports containing:

- Incident summary
- Reported symptoms
- Device and system information
- Diagnostic steps performed
- Test results
- Evidence collected
- Findings
- Root cause status
- Resolution
- Recommendations

### 6.8 Learning Mode

Provide technical explanations for diagnostic steps.

The learning content should explain both
the procedure and the underlying technical principles.

---

## 7. Technology Stack

Use the following technology stack for the MVP:

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- JSON
- Pytest
- Git
- GitHub

Do not introduce unnecessary frameworks
or external services without a clear reason.

---

## 8. Proposed Architecture

### Diagnostic Module

- classifier.py
- keyword_extractor.py
- diagnostic_engine.py
- troubleshooting.py

### Knowledge Module

- knowledge_base.py
- hardware_rules.json
- windows_rules.json
- network_rules.json

### Service Module

- incident_service.py
- report_service.py
- search_builder.py

### Database Module

- models.py
- db.py

### Web Module

- routes.py
- templates/
- static/

Architecture may evolve as implementation progresses,
but changes must be justified.

---

## 9. Development Principles

### 9.1 Modular Design

Keep responsibilities separated.

Avoid placing all application logic
inside one Python file.

### 9.2 Maintainability

Use clear naming conventions,
readable code and appropriate documentation.

### 9.3 Testability

Important functions and diagnostic rules
must have automated tests.

### 9.4 Reliability

Diagnostic decisions should be deterministic
and reproducible.

### 9.5 Extensibility

New diagnostic workflows should be addable
without major changes to existing modules.

### 9.6 Documentation

Keep documentation consistent with the actual
implementation.

Never document a feature as completed
unless it has been implemented and verified.

---

## 10. Safety Requirements

Safety takes priority over diagnostic completion.

The system must:

- Never instruct users to remove or reconnect
  hardware while the device is powered.
- Never instruct users to open a power supply unit
  for internal repair.
- Require shutdown and disconnection from power
  before relevant internal hardware work.
- Include ESD precautions where applicable.
- Stop and recommend professional assistance
  if there is a swollen battery, smoke,
  burning smell or electrical damage.
- Provide strong warnings before BIOS or firmware updates.
- Recommend backups before destructive OS repair,
  reset or formatting procedures.
- Distinguish read-only commands from commands
  that modify system configuration.
- Escalate procedures beyond the user's skill level.

Never encourage users to perform dangerous
hardware or electrical repairs.

---

## 11. Testing Requirements

Use Pytest.

Test coverage should include:

- Keyword extraction
- Issue classification
- Knowledge base loading
- Workflow validation
- Diagnostic rule evaluation
- Conditional branching
- Invalid input handling
- Incident management
- Report generation

Include normal cases, edge cases and invalid cases.

Do not assume code works simply because
it has been written.

Run relevant tests and verify results.

---

## 12. Development Roadmap

Phase 1 — Diagnostic Engine Foundation

- Define knowledge base schema
- Define diagnostic workflow structure
- Define diagnostic step and branching rules
- Define evidence and test-result representations
- Implement initial diagnostic engine
- Write automated tests

Phase 2 — Diagnostic Knowledge Base

- Hardware workflows
- Windows workflows
- Networking workflows
- Validate diagnostic logic and safety requirements

Phase 3 — Flask Web Application

- Application setup
- User interface
- Incident input
- Diagnostic workflow interface

Phase 4 — Incident Management

- SQLite integration
- Incident records
- Diagnostic history
- Evidence storage

Phase 5 — Learning Mode and Reports

- Technical explanations
- Learning content
- Professional incident reports

Phase 6 — Quality Assurance and Deployment

- Expand test coverage
- Improve documentation
- GitHub repository maintenance
- CI/CD
- Deployment

---

## 13. Project Documentation

Maintain the following documents:

- README.md
- docs/project_specification.md
- docs/architecture.md
- docs/knowledge_base_design.md
- docs/development_progress.md

Keep AGENTS.md as the project-wide instruction file.

Update documentation when important design
or implementation decisions change.

---

## 14. AI Coding Assistant Instructions

When assisting with this project:

1. Follow this document as the project baseline.
2. Do not change the product direction without discussion.
3. Do not introduce AI API dependencies into the MVP.
4. Do not simplify the system into a basic FAQ
   or chatbot.
5. Preserve evidence-based diagnostic principles.
6. Follow all safety requirements.
7. Explain significant architectural decisions.
8. Avoid unnecessary complexity.
9. Do not claim unimplemented features are complete.
10. Verify code through tests where appropriate.

When creating or modifying Python files:

- Explain the purpose of each major function.
- Explain important inputs and outputs.
- Explain how functions interact.
- Keep code readable and modular.
- Include appropriate error handling.
- Provide tests for important logic.

---

## 15. Development Interaction Rules

Development should proceed one clearly defined step at a time.

For each step:

1. Explain the objective.
2. Explain why the step is necessary.
3. Identify the files involved.
4. Explain the proposed design.
5. Implement the change.
6. Run relevant tests.
7. Explain the results.
8. Confirm completion before moving to the next step.

Do not skip foundational design decisions.

Use professional technical terminology
where appropriate, with clear explanations.

---

## 16. Current Project Status

Project setup has started.

The project directory has been created.

Current task:
Establish the project documentation
and define the diagnostic knowledge base design.

Next recommended technical task:

Define the Diagnostic Knowledge Base schema,
including:

- Workflow structure
- Diagnostic step structure
- Conditional branching
- Evidence representation
- Test-result representation
- Safety warnings
- Technical references

Validate the schema using representative
Hardware, Windows and Networking examples.

Do not begin large-scale implementation
before the foundational data design is agreed.