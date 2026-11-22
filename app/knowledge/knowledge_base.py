"""Diagnostic Knowledge Base loader and structural validator.

Loads JSON workflow rule files from ``app/data/``, enforces structural and
graph integrity rules (unique IDs, valid transition targets, reachability,
safety fields, cross-OS variants, and cycle visit limits), and provides
query helpers for the Diagnostic Engine and presentation layer.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

SUPPORTED_CATEGORIES = frozenset({"hardware", "os", "network"})
SUPPORTED_OS_VALUES = frozenset({"windows", "linux", "macos", "all"})
CONCRETE_OS_VALUES = frozenset({"windows", "linux", "macos"})
VALID_TEST_TYPES = frozenset(
    {
        "visual_inspection",
        "physical_check",
        "command_execution",
        "system_information",
        "performance_check",
        "hardware_test",
        "user_confirmation",
    }
)
VALID_RISK_LEVELS = frozenset(
    {"read_only", "system_change", "destructive", "not_applicable"}
)
VALID_RESULT_CODES = frozenset(
    {"normal", "abnormal", "inconclusive", "not_performed", "unable_to_perform"}
)
VALID_TRANSITION_ACTIONS = frozenset(
    {"next_step", "request_more_information", "pause", "complete", "escalate"}
)
REQUIRED_FALLBACK_RESULTS = frozenset(
    {"inconclusive", "not_performed", "unable_to_perform"}
)
VALID_PARSER_KEYS = frozenset({"ip_config", "ping", None})


class KnowledgeBaseValidationError(ValueError):
    """Raised when a knowledge base JSON file fails structural validation."""


def _require_non_empty_str(obj: dict[str, Any], field: str, context: str) -> str:
    value = obj.get(field)
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeBaseValidationError(
            f"{context}: '{field}' must be a non-empty string."
        )
    return value


def _validate_transition(
    transition: Any, step_ids: set[str], context: str
) -> None:
    if not isinstance(transition, dict):
        raise KnowledgeBaseValidationError(f"{context}: transition must be an object.")
    action = transition.get("action")
    if action not in VALID_TRANSITION_ACTIONS:
        raise KnowledgeBaseValidationError(
            f"{context}: invalid transition action '{action}'."
        )
    next_step_id = transition.get("next_step_id")
    if action == "next_step":
        if not isinstance(next_step_id, str) or next_step_id not in step_ids:
            raise KnowledgeBaseValidationError(
                f"{context}: next_step_id '{next_step_id}' does not exist in workflow steps."
            )
    elif next_step_id is not None and not isinstance(next_step_id, str):
        raise KnowledgeBaseValidationError(
            f"{context}: next_step_id must be a string or null."
        )


def _validate_safety_red_flags(flags: Any, context: str) -> None:
    if not isinstance(flags, list):
        raise KnowledgeBaseValidationError(f"{context}: safety_red_flags must be a list.")
    seen_ids: set[str] = set()
    for idx, flag in enumerate(flags):
        flag_ctx = f"{context}.safety_red_flags[{idx}]"
        if not isinstance(flag, dict):
            raise KnowledgeBaseValidationError(f"{flag_ctx}: must be an object.")
        flag_id = _require_non_empty_str(flag, "flag_id", flag_ctx)
        if flag_id in seen_ids:
            raise KnowledgeBaseValidationError(
                f"{flag_ctx}: duplicate flag_id '{flag_id}'."
            )
        seen_ids.add(flag_id)
        _require_non_empty_str(flag, "label", flag_ctx)
        _require_non_empty_str(flag, "warning_message", flag_ctx)
        _require_non_empty_str(flag, "escalation_instruction", flag_ctx)


def _validate_step(
    step: Any, step_ids: set[str], ref_ids: set[str], workflow_id: str
) -> None:
    if not isinstance(step, dict):
        raise KnowledgeBaseValidationError(
            f"Workflow '{workflow_id}': each step must be an object."
        )

    step_id = _require_non_empty_str(step, "step_id", f"Workflow '{workflow_id}'")
    ctx = f"Workflow '{workflow_id}' step '{step_id}'"

    _require_non_empty_str(step, "title", ctx)
    _require_non_empty_str(step, "objective", ctx)
    _require_non_empty_str(step, "expected_results", ctx)

    instructions = step.get("instructions")
    if (
        not isinstance(instructions, list)
        or not instructions
        or not all(isinstance(i, str) and i.strip() for i in instructions)
    ):
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'instructions' must be a non-empty list of strings."
        )

    if step.get("test_type") not in VALID_TEST_TYPES:
        raise KnowledgeBaseValidationError(
            f"{ctx}: invalid test_type '{step.get('test_type')}'."
        )

    if step.get("command_risk_level") not in VALID_RISK_LEVELS:
        raise KnowledgeBaseValidationError(
            f"{ctx}: invalid command_risk_level '{step.get('command_risk_level')}'."
        )

    parser_key = step.get("parser_key")
    if parser_key not in VALID_PARSER_KEYS:
        raise KnowledgeBaseValidationError(
            f"{ctx}: invalid parser_key '{parser_key}'."
        )

    max_visits = step.get("max_visits")
    if isinstance(max_visits, bool) or not isinstance(max_visits, int) or not (1 <= max_visits <= 5):
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'max_visits' must be an integer between 1 and 5."
        )

    safety_reqs = step.get("safety_requirements")
    if not isinstance(safety_reqs, list) or not all(
        isinstance(item, str) for item in safety_reqs
    ):
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'safety_requirements' must be a list of strings."
        )

    if "safety_red_flags" in step:
        _validate_safety_red_flags(step["safety_red_flags"], ctx)

    learning = step.get("learning_content")
    if not isinstance(learning, dict):
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'learning_content' must be an object."
        )
    for field in ("why_this_step", "technical_principle", "limitations"):
        _require_non_empty_str(learning, field, f"{ctx}.learning_content")

    os_variants = step.get("os_variants")
    if os_variants is not None:
        if not isinstance(os_variants, dict):
            raise KnowledgeBaseValidationError(f"{ctx}: 'os_variants' must be an object.")
        for os_key, variant in os_variants.items():
            if os_key not in CONCRETE_OS_VALUES:
                raise KnowledgeBaseValidationError(
                    f"{ctx}.os_variants: unsupported OS key '{os_key}'."
                )
            if not isinstance(variant, dict):
                raise KnowledgeBaseValidationError(
                    f"{ctx}.os_variants.{os_key}: must be an object."
                )
            v_instr = variant.get("instructions")
            if (
                not isinstance(v_instr, list)
                or not v_instr
                or not all(isinstance(i, str) and i.strip() for i in v_instr)
            ):
                raise KnowledgeBaseValidationError(
                    f"{ctx}.os_variants.{os_key}: 'instructions' must be a non-empty list of strings."
                )

    outcomes = step.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'outcomes' must be a non-empty list."
        )
    seen_outcome_ids: set[str] = set()
    for idx, outcome in enumerate(outcomes):
        o_ctx = f"{ctx}.outcomes[{idx}]"
        if not isinstance(outcome, dict):
            raise KnowledgeBaseValidationError(f"{o_ctx}: must be an object.")
        outcome_id = _require_non_empty_str(outcome, "outcome_id", o_ctx)
        if outcome_id in seen_outcome_ids:
            raise KnowledgeBaseValidationError(
                f"{o_ctx}: duplicate outcome_id '{outcome_id}'."
            )
        seen_outcome_ids.add(outcome_id)
        _require_non_empty_str(outcome, "label", o_ctx)
        if outcome.get("result_code") not in VALID_RESULT_CODES:
            raise KnowledgeBaseValidationError(
                f"{o_ctx}: invalid result_code '{outcome.get('result_code')}'."
            )
        _validate_transition(outcome.get("transition"), step_ids, o_ctx)

    result_transitions = step.get("result_transitions")
    if not isinstance(result_transitions, dict):
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'result_transitions' must be an object."
        )
    for req_code in REQUIRED_FALLBACK_RESULTS:
        if req_code not in result_transitions:
            raise KnowledgeBaseValidationError(
                f"{ctx}.result_transitions: missing required fallback '{req_code}'."
            )
    for code, transition in result_transitions.items():
        if code not in VALID_RESULT_CODES:
            raise KnowledgeBaseValidationError(
                f"{ctx}.result_transitions: invalid result code '{code}'."
            )
        _validate_transition(transition, step_ids, f"{ctx}.result_transitions.{code}")

    step_refs = step.get("reference_ids")
    if not isinstance(step_refs, list):
        raise KnowledgeBaseValidationError(f"{ctx}: 'reference_ids' must be a list.")
    for rid in step_refs:
        if rid not in ref_ids:
            raise KnowledgeBaseValidationError(
                f"{ctx}: reference_id '{rid}' not found in workflow references."
            )


def _step_neighbors(step: dict[str, Any]) -> list[str]:
    """Return all unique target step IDs referenced by a step's transitions."""
    neighbors: list[str] = []
    for outcome in step.get("outcomes", []):
        tr = outcome.get("transition", {})
        if tr.get("action") == "next_step" and tr.get("next_step_id"):
            neighbors.append(tr["next_step_id"])
    for tr in step.get("result_transitions", {}).values():
        if tr.get("action") == "next_step" and tr.get("next_step_id"):
            neighbors.append(tr["next_step_id"])
    return neighbors


