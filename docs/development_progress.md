# IT Support Diagnostic & Case Management System

**Document Type:** Development Progress  
**Version:** 1.1  
**Last Updated:** 2026-11-22  
**Project Status:** Planning and Technical Design (Aligned for Cross-OS MVP)

---

## 1. Overall Project Status

The project is currently in the initial planning and technical design stage.

The project directory and foundational documentation have been created.

Core application development has not yet started.

### Current Status

| Area | Status |
|---|---|
| Project Initialization | Completed |
| Master Project Instructions | Completed |
| Product Specification | Completed |
| System Architecture | Completed |
| Knowledge Base Design | Completed |
| Development Progress Documentation | In Progress |
| JSON Knowledge Base Implementation | Completed |
| Diagnostic Engine Implementation | Completed |
| Automated Testing | In Progress (45 tests passing: KB + Parser + Engine + Classifier + DB + Reports) |
| Flask Application | Pending |
| SQLite Integration | Completed |
| Incident Management | Completed |
| Report Generation | Completed |
| Deployment | Pending |

---

## 2. Completed Tasks

### Phase 0 — Project Initialization

Completed:

- Created IT_Support_Diagnostic_Assistant project directory.
- Opened the project directory in Visual Studio Code.
- Created AGENTS.md.
- Defined the project direction and development requirements.

### Phase 1 — Product and Technical Design

Completed:

- Created docs directory.
- Created README.md.
- Created project_specification.md.
- Created architecture.md.
- Created knowledge_base_design.md.

### Design Decisions Confirmed

Product direction:

Hybrid — Professional IT Diagnostic Platform + Cross-OS IT Support Learning Platform.

Initial technical scope (Cross-OS):

- PC Hardware (`hardware`)
- Operating Systems (`os` — Windows, Linux, macOS)
- Networking (`network` — Windows, Linux, macOS)

MVP workflow strategy:

- Start with **3 flagship high-depth workflows** (`NET-001`, `HW-001`, `OS-001`) instead of 18 shallow workflows, prioritizing end-to-end depth, cross-OS accuracy, and test coverage.

Key MVP differentiators (vs. generic AI chatbots):

- **Lightweight Command Output Parser** (`output_parser.py`) for key diagnostic commands (`ping`, `ipconfig`/`ifconfig`/`ip a`) to deterministically extract evidence and suggest normalized results.
- **Handoff-Ready Escalation Reports** (Markdown / printable HTML with ruled-out causes and evidence chain for L1-to-L2 handoff).
- **Side-by-Side Cross-OS Learning Panel** (technical principles, command risk badges, and Windows/Linux/macOS equivalent tabs).

MVP technology stack:

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

AI policy:

Core diagnostic functionality will use deterministic Python logic and structured knowledge.

External AI API integration is not required for the MVP.

Architecture:

Modular layered architecture with a data-driven diagnostic engine.

---

## 3. Current Development Stage

Current stage:

Foundational Technical Design.

The next objective is to validate and implement the diagnostic knowledge base before developing the complete diagnostic engine.

The knowledge base is the foundation for workflow execution and conditional decision-making.

---

## 4. Pending Development Tasks

### Phase 2 — Knowledge Base Foundation

Pending tasks:

- Define and validate the final JSON schema (including `os_variants`, `outcomes`, `command_risk_level`, `learning_content`, `parser_key`, and `safety_red_flags`).
- Create the 3 flagship MVP workflows:
  - `NET-001` (No Internet Connectivity — Windows/Linux/macOS)
  - `HW-001` (PC Does Not Power On / No Display)
  - `OS-001` (Slow System Performance / High Resource Usage — Windows/Linux/macOS)
- Implement `knowledge_base.py` loading and structural validation.
- Create automated knowledge base tests.

### Phase 3 — Diagnostic Engine & Output Parser Foundation

Pending tasks:

