"""Automated tests for the Diagnostic Knowledge Base loader and validator."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from app.knowledge.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseValidationError,
    detect_cycles,
    validate_workflow,
    validate_workflow_file,
)


def _load_real_kb() -> KnowledgeBase:
    kb = KnowledgeBase()
    kb.load_all()
    return kb


def test_load_all_flagship_workflows() -> None:
    kb = _load_real_kb()
    workflows = kb.list_workflows()
    workflow_ids = {wf["workflow_id"] for wf in workflows}
    assert workflow_ids == {"HW-001", "NET-001", "OS-001"}


def test_filter_workflows_by_category_and_os() -> None:
    kb = _load_real_kb()
    assert len(kb.list_workflows(category="network")) == 1
    assert len(kb.list_workflows(category="hardware")) == 1
    assert len(kb.list_workflows(category="os")) == 1
    # All 3 flagship workflows support windows, linux, and macos (HW-001 uses "all")
    for os_name in ("windows", "linux", "macos"):
        assert len(kb.list_workflows(target_os=os_name)) == 3


def test_resolve_step_for_cross_os_variants() -> None:
    kb = _load_real_kb()

    win_step = kb.resolve_step_for_os("NET-001", "NET-001-S2", "windows")
    linux_step = kb.resolve_step_for_os("NET-001", "NET-001-S2", "linux")
    mac_step = kb.resolve_step_for_os("NET-001", "NET-001-S2", "macos")

    assert win_step["active_command"] == "ipconfig /all"
    assert linux_step["active_command"] == "ip a && ip r"
    assert mac_step["active_command"] == "ifconfig en0 && route -n get default"
    # Side-by-side variants remain available for the Learning Drawer
    assert set(win_step["os_variants"].keys()) == {"windows", "linux", "macos"}


def test_resolve_step_fallback_for_os_agnostic_hardware_step() -> None:
    kb = _load_real_kb()
    step = kb.resolve_step_for_os("HW-001", "HW-001-S1", "macos")
    assert step["resolved_os"] == "macos"
    assert step["active_instructions"] == step["instructions"]
    assert step["active_command"] is None


def test_resolve_step_rejects_invalid_os() -> None:
    kb = _load_real_kb()
    with pytest.raises(ValueError, match="Unsupported target_os"):
        kb.resolve_step_for_os("NET-001", "NET-001-S1", "android")


def test_get_references_for_step() -> None:
    kb = _load_real_kb()
    refs = kb.get_references_for_step("NET-001", "NET-001-S2")
    ref_ids = {ref["reference_id"] for ref in refs}
    assert ref_ids == {"REF-NET-RFC3927", "REF-NET-MS-IPCONFIG"}


def test_flagship_workflows_have_no_unintended_cycles() -> None:
    kb = _load_real_kb()
    for wf in kb.list_workflows():
        assert detect_cycles(wf) == []


def test_detect_cycles_identifies_loop() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("NET-001"))
    # Introduce a deliberate loop from S2B back to S2
    for step in wf["steps"]:
        if step["step_id"] == "NET-001-S2B":
            step["outcomes"][0]["transition"]["next_step_id"] = "NET-001-S2"
    cycles = detect_cycles(wf)
    assert cycles
    assert "NET-001-S2" in cycles[0] and "NET-001-S2B" in cycles[0]


def test_rejects_broken_next_step_reference() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("NET-001"))
    wf["steps"][0]["outcomes"][0]["transition"]["next_step_id"] = "DOES-NOT-EXIST"
    with pytest.raises(KnowledgeBaseValidationError, match="does not exist"):
        validate_workflow(wf)


def test_rejects_unreachable_orphan_step() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("HW-001"))
    orphan = copy.deepcopy(wf["steps"][-1])
    orphan["step_id"] = "HW-001-ORPHAN"
    wf["steps"].append(orphan)
    with pytest.raises(KnowledgeBaseValidationError, match="unreachable"):
        validate_workflow(wf)


def test_rejects_missing_required_fallback_transition() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("OS-001"))
    del wf["steps"][0]["result_transitions"]["unable_to_perform"]
    with pytest.raises(KnowledgeBaseValidationError, match="missing required fallback"):
        validate_workflow(wf)


def test_rejects_invalid_command_risk_level() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("OS-001"))
    wf["steps"][0]["command_risk_level"] = "super_safe"
    with pytest.raises(KnowledgeBaseValidationError, match="invalid command_risk_level"):
        validate_workflow(wf)


def test_rejects_invalid_reference_id() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("NET-001"))
    wf["steps"][0]["reference_ids"].append("REF-MISSING")
    with pytest.raises(KnowledgeBaseValidationError, match="not found in workflow references"):
        validate_workflow(wf)


def test_rejects_duplicate_workflow_id_across_files(tmp_path: Path) -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("NET-001"))
    payload = {"schema_version": "1.0", "category": "network", "workflows": [wf]}
    (tmp_path / "a_rules.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "b_rules.json").write_text(json.dumps(payload), encoding="utf-8")

    dup_kb = KnowledgeBase(data_dir=tmp_path)
    with pytest.raises(KnowledgeBaseValidationError, match="Duplicate workflow_id"):
        dup_kb.load_all()


def test_rejects_invalid_json_file(tmp_path: Path) -> None:
    (tmp_path / "broken_rules.json").write_text("{not valid json", encoding="utf-8")
    broken_kb = KnowledgeBase(data_dir=tmp_path)
    with pytest.raises(KnowledgeBaseValidationError, match="Failed to read/parse"):
        broken_kb.load_all()


def test_rejects_category_mismatch() -> None:
    kb = _load_real_kb()
    wf = copy.deepcopy(kb.get_workflow("NET-001"))
    payload = {"schema_version": "1.0", "category": "hardware", "workflows": [wf]}
    with pytest.raises(KnowledgeBaseValidationError, match="does not match file category"):
        validate_workflow_file(payload)