def detect_cycles(workflow: dict[str, Any]) -> list[list[str]]:
    """Detect directed cycles in a workflow's step transition graph.

    Returns a list of cycle paths (each a list of step IDs). An empty list
    means the workflow graph is acyclic.
    """
    step_map = {step["step_id"]: step for step in workflow.get("steps", [])}
    visited: set[str] = set()
    in_stack: set[str] = set()
    path: list[str] = []
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        in_stack.add(node)
        path.append(node)
        for nxt in _step_neighbors(step_map[node]):
            if nxt not in step_map:
                continue
            if nxt in in_stack:
                idx = path.index(nxt)
                cycles.append(path[idx:] + [nxt])
            elif nxt not in visited:
                dfs(nxt)
        path.pop()
        in_stack.remove(node)

    for step_id in step_map:
        if step_id not in visited:
            dfs(step_id)
    return cycles


def validate_workflow(
    workflow: Any, expected_category: str | None = None
) -> None:
    """Validate a single diagnostic workflow definition.

    Checks required metadata, references, safety red flags, step schemas,
    transition targets, and reachability from ``initial_step_id``.
    """
    if not isinstance(workflow, dict):
        raise KnowledgeBaseValidationError("Workflow entry must be an object.")

    workflow_id = _require_non_empty_str(workflow, "workflow_id", "Workflow")
    ctx = f"Workflow '{workflow_id}'"

    _require_non_empty_str(workflow, "workflow_name", ctx)
    _require_non_empty_str(workflow, "description", ctx)
    _require_non_empty_str(workflow, "version", ctx)

    category = workflow.get("category")
    if category not in SUPPORTED_CATEGORIES:
        raise KnowledgeBaseValidationError(
            f"{ctx}: invalid category '{category}'."
        )
    if expected_category is not None and category != expected_category:
        raise KnowledgeBaseValidationError(
            f"{ctx}: category '{category}' does not match file category '{expected_category}'."
        )

    supported_os = workflow.get("supported_os")
    if (
        not isinstance(supported_os, list)
        or not supported_os
        or not all(os_name in SUPPORTED_OS_VALUES for os_name in supported_os)
    ):
        raise KnowledgeBaseValidationError(
            f"{ctx}: 'supported_os' must be a non-empty list of supported OS names."
        )

    _validate_safety_red_flags(workflow.get("safety_red_flags"), ctx)

    references = workflow.get("references")
    if not isinstance(references, list):
        raise KnowledgeBaseValidationError(f"{ctx}: 'references' must be a list.")
    ref_ids: set[str] = set()
    for idx, ref in enumerate(references):
        r_ctx = f"{ctx}.references[{idx}]"
        if not isinstance(ref, dict):
            raise KnowledgeBaseValidationError(f"{r_ctx}: must be an object.")
        rid = _require_non_empty_str(ref, "reference_id", r_ctx)
        if rid in ref_ids:
            raise KnowledgeBaseValidationError(
                f"{r_ctx}: duplicate reference_id '{rid}'."
            )
        ref_ids.add(rid)
        for field in ("title", "publisher", "url", "description"):
            _require_non_empty_str(ref, field, r_ctx)

    steps = workflow.get("steps")
    if not isinstance(steps, list) or not steps:
        raise KnowledgeBaseValidationError(f"{ctx}: 'steps' must be a non-empty list.")

    step_ids: set[str] = set()
    for step in steps:
        if not isinstance(step, dict):
            raise KnowledgeBaseValidationError(f"{ctx}: each step must be an object.")
        sid = _require_non_empty_str(step, "step_id", ctx)
        if sid in step_ids:
            raise KnowledgeBaseValidationError(
                f"{ctx}: duplicate step_id '{sid}'."
            )
        step_ids.add(sid)

    initial_step_id = _require_non_empty_str(workflow, "initial_step_id", ctx)
    if initial_step_id not in step_ids:
        raise KnowledgeBaseValidationError(
            f"{ctx}: initial_step_id '{initial_step_id}' not found in steps."
        )

    for step in steps:
        _validate_step(step, step_ids, ref_ids, workflow_id)

    # Verify all steps are reachable from initial_step_id via BFS.
    step_map = {step["step_id"]: step for step in steps}
    reachable: set[str] = set()
    queue: deque[str] = deque([initial_step_id])
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        for nxt in _step_neighbors(step_map[current]):
            if nxt not in reachable:
                queue.append(nxt)

    unreachable = step_ids - reachable
    if unreachable:
        raise KnowledgeBaseValidationError(
            f"{ctx}: unreachable step(s) detected: {sorted(unreachable)}."
        )