- Implement workflow initialization and target OS resolution.
- Implement diagnostic session state.
- Implement diagnostic step retrieval.
- Implement multi-outcome and fallback test-result validation.
- Implement conditional branching and cycle control (`max_visits`).
- Implement diagnostic termination and safety escalation (`safety_stop`).
- Implement lightweight deterministic `output_parser.py` for key commands (`ping`, `ipconfig`/`ifconfig`/`ip a`).
- Create diagnostic engine and output parser unit tests.

### Phase 4 — Incident and Evidence Management

Pending tasks:

- Define database schema.
- Implement SQLite initialization.
- Define incident records.
- Define diagnostic session records.
- Define test-result records.
- Define evidence records.
- Implement incident services.
- Test database operations.

### Phase 5 — Flask Application

Pending tasks:

- Initialize Flask application.
- Implement application routes.
- Build incident input interface.
- Build diagnostic workflow interface.
- Display diagnostic results.
- Integrate application services.

### Phase 6 — Reports and Cross-OS Learning Mode

Pending tasks:

- Implement handoff-ready incident & escalation report generation (Markdown / printable HTML, ruled-out causes, evidence chain).
- Build expandable Cross-OS Learning Panel (technical explanations, test limitations, command risk badges, and Windows/Linux/macOS comparison tabs).
- Review report accuracy and traceability.

### Phase 7 — Quality Assurance and Deployment

Pending tasks:

- Expand automated test coverage.
- Review safety requirements.
- Improve error handling.
- Complete README documentation.
- Configure GitHub repository.
- Add CI/CD where appropriate.
- Prepare deployment.

---

## 5. Immediate Next Action

The next development task is:

**Phase 2.1 — Finalize and validate the JSON Knowledge Base Schema.**

Before writing the Python engine, finalize and validate the concrete JSON schema against the 3 flagship MVP workflows (`NET-001`, `HW-001`, `OS-001`).

The validation should confirm:

1. All categories can use the same workflow structure.
2. Diagnostic steps can support different types of tests.
3. Every supported test result has a defined transition or safe default policy.
4. Conditional branching works without workflow-specific Python code.
5. Safety-stop conditions override normal workflow progression.
6. Evidence can be associated with incidents and diagnostic steps.
7. Invalid workflows can be rejected before execution.

The schema must be agreed upon before large-scale workflow creation.

---

## 6. Development Governance

### Completion Criteria

A task should only be marked Completed when:

- The required implementation or documentation exists.
- Relevant validation has been performed.
- Automated tests pass where applicable.
- The result has been reviewed.

### Change Management

Significant changes to product direction, technical scope, architecture, or diagnostic methodology must be documented.

### Documentation Maintenance

Update this file whenever a major development milestone is completed.

Keep documentation consistent with the actual source code and test results.

Never report planned functionality as implemented functionality.

---

## 7. Project Milestones

| Milestone | Description | Status |
|---|---|---|
| M0 | Project initialization | Completed |
| M1 | Product and technical design | Completed |
| M2 | Knowledge base foundation | Completed |
| M3 | Diagnostic engine | Completed |
| M4 | Incident and evidence management | Completed |
| M5 | Flask application | Pending |
| M6 | Reports and learning mode | Pending |
| M7 | QA and deployment | Pending |

---

## 8. Current Project Structure

```text
IT_Support_Diagnostic_Assistant/
│
├── AGENTS.md
├── README.md
│
└── docs/
    ├── project_specification.md
    ├── architecture.md
    ├── knowledge_base_design.md
    └── development_progress.md
```

This represents the current documentation structure.

Application source code, tests, and diagnostic data have not yet been created.

---

## 9. Project Notes

The project prioritizes:

- Evidence-based diagnosis
- Deterministic decision-making
- Reusable diagnostic workflows
- Maintainable architecture
- Safety-aware troubleshooting
- Technical learning
- Professional incident documentation

The core diagnostic engine must remain independent of external AI APIs.

The initial implementation should prioritize correctness, clarity, testability, and extensibility over unnecessary complexity.