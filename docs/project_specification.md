# IT Support Diagnostic & Case Management System

**Document Type:** Product Specification  
**Version:** 1.0  
**Project Status:** Initial Design  
**Product Direction:** Hybrid — Professional IT Diagnostic Platform + IT Support Learning Platform

---

## 1. Product Overview

### 1.1 Introduction

The IT Support Diagnostic & Case Management System is a structured IT troubleshooting and diagnostic platform designed to assist users in identifying, investigating, documenting, and resolving common IT problems.

The platform combines rule-based diagnostic workflows, technical knowledge, evidence management, incident tracking, and educational explanations.

Unlike conventional FAQ websites or AI chatbot-based troubleshooting tools, the system guides users through a structured diagnostic process and determines subsequent actions based on actual test results and collected evidence.

### 1.2 Product Vision

To develop a professional IT diagnostic platform that demonstrates practical IT Support methodology while helping users understand the technical principles behind troubleshooting procedures.

The system should be useful both as a practical troubleshooting tool and as a technical learning platform.

### 1.3 Product Objectives

The project aims to:

1. Provide structured troubleshooting workflows.
2. Improve diagnostic consistency and traceability.
3. Reduce reliance on unsupported assumptions.
4. Explain the technical principles behind diagnostic procedures.
5. Maintain incident and diagnostic history.
6. Generate structured IT support incident reports.
7. Demonstrate practical IT Support and software engineering capabilities.

---

## 2. Problem Statement

Traditional IT troubleshooting methods often involve searching online articles, following disconnected instructions, or relying on personal experience.

These approaches may result in:

- Inconsistent troubleshooting procedures.
- Repeated or unnecessary diagnostic actions.
- Insufficient evidence collection.
- Difficulty identifying the actual root cause.
- Poor documentation of diagnostic activities.
- Limited understanding of the technical principles involved.

An AI chatbot may generate troubleshooting suggestions, but generated suggestions alone do not necessarily provide a persistent, structured, evidence-based diagnostic record.

This project addresses these limitations by providing controlled diagnostic workflows, conditional decision-making, evidence recording, and incident management.

---

## 3. Target Users

### 3.1 Primary Users

- IT Support Technicians
- Helpdesk Support Staff
- Junior System Administrators
- IT Support Students
- Individuals learning practical IT troubleshooting

### 3.2 Secondary Users

- Technical learners
- Small IT support teams
- Individuals who want to document and review troubleshooting cases

---

## 4. Product Scope

The initial product scope covers three major technical categories.

### 4.1 PC Hardware Diagnostics

Supported topics include:

- Power-related problems
- Boot and POST failures
- No display
- RAM-related issues
- Storage detection and health
- CPU and GPU symptoms
- Cooling and overheating
- Monitor and display connectivity

### 4.2 Windows Diagnostics

Supported topics include:

- Windows startup failures
- Blue Screen of Death (BSOD)
- Unexpected shutdowns
- Slow system performance
- High CPU, RAM, and disk usage
- Device Manager problems
- Driver-related issues
- Windows Update problems
- System File Checker (SFC)
- DISM
- Event Viewer

### 4.3 Networking Diagnostics

Supported topics include:

- No internet connection
- Ethernet connectivity problems
- Wi-Fi connectivity problems
- IP configuration
- Default gateway issues
- DNS resolution failures
- Network adapter problems
- Packet loss and latency
- ipconfig
- ping
- tracert
- nslookup
- netstat

The knowledge base must support future expansion into additional IT support categories.

---

## 5. Functional Requirements

### FR-01: Incident Input

The system shall allow users to describe an IT incident using natural language.

The system should extract relevant information, including:

- Device type
- Symptoms
- Error messages
- Operating system
- Recent system or hardware changes
- Frequency of occurrence
- Conditions under which the problem occurs

The system should request missing information when necessary.

### FR-02: Issue Classification

The system shall classify incidents into supported technical categories.

Initial categories:

- Hardware
- Windows
- Networking

The classification mechanism should support future expansion.

### FR-03: Diagnostic Workflow Selection

The system shall select an appropriate diagnostic workflow based on the incident description and extracted information.

The system should avoid assigning a workflow when the available information is insufficient or ambiguous.

