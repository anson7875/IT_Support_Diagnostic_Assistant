"""Unit tests for the deterministic cross-OS command output parser."""

from __future__ import annotations

import pytest

from app.diagnostic.output_parser import (
    parse_command_output,
    parse_ip_config,
    parse_ping,
)


def test_parse_windows_ipconfig_valid() -> None:
    sample = """
    Wireless LAN adapter Wi-Fi:
       IPv4 Address. . . . . . . . . . . : 192.168.1.42(Preferred)
       Subnet Mask . . . . . . . . . . . : 255.255.255.0
       Default Gateway . . . . . . . . . : 192.168.1.1
    """
    result = parse_ip_config(sample, target_os="windows")
    assert result.suggested_result_code == "normal"
    assert result.suggested_outcome_id == "valid_ip_and_gateway"
    assert result.extracted_metrics["ipv4_addresses"] == ["192.168.1.42"]
    assert result.extracted_metrics["default_gateway"] == "192.168.1.1"
    assert result.extracted_metrics["has_apipa"] is False


def test_parse_windows_ipconfig_apipa() -> None:
    sample = """
    Ethernet adapter Ethernet:
       Autoconfiguration IPv4 Address. . : 169.254.88.12(Preferred)
       Subnet Mask . . . . . . . . . . . : 255.255.0.0
       Default Gateway . . . . . . . . . :
    """
    result = parse_ip_config(sample, target_os="windows")
    assert result.suggested_result_code == "abnormal"
    assert result.suggested_outcome_id == "apipa_or_no_ip"
    assert result.extracted_metrics["has_apipa"] is True


def test_parse_windows_ipconfig_media_disconnected() -> None:
    sample = """
    Ethernet adapter Ethernet:
       Media State . . . . . . . . . . . : Media disconnected
    """
    result = parse_ip_config(sample, target_os="windows")
    assert result.suggested_result_code == "abnormal"
    assert result.suggested_outcome_id == "interface_down"
    assert result.extracted_metrics["interface_down_detected"] is True


def test_parse_linux_ip_a_and_route_valid() -> None:
    sample = """
    1: lo: <LOOPBACK,UP,LOWER_UP>
        inet 127.0.0.1/8 scope host lo
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
        inet 10.0.0.15/24 brd 10.0.0.255 scope global dynamic eth0
    default via 10.0.0.1 dev eth0 proto dhcp
    """
    result = parse_ip_config(sample, target_os="linux")
    assert result.suggested_result_code == "normal"
    assert result.suggested_outcome_id == "valid_ip_and_gateway"
    assert result.extracted_metrics["ipv4_addresses"] == ["10.0.0.15"]
    assert result.extracted_metrics["default_gateway"] == "10.0.0.1"


def test_parse_macos_ifconfig_apipa() -> None:
    sample = """
    en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        inet 169.254.42.18 netmask 0xffff0000 broadcast 169.254.255.255
        status: active
    """
    result = parse_ip_config(sample, target_os="macos")
    assert result.suggested_result_code == "abnormal"
    assert result.suggested_outcome_id == "apipa_or_no_ip"
    assert result.extracted_metrics["has_apipa"] is True


def test_parse_macos_ifconfig_inactive() -> None:
    sample = """
    en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500
        status: inactive
    """
    result = parse_ip_config(sample, target_os="macos")
    assert result.suggested_result_code == "abnormal"
    assert result.suggested_outcome_id == "interface_down"


def test_parse_windows_ping_success() -> None:
    sample = """
    Pinging 8.8.8.8 with 32 bytes of data:
    Reply from 8.8.8.8: bytes=32 time=11ms TTL=118
    Ping statistics for 8.8.8.8:
        Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
    Approximate round trip times in milli-seconds:
        Minimum = 10ms, Maximum = 14ms, Average = 12ms
    """
    result = parse_ping(sample, target_os="windows")
    assert result.suggested_result_code == "normal"
    assert result.extracted_metrics["transmitted"] == 4
    assert result.extracted_metrics["received"] == 4
    assert result.extracted_metrics["packet_loss_pct"] == 0.0
    assert result.extracted_metrics["avg_latency_ms"] == 12.0


def test_parse_linux_ping_success() -> None:
    sample = """
    --- 192.168.1.1 ping statistics ---
    4 packets transmitted, 4 received, 0% packet loss, time 3005ms
    rtt min/avg/max/mdev = 1.120/2.340/3.500/0.410 ms
    """
    result = parse_ping(sample, target_os="linux")
    assert result.suggested_result_code == "normal"
    assert result.extracted_metrics["packet_loss_pct"] == 0.0
    assert result.extracted_metrics["avg_latency_ms"] == 2.34


def test_parse_macos_ping_failure() -> None:
    sample = """
    Request timeout for icmp_seq 0
    --- 8.8.8.8 ping statistics ---
    4 packets transmitted, 0 packets received, 100.0% packet loss
    """
    result = parse_ping(sample, target_os="macos")
    assert result.suggested_result_code == "abnormal"
    assert result.extracted_metrics["packet_loss_pct"] == 100.0
    assert result.extracted_metrics["received"] == 0


def test_parse_inconclusive_on_empty_or_garbage_input() -> None:
    assert parse_ip_config("", target_os="windows").suggested_result_code == "inconclusive"
    assert parse_ping("random text without stats", target_os="linux").suggested_result_code == "inconclusive"


def test_dispatcher_routes_and_rejects_unknown_key() -> None:
    res = parse_command_output("ping", "Request timed out.", target_os="windows")
    assert res.suggested_result_code == "abnormal"
    with pytest.raises(ValueError, match="Unsupported parser_key"):
        parse_command_output("unknown_cmd", "hello")
