"""Unit tests for bilingual keyword extraction and rule-based incident classification."""

from __future__ import annotations

from app.diagnostic.classifier import classify_incident
from app.diagnostic.keyword_extractor import extract_incident_info


def test_extract_and_classify_english_network_macos() -> None:
    res = classify_incident("My MacBook is connected to Wi-Fi but has no internet and shows 169.254.12.5")
    assert res.category == "network"
    assert res.recommended_workflow_id == "NET-001"
    assert res.confidence == "high"
    assert res.extracted_info.detected_os == "macos"
    assert res.extracted_info.device_type == "laptop"
    assert "169.254.12.5" in res.extracted_info.error_codes
    assert res.missing_information == []


def test_extract_and_classify_chinese_network_issue() -> None:
    res = classify_incident("我的電腦連上Wi-Fi但無法上網，懷疑是網絡問題")
    assert res.category == "network"
    assert res.recommended_workflow_id == "NET-001"
    assert "target_os" in res.missing_information  # OS was not mentioned


def test_extract_and_classify_hardware_no_power_with_safety_flag() -> None:
    res = classify_incident("My desktop PC won't power on and there is a burning smell from the PSU")
    assert res.category == "hardware"
    assert res.recommended_workflow_id == "HW-001"
    assert res.safety_warning is not None
    assert "burning smell" in res.extracted_info.safety_keywords_detected


def test_extract_and_classify_chinese_hardware_swollen_battery() -> None:
    res = classify_incident("手提電腦開唔到機，而且見到電池膨脹")
    assert res.category == "hardware"
    assert res.recommended_workflow_id == "HW-001"
    assert res.extracted_info.device_type == "laptop"
    assert res.safety_warning is not None
    assert "swollen battery" in res.extracted_info.safety_keywords_detected


def test_extract_and_classify_linux_os_performance() -> None:
    res = classify_incident("Ubuntu Linux server is extremely slow with high CPU and memory usage")
    assert res.category == "os"
    assert res.recommended_workflow_id == "OS-001"
    assert res.confidence == "high"
    assert res.extracted_info.detected_os == "linux"
    assert res.extracted_info.device_type == "server"


def test_does_not_force_classification_on_unsupported_input() -> None:
    res = classify_incident("I need help resetting my Microsoft 365 Outlook email signature")
    assert res.category is None
    assert res.recommended_workflow_id is None
    assert res.confidence == "unsupported"


def test_does_not_force_classification_on_ambiguous_tie() -> None:
    # 1 network keyword ("wifi") vs 1 os keyword ("slow") -> tie -> ambiguous
    res = classify_incident("wifi slow")
    assert res.category is None
    assert res.recommended_workflow_id is None
    assert res.confidence == "ambiguous"


def test_empty_description_handled_safely() -> None:
    info = extract_incident_info("   ")
    assert info.detected_os is None
    res = classify_incident("")
    assert res.category is None
    assert res.confidence == "unsupported"
