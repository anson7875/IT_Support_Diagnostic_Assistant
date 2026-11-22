"""Lightweight deterministic command output parser.

Parses pasted terminal outputs for selected common cross-OS networking
commands (Windows, Linux, macOS) using regular expressions to extract
structured evidence and suggest normalized diagnostic results without
relying on external AI APIs.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

IPV4_PATTERN = r"(?:\d{1,3}\.){3}\d{1,3}"


@dataclass(frozen=True)
class ParsedCommandResult:
    """Structured result returned by deterministic command output parsers."""

    parser_key: str
    target_os: str
    suggested_result_code: str
    suggested_outcome_id: str | None
    extracted_metrics: dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the parsed result into a plain dictionary."""
        return asdict(self)


def _is_valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def _is_apipa(ip: str) -> bool:
    return ip.startswith("169.254.")


def parse_ip_config(
    raw_output: str, target_os: str = "windows"
) -> ParsedCommandResult:
    """Parse IP configuration output from Windows ``ipconfig``, Linux ``ip a``/``ip r``, or macOS ``ifconfig``/``route``.

    Extracts non-loopback IPv4 addresses, APIPA flags, default gateway, and
    interface-down indicators to suggest a normalized test result.
    """
    os_key = target_os.lower()
    text = (raw_output or "").strip()
    if not text:
        return ParsedCommandResult(
            parser_key="ip_config",
            target_os=os_key,
            suggested_result_code="inconclusive",
            suggested_outcome_id=None,
            extracted_metrics={},
            summary="No terminal output provided to parse.",
        )

    ipv4_candidates: list[str] = []

    # Windows ipconfig format: "IPv4 Address. . . . . . . . . . . : 192.168.1.25(Preferred)"
    for match in re.finditer(
        rf"IPv4 Address[^\n:]*:\s*({IPV4_PATTERN})", text, re.IGNORECASE
    ):
        ipv4_candidates.append(match.group(1))

    # Linux/macOS format: "inet 192.168.1.25/24 ..." or "inet 192.168.1.25 netmask ..."
    for match in re.finditer(
        rf"(?<!\w)inet\s+({IPV4_PATTERN})(?:/\d+)?\b", text
    ):
        ipv4_candidates.append(match.group(1))

    # Deduplicate while preserving order and filtering loopback/invalid IPs
    ipv4_addresses: list[str] = []
    for ip in ipv4_candidates:
        if _is_valid_ipv4(ip) and not ip.startswith("127.") and ip not in ipv4_addresses:
            ipv4_addresses.append(ip)

    # Extract Default Gateway across Windows, Linux (`ip r`), and macOS (`route -n get default`)
    gateway: str | None = None
    gateway_patterns = [
        rf"Default Gateway[^\n:]*:\s*({IPV4_PATTERN})",
        rf"default\s+via\s+({IPV4_PATTERN})",
        rf"gateway:\s*({IPV4_PATTERN})",
    ]
    for pattern in gateway_patterns:
        gw_match = re.search(pattern, text, re.IGNORECASE)
        if gw_match and _is_valid_ipv4(gw_match.group(1)):
            gateway = gw_match.group(1)
            break

    has_blank_gateway_label = (
        gateway is None
        and re.search(r"Default Gateway[^\n:]*:\s*(?:\r?\n|$)", text, re.IGNORECASE)
        is not None
    )

    apipa_addresses = [ip for ip in ipv4_addresses if _is_apipa(ip)]
    non_apipa_addresses = [ip for ip in ipv4_addresses if not _is_apipa(ip)]

    interface_down = bool(
        re.search(
            r"Media disconnected|status:\s*inactive|NO-CARRIER|state\s+DOWN",
            text,
            re.IGNORECASE,
        )
    )

    metrics: dict[str, Any] = {
        "ipv4_addresses": ipv4_addresses,
        "has_apipa": bool(apipa_addresses),
        "default_gateway": gateway,
        "interface_down_detected": interface_down,
    }

    if apipa_addresses and not non_apipa_addresses:
        return ParsedCommandResult(
            parser_key="ip_config",
            target_os=os_key,
            suggested_result_code="abnormal",
            suggested_outcome_id="apipa_or_no_ip",
            extracted_metrics=metrics,
            summary=(
                f"APIPA link-local IP detected ({', '.join(apipa_addresses)}); "
                "device failed to obtain a valid DHCP lease."
            ),
        )

    if non_apipa_addresses:
        if has_blank_gateway_label:
            return ParsedCommandResult(
                parser_key="ip_config",
                target_os=os_key,
                suggested_result_code="abnormal",
                suggested_outcome_id="apipa_or_no_ip",
                extracted_metrics=metrics,
                summary=(
                    f"IPv4 address found ({non_apipa_addresses[0]}), "
                    "but Default Gateway is blank."
                ),
            )
        gw_note = (
            f"Default Gateway: {gateway}"
            if gateway
            else "Default Gateway not present in pasted snippet"
        )
        return ParsedCommandResult(
            parser_key="ip_config",
            target_os=os_key,
            suggested_result_code="normal",
            suggested_outcome_id="valid_ip_and_gateway",
            extracted_metrics=metrics,
            summary=f"Valid IPv4 detected ({non_apipa_addresses[0]}). {gw_note}.",
        )

    if interface_down:
        return ParsedCommandResult(
            parser_key="ip_config",
            target_os=os_key,
            suggested_result_code="abnormal",
            suggested_outcome_id="interface_down",
            extracted_metrics=metrics,
            summary="Network interface reports disconnected/inactive status with no IPv4 address.",
        )

    return ParsedCommandResult(
        parser_key="ip_config",
        target_os=os_key,
        suggested_result_code="inconclusive",
        suggested_outcome_id=None,
        extracted_metrics=metrics,
        summary="Could not reliably extract IPv4 or interface state from the pasted output.",
    )