### FR-04: Step-by-Step Diagnosis

The system shall present one primary diagnostic step at a time.

Each diagnostic step should contain:

- Step ID
- Step title
- Objective
- Instructions
- Required tools or commands
- Expected results
- Possible abnormal results
- Safety warnings
- Relevant technical explanations

### FR-05: Conditional Diagnostic Branching

The system shall evaluate user responses and test results against predefined diagnostic rules.

The next diagnostic step must be determined by the applicable conditions.

The system should support:

- Normal result
- Abnormal result
- Inconclusive result
- Test not performed
- Unable to perform test
- Safety escalation

### FR-06: Diagnostic Explanation

The system shall explain the purpose and technical principles of diagnostic procedures.

Explanations should include:

- What is being tested
- Why the test is necessary
- How to perform the test
- What normal results indicate
- What abnormal results may suggest
- Limitations of the test

### FR-07: Evidence Recording

The system shall record diagnostic observations and test results.

Evidence should be associated with:

- Incident ID
- Diagnostic workflow ID
- Diagnostic step ID
- Timestamp
- Test method
- Recorded result
- User observations

The system must distinguish between reported information, observed results, and verified findings.

### FR-08: Incident Management

The system shall support:

- Creating incidents
- Viewing incident details
- Updating incident status
- Recording diagnostic activities
- Recording findings
- Recording resolutions
- Reviewing historical incidents

### FR-09: Root Cause Management

The system shall distinguish between:

- Possible cause
- Suspected cause
- Evidence-supported finding
- Confirmed root cause

A suspected cause must not automatically be recorded as a confirmed root cause.

### FR-10: Incident Report Generation

The system shall generate structured incident reports containing:

- Incident summary
- Reported symptoms
- Device and system information
- Diagnostic procedures performed
- Test results
- Evidence collected
- Findings
- Root cause status
- Resolution
- Recommendations

### FR-11: Learning Mode

The system shall provide technical explanations to help users understand diagnostic procedures and relevant IT concepts.

Learning content should be connected to the corresponding diagnostic steps.

---

## 6. Diagnostic Methodology Requirements

### 6.1 Evidence-Based Diagnosis

Diagnostic decisions must be based on available information and recorded evidence.

The system must not present assumptions as verified facts.

### 6.2 Structured Diagnostic Process

A typical diagnostic process should follow:

1. Incident description
2. Information extraction
3. Issue classification
4. Workflow selection
5. Diagnostic step execution
6. Result collection
7. Rule evaluation
8. Next-step selection
9. Findings assessment
10. Resolution or escalation

### 6.3 Diagnostic Traceability

The system should maintain a traceable relationship between:

- Incident
- Workflow
- Diagnostic step
- Test execution
- Test result
- Evidence
- Findings
- Resolution

### 6.4 Inconclusive Results

The system must support inconclusive results.

It should not force a diagnostic conclusion when evidence is insufficient.

### 6.5 Diagnostic Termination

A diagnostic workflow should terminate when:

- A supported resolution is reached.
- The available evidence is sufficient to establish a finding.
- Further testing is unnecessary.
- The issue requires specialist intervention.
- A safety condition requires immediate termination.
- No supported diagnostic path remains.

---

## 7. Evidence and Data Management Requirements

The system should preserve the distinction between different information types.

| Information Type | Description |
|---|---|
| User Report | Information provided by the user |
| Observation | What the user or technician observes |
| Test | A diagnostic action performed |
| Test Result | The outcome of the test |
| Evidence | Information supporting an assessment |
| Finding | An interpretation supported by evidence |
| Root Cause | The confirmed underlying cause |
| Resolution | Action taken to address the issue |

The system should retain diagnostic history to support future review and reporting.

---

## 8. Safety Requirements

Safety takes priority over diagnostic completion.

The system must:

1. Never instruct users to remove or reconnect hardware while powered.
2. Never instruct users to open a power supply unit for internal repair.
3. Require appropriate shutdown and power disconnection before relevant internal hardware work.
4. Include ESD precautions where applicable.
5. Stop and recommend professional assistance when there is a swollen battery, smoke, burning smell, or electrical damage.
6. Provide strong warnings before BIOS or firmware updates.
7. Recommend data backups before destructive operating system repair, reset, or formatting.
8. Distinguish read-only commands from commands that modify system configuration.
9. Escalate procedures beyond the user's skill level.

