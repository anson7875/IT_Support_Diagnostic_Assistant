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

### 4.2 Operating Systems (Windows, Linux, macOS)

Include cross-platform OS troubleshooting and OS-specific equivalents:

- OS startup and boot failures
- System crashes (Windows BSOD, Linux kernel panic, macOS kernel panic)
- Unexpected shutdowns
- Slow system performance and high CPU, RAM, or disk usage
- Device and driver issues (Device Manager, `lspci`/`lsusb`/`dmesg`, System Information)
- OS updates and package/system repair tools (SFC/DISM, `apt`/`dnf`/`systemctl`, Disk Utility/First Aid)
- System logs (Event Viewer, `journalctl`/`/var/log`, Console.app/`log show`)

### 4.3 Networking (Cross-OS: Windows, Linux, macOS)

Include:

- No internet connection
- Ethernet problems
- Wi-Fi problems
- IP configuration
- Default gateway
- DNS resolution
- Network adapter problems
- Packet loss and latency
- Cross-OS diagnostic commands:
  - Windows: `ipconfig`, `ping`, `tracert`, `nslookup`, `netstat`
  - Linux: `ip a` / `ip r`, `ping`, `traceroute`, `dig` / `nslookup`, `ss`
  - macOS: `ifconfig` / `networksetup`, `ping`, `traceroute`, `scutil --dns` / `nslookup`, `netstat`

The knowledge base should be modular so new
diagnostic categories and OS variants can be added later.

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

- Hardware (`hardware`)
- Operating Systems (`os` — Windows, Linux, macOS)
- Networking (`network` — cross-OS)

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

### 6.7 Incident & Escalation Handoff Reports

Generate structured, handoff-ready reports (e.g., for L1-to-L2 escalation) containing:

- Incident summary & target OS environment
- Reported symptoms
- Device and system information
- Diagnostic steps performed
- Test results and parsed command outputs
- Evidence collected
- Ruled-out causes
- Findings and root cause status
- Resolution (if resolved)
- Escalation notes and recommendations

Support exporting or copying reports in clean structured formats (e.g., Markdown / printable HTML).

### 6.8 Learning Mode (Cross-OS)

Provide technical explanations for diagnostic steps via an expandable learning panel.

The learning content should explain:

- The procedure and underlying technical principles (e.g., OSI layers, OS architecture)
- Test limitations
- Command risk level (`read_only`, `system_change`, `destructive`)
- Cross-OS command and GUI equivalents (Windows, Linux, macOS side-by-side comparison)

### 6.9 Lightweight Command Output Parser

Provide deterministic Python regex/rule-based parsing for selected common diagnostic command outputs (e.g., `ping`, `ipconfig` / `ifconfig` / `ip a`) in the MVP to automatically extract structured evidence and suggest normalized test results.

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
- output_parser.py
- diagnostic_engine.py
- troubleshooting.py

### Knowledge Module

- knowledge_base.py
- hardware_rules.json
- os_rules.json
- network_rules.json

### Service Module

- incident_service.py
- report_service.py

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

Phase 0 — Project Initialization (Completed)

- Project directory setup and Git initialization
- Master project instructions (`AGENTS.md`)

Phase 1 — Product and Technical Design (Completed)

- Product specification, architecture, knowledge base design, and development progress tracking

Phase 2 — Knowledge Base Foundation

- Finalize and validate JSON schema (supporting Windows/Linux/macOS, multi-outcome branching, learning content, command risk levels, and safety triggers)
- Create 3 flagship MVP workflows (1 Hardware, 1 Cross-OS Operating System, 1 Cross-OS Networking)
- Implement `knowledge_base.py` loading and structural validation
- Write automated knowledge base tests

Phase 3 — Diagnostic Engine & Lightweight Output Parser

- Implement diagnostic session state, step retrieval, outcome evaluation, conditional branching, cycle control, and safety-stop override
- Implement lightweight deterministic command output parser (`output_parser.py`) for key commands (e.g., `ping`, `ipconfig`/`ifconfig`/`ip a`)
- Write diagnostic engine and parser unit tests

Phase 4 — Incident and Evidence Management

- SQLite database schema and initialization
- Incident records, diagnostic sessions, step results, evidence storage, findings, and resolutions
- Incident service and database tests

Phase 5 — Flask Web Application

- Application setup and routes
- Incident input interface (including target OS selection)
- Interactive step-by-step diagnostic workflow interface (with command paste/parse support)

Phase 6 — Reports and Cross-OS Learning Mode

- Handoff-ready incident & escalation report generation (Markdown / printable HTML)
- Side-by-side cross-OS learning drawer (Windows / Linux / macOS comparison, technical principles, command risk badges)

Phase 7 — Quality Assurance and Deployment

- Expand automated test coverage
- Review safety requirements and error handling
- Complete portfolio-ready `README.md`
- GitHub repository maintenance, CI/CD, and deployment

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

Project setup and foundational design documentation have been completed and aligned for cross-OS support (Windows, Linux, macOS) and focused MVP delivery.

Current task:
Phase 2.1 — Finalize and validate the Diagnostic Knowledge Base JSON schema, including:

- Workflow structure (with cross-OS support)
- Diagnostic step structure (with `os_variants`, `outcomes`, `command_risk_level`, `learning_content`)
- Conditional branching and cycle limits
- Evidence and test-result representations
- Safety warnings and `safety_stop` trigger rules
- Technical references

Validate the schema using 3 flagship MVP workflows (Hardware, Cross-OS Operating System, Cross-OS Networking).

Do not begin large-scale implementation before the foundational JSON schema is finalized and validated.