def validate_workflow_file(
    data: Any, source_name: str = "<memory>"
) -> list[dict[str, Any]]:
    """Validate a top-level knowledge base JSON document and return its workflows."""
    if not isinstance(data, dict):
        raise KnowledgeBaseValidationError(
            f"{source_name}: root JSON value must be an object."
        )
    if data.get("schema_version") != "1.0":
        raise KnowledgeBaseValidationError(
            f"{source_name}: unsupported schema_version '{data.get('schema_version')}'."
        )
    category = data.get("category")
    if category not in SUPPORTED_CATEGORIES:
        raise KnowledgeBaseValidationError(
            f"{source_name}: invalid file category '{category}'."
        )
    workflows = data.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        raise KnowledgeBaseValidationError(
            f"{source_name}: 'workflows' must be a non-empty list."
        )
    for wf in workflows:
        validate_workflow(wf, expected_category=category)
    return workflows


class KnowledgeBase:
    """In-memory repository of validated diagnostic workflows loaded from JSON."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent / "data"
        self.data_dir = Path(data_dir)
        self._workflows: dict[str, dict[str, Any]] = {}

    def load_all(self) -> None:
        """Load and validate all ``*_rules.json`` files from ``self.data_dir``."""
        if not self.data_dir.is_dir():
            raise KnowledgeBaseValidationError(
                f"Knowledge base directory not found: {self.data_dir}"
            )

        rule_files = sorted(self.data_dir.glob("*_rules.json"))
        if not rule_files:
            raise KnowledgeBaseValidationError(
                f"No '*_rules.json' files found in {self.data_dir}"
            )

        loaded: dict[str, dict[str, Any]] = {}
        for file_path in rule_files:
            try:
                raw_text = file_path.read_text(encoding="utf-8")
                data = json.loads(raw_text)
            except (OSError, json.JSONDecodeError) as exc:
                raise KnowledgeBaseValidationError(
                    f"Failed to read/parse '{file_path.name}': {exc}"
                ) from exc

            workflows = validate_workflow_file(data, source_name=file_path.name)
            for wf in workflows:
                wid = wf["workflow_id"]
                if wid in loaded:
                    raise KnowledgeBaseValidationError(
                        f"Duplicate workflow_id '{wid}' across knowledge base files."
                    )
                loaded[wid] = wf

        self._workflows = loaded

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Return a workflow definition by ID, or raise KeyError if missing."""
        if workflow_id not in self._workflows:
            raise KeyError(f"Workflow '{workflow_id}' not found.")
        return self._workflows[workflow_id]

    def list_workflows(
        self, category: str | None = None, target_os: str | None = None
    ) -> list[dict[str, Any]]:
        """Return loaded workflows, optionally filtered by category and target OS."""
        results = list(self._workflows.values())
        if category is not None:
            results = [wf for wf in results if wf["category"] == category]
        if target_os is not None:
            os_key = target_os.lower()
            results = [
                wf
                for wf in results
                if "all" in wf["supported_os"] or os_key in wf["supported_os"]
            ]
        return results

    def get_step(self, workflow_id: str, step_id: str) -> dict[str, Any]:
        """Return a raw diagnostic step by workflow ID and step ID."""
        wf = self.get_workflow(workflow_id)
        for step in wf["steps"]:
            if step["step_id"] == step_id:
                return step
        raise KeyError(f"Step '{step_id}' not found in workflow '{workflow_id}'.")

    def resolve_step_for_os(
        self, workflow_id: str, step_id: str, target_os: str = "windows"
    ) -> dict[str, Any]:
        """Return a step enriched with active instructions/commands for ``target_os``.

        Preserves ``os_variants`` so the UI Learning Drawer can still display
        side-by-side Windows, Linux, and macOS equivalents.
        """
        os_key = target_os.lower()
        if os_key not in CONCRETE_OS_VALUES:
            raise ValueError(
                f"Unsupported target_os '{target_os}'. Expected one of {sorted(CONCRETE_OS_VALUES)}."
            )

        step = self.get_step(workflow_id, step_id)
        variants = step.get("os_variants") or {}
        variant = variants.get(os_key)

        resolved = dict(step)
        resolved["resolved_os"] = os_key
        if variant:
            resolved["active_instructions"] = list(variant["instructions"])
            resolved["active_command"] = variant.get("command")
            resolved["active_gui_path"] = variant.get("gui_path")
            resolved["active_expected_output_hint"] = variant.get(
                "expected_output_hint"
            )
        else:
            resolved["active_instructions"] = list(step["instructions"])
            resolved["active_command"] = None
            resolved["active_gui_path"] = None
            resolved["active_expected_output_hint"] = None
        return resolved

    def get_references_for_step(
        self, workflow_id: str, step_id: str
    ) -> list[dict[str, Any]]:
        """Resolve a step's ``reference_ids`` into full reference objects."""
        wf = self.get_workflow(workflow_id)
        step = self.get_step(workflow_id, step_id)
        ref_map = {ref["reference_id"]: ref for ref in wf.get("references", [])}
        return [ref_map[rid] for rid in step.get("reference_ids", []) if rid in ref_map]