Every diagnostic workflow must be reviewed for relevant safety risks before being released.

---

## 9. Technical Requirements

### 9.1 Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Web Framework | Flask |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Knowledge Base | JSON |
| Automated Testing | Pytest |
| Version Control | Git |
| Repository Hosting | GitHub |

### 9.2 Architecture Requirements

The application should separate the following responsibilities:

- Incident input and classification
- Diagnostic workflow execution
- Knowledge base management
- Evidence recording
- Incident management
- Report generation
- Web presentation
- Database operations

Diagnostic knowledge should be separated from application logic.

### 9.3 Maintainability

The system should use modular components, clear naming conventions, and appropriate documentation.

### 9.4 Reliability

Diagnostic rules should produce deterministic and reproducible outcomes when given the same inputs.

### 9.5 Testability

Important diagnostic functions and business logic must have automated tests.

---

## 10. Non-Functional Requirements

### NFR-01: Usability

The interface should be understandable to users with basic IT knowledge.

### NFR-02: Maintainability

The application should be modular and easy to update.

### NFR-03: Extensibility

New diagnostic categories and workflows should be addable without major changes to the diagnostic engine.

### NFR-04: Reliability

The system should handle invalid input and incomplete diagnostic results without producing unsupported conclusions.

### NFR-05: Traceability

Diagnostic actions and results should be associated with their corresponding incidents and workflow steps.

### NFR-06: Safety

The system must identify dangerous procedures and prevent unsafe diagnostic guidance.

### NFR-07: Performance

The MVP should operate efficiently on a typical personal computer without requiring external AI services.

---

## 11. MVP Scope

The MVP will focus on establishing a reliable diagnostic foundation.

### Included in MVP

- Natural-language incident input
- Basic keyword and information extraction
- Rule-based issue classification
- Structured JSON knowledge base
- Diagnostic workflow engine
- Conditional diagnostic branching
- Test-result recording
- Initial evidence representation
- Flask-based web interface
- SQLite incident storage
- Basic incident reports
- Pytest automated tests

### Excluded from Initial MVP

- External AI API integration
- Automatic hardware detection
- Remote computer control
- Automated system repair
- Enterprise authentication and authorization
- Multi-tenant deployment
- Advanced analytics dashboard
- Complex enterprise ticketing integrations

These features may be considered in future versions.

---

## 12. Acceptance Criteria

The MVP will be considered functionally acceptable when:

1. A user can submit a supported IT incident.
2. The system can extract relevant information from the description.
3. The system can classify supported incident categories.
4. The system can select an appropriate diagnostic workflow.
5. The system can present diagnostic steps sequentially.
6. The system can evaluate test results.
7. Conditional rules can select different next steps.
8. The system can record diagnostic evidence.
9. The system can distinguish suspected causes from confirmed root causes.
10. The system can save and retrieve incident records.
11. The system can generate a structured incident report.
12. Important diagnostic logic has automated test coverage.
13. Safety-related conditions can trigger appropriate warnings or escalation.
14. The system does not require external AI API services for core functionality.

All acceptance criteria must be verified through implementation and testing. They must not be marked complete merely because they are documented.

---

## 13. Future Development Opportunities

Potential future enhancements include:

- Expanded hardware diagnostic knowledge
- Advanced Windows event analysis
- More comprehensive networking diagnostics
- Searchable diagnostic knowledge base
- Advanced incident analytics
- User accounts and role-based access
- Knowledge base version management
- Optional AI-assisted incident summarization
- Optional AI-assisted explanation generation
- Integration with external IT service management systems

Future enhancements must not compromise the evidence-based diagnostic foundation.

---

## 14. Document Governance

**Document Owner:** Project Maintainer  
**Version:** 1.0  
**Status:** Initial Design

This document defines the initial product requirements and MVP scope.

Changes to product direction, core functionality, technical scope, or safety requirements should be documented and reviewed before implementation.

The actual implementation and test results remain the source of truth for development status.