def parse_ping(raw_output: str, target_os: str = "windows") -> ParsedCommandResult:
    """Parse ``ping`` output from Windows, Linux, or macOS.

    Extracts packets transmitted/received, packet loss percentage, and average
    round-trip latency to suggest whether connectivity succeeded or failed.
    """
    os_key = target_os.lower()
    text = (raw_output or "").strip()
    if not text:
        return ParsedCommandResult(
            parser_key="ping",
            target_os=os_key,
            suggested_result_code="inconclusive",
            suggested_outcome_id=None,
            extracted_metrics={},
            summary="No ping output provided to parse.",
        )

    transmitted: int | None = None
    received: int | None = None
    packet_loss_pct: float | None = None
    avg_latency_ms: float | None = None

    # Windows: "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
    win_pkt = re.search(
        r"Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*\d+\s*\((\d+(?:\.\d+)?)%\s*loss\)",
        text,
        re.IGNORECASE,
    )
    if win_pkt:
        transmitted = int(win_pkt.group(1))
        received = int(win_pkt.group(2))
        packet_loss_pct = float(win_pkt.group(3))

    # Linux / macOS:
    # "4 packets transmitted, 4 received, 0% packet loss"
    # "4 packets transmitted, 4 packets received, 0.0% packet loss"
    unix_pkt = re.search(
        r"(\d+)\s+packets\s+transmitted,\s*(\d+)\s+(?:packets\s+)?received,\s*(\d+(?:\.\d+)?)%\s+packet\s+loss",
        text,
        re.IGNORECASE,
    )
    if unix_pkt and packet_loss_pct is None:
        transmitted = int(unix_pkt.group(1))
        received = int(unix_pkt.group(2))
        packet_loss_pct = float(unix_pkt.group(3))

    # Windows latency: "Average = 12ms"
    win_avg = re.search(r"Average\s*=\s*(\d+(?:\.\d+)?)\s*ms", text, re.IGNORECASE)
    if win_avg:
        avg_latency_ms = float(win_avg.group(1))

    # Linux / macOS latency:
    # "rtt min/avg/max/mdev = 1.123/2.456/3.789/0.500 ms"
    # "round-trip min/avg/max/stddev = 1.234/2.345/3.456/0.400 ms"
    unix_avg = re.search(
        r"min/avg/max/(?:mdev|stddev)\s*=\s*\d+(?:\.\d+)?/(\d+(?:\.\d+)?)/",
        text,
        re.IGNORECASE,
    )
    if unix_avg and avg_latency_ms is None:
        avg_latency_ms = float(unix_avg.group(1))

    failure_indicator = bool(
        re.search(
            r"Request timed out|Destination host unreachable|100(?:\.0)?%\s*(?:packet\s+)?loss|"
            r"could not find host|Name or service not known|cannot resolve|General failure",
            text,
            re.IGNORECASE,
        )
    )

    metrics: dict[str, Any] = {
        "transmitted": transmitted,
        "received": received,
        "packet_loss_pct": packet_loss_pct,
        "avg_latency_ms": avg_latency_ms,
    }

    if packet_loss_pct is not None:
        if packet_loss_pct == 0.0:
            latency_str = (
                f", avg latency {avg_latency_ms} ms"
                if avg_latency_ms is not None
                else ""
            )
            return ParsedCommandResult(
                parser_key="ping",
                target_os=os_key,
                suggested_result_code="normal",
                suggested_outcome_id=None,
                extracted_metrics=metrics,
                summary=f"Ping succeeded: {received}/{transmitted} received (0% loss{latency_str}).",
            )
        if packet_loss_pct >= 100.0 or received == 0:
            return ParsedCommandResult(
                parser_key="ping",
                target_os=os_key,
                suggested_result_code="abnormal",
                suggested_outcome_id=None,
                extracted_metrics=metrics,
                summary=f"Ping failed: 100% packet loss ({received}/{transmitted} received).",
            )
        return ParsedCommandResult(
            parser_key="ping",
            target_os=os_key,
            suggested_result_code="abnormal",
            suggested_outcome_id=None,
            extracted_metrics=metrics,
            summary=(
                f"Partial packet loss detected: {packet_loss_pct}% loss "
                f"({received}/{transmitted} received)."
            ),
        )

    if failure_indicator:
        return ParsedCommandResult(
            parser_key="ping",
            target_os=os_key,
            suggested_result_code="abnormal",
            suggested_outcome_id=None,
            extracted_metrics=metrics,
            summary="Ping failure indicator detected (timeout, unreachable host, or resolution error).",
        )

    return ParsedCommandResult(
        parser_key="ping",
        target_os=os_key,
        suggested_result_code="inconclusive",
        suggested_outcome_id=None,
        extracted_metrics=metrics,
        summary="Could not extract ping packet statistics from the pasted output.",
    )


def parse_command_output(
    parser_key: str, raw_output: str, target_os: str = "windows"
) -> ParsedCommandResult:
    """Dispatch raw terminal output to the appropriate deterministic parser."""
    if parser_key == "ip_config":
        return parse_ip_config(raw_output, target_os=target_os)
    if parser_key == "ping":
        return parse_ping(raw_output, target_os=target_os)
    raise ValueError(f"Unsupported parser_key '{parser_key}'.")
