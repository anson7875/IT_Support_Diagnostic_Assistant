"""Deterministic bilingual (English + Traditional Chinese) keyword extractor.

Extracts structured technical signals (OS, device type, category keywords,
error codes, and safety red-flag terms) from natural-language IT incident
descriptions without relying on external AI APIs.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

# Category keyword rules: (display_token, regex_pattern)
CATEGORY_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "network": [
        ("internet", r"\binternet\b"),
        ("wi-fi", r"\bwi-?fi\b"),
        ("ethernet", r"\bethernet\b"),
        ("network", r"\bnetwork(?:ing)?\b"),
        ("dns", r"\bdns\b"),
        ("dhcp", r"\bdhcp\b"),
        ("apipa", r"\bapipa\b|169\.254\.\d{1,3}\.\d{1,3}"),
        ("ip address", r"\bip\s*(?:address|config)?\b"),
        ("ping", r"\bping\b"),
        ("gateway", r"\bgateway\b"),
        ("router", r"\brouter\b"),
        ("offline", r"\boffline\b"),
        ("no connection", r"\bno\s+(?:internet|connection|network)\b"),
        ("無法上網", r"無法上網|上不到網|上唔到網|不能上網|連不到網|連唔到網|斷網"),
        ("網路/網絡", r"網路|網絡|寬頻|路由器"),
    ],
    "hardware": [
        ("power on", r"\b(?:won'?t|not|no|cannot|can'?t)\s+(?:power|turn)\s+on\b|\bno\s+power\b"),
        ("no display", r"\bno\s+(?:display|signal|video)\b|\bblack\s+screen\b|\bblank\s+screen\b"),
        ("post", r"\bpost\b|\bbeep\s*codes?\b"),
        ("monitor", r"\bmonitor\b|\bhdmi\b|\bdisplayport\b"),
        ("psu", r"\bpsu\b|\bpower\s+supply\b|\bcharger\b"),
        ("motherboard", r"\bmotherboard\b|\bgpu\b|\bfans?\s+spin"),
        ("battery", r"\bbattery\b"),
        ("無法開機", r"無法開機|開不到機|開唔到機|不能開機|沒反應|冇反應"),
        ("無畫面", r"無畫面|沒有畫面|冇畫面|黑屏|黑畫面|螢幕沒訊號|熒幕冇訊號"),
        ("電源/硬體", r"電源|火牛|充電器|風扇|主機板|顯卡|電池"),
    ],
    "os": [
        ("slow", r"\bslow(?:down|ness)?\b|\bsluggish\b|\blag(?:ging|gy)?\b|\bfreez(?:e|ing|es)\b"),
        ("high cpu", r"\bhigh\s+cpu\b|\bcpu\s*(?:100%|spike|usage|high)\b"),
        ("high memory", r"\b(?:high\s+)?(?:memory|ram)\s*(?:usage|full|leak|pressure)?\b|\bswap\b"),
        ("disk usage", r"\bdisk\s*(?:100%|full|space|usage|i/o)\b|\bstorage\s+full\b"),
        ("bsod", r"\bbsod\b|\bblue\s+screen\b|\bkernel\s+panic\b"),
        ("task manager", r"\btask\s+manager\b|\bactivity\s+monitor\b|\bjournalctl\b|\bevent\s+viewer\b"),
        ("performance", r"\bperformance\b|\bunresponsive\b|\bcrash(?:ing|ed)?\b"),
        ("系統卡頓", r"卡頓|好慢|很慢|變慢|當機|死機|藍屏|空間不足|記憶體不足|磁碟\s*100%"),
    ],
}

OS_PATTERNS: dict[str, str] = {
    "windows": r"\bwindows\b|\bwin\s*(?:10|11)\b|\bpowershell\b|\bipconfig\b",
    "linux": r"\blinux\b|\bubuntu\b|\bdebian\b|\bfedora\b|\bcentos\b|\bred\s*hat\b|\barch\b|\bjournalctl\b",
    "macos": r"\bmac\s*os\b|\bmacbook\b|\bimac\b|\bmac\s+mini\b|\bmac\s+studio\b|\bmac\b|蘋果電腦",
}

DEVICE_PATTERNS: dict[str, str] = {
    "laptop": r"\blaptop\b|\bnotebook\b|\bmacbook\b|筆電|手提電腦|筆記型電腦",
    "desktop": r"\bdesktop\b|\bpc\b|\btower\b|\bworkstation\b|\bimac\b|桌機|桌上型|台式機",
    "server": r"\bserver\b|伺服器|服務器",
}

SAFETY_PATTERNS: list[tuple[str, str]] = [
    ("smoke", r"\bsmoke\b|\bsmoking\b|冒煙"),
    ("burning smell", r"\bburn(?:ing|t)\s+smell\b|燒焦味|燶味"),
    ("swollen battery", r"\bswollen\s+battery\b|\bbulging\s+battery\b|電池膨脹|電池發脹|電池鼓包"),
    ("sparks / electrical damage", r"\bsparks?\b|\belectrical\s+damage\b|火花|漏電"),
    ("liquid spill", r"\bliquid\s+spill\b|\bspilled\s+water\b|進水|倒水|入水"),
]

ERROR_CODE_PATTERN = re.compile(
    r"\b(?:0x[0-9A-Fa-f]{4,8}|ERR_[A-Z0-9_]+|STOP\s+CODE[:\s]+[A-Z0-9_]+|169\.254\.\d{1,3}\.\d{1,3})\b"
)


@dataclass(frozen=True)
class ExtractedIncidentInfo:
    """Structured technical information extracted from an incident description."""

    raw_description: str
    detected_os: str | None
    device_type: str | None
    matched_keywords: dict[str, list[str]] = field(default_factory=dict)
    safety_keywords_detected: list[str] = field(default_factory=list)
    error_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize extracted information into a plain dictionary."""
        return asdict(self)


def extract_incident_info(description: str) -> ExtractedIncidentInfo:
    """Deterministically extract OS, device, symptom keywords, errors, and safety triggers."""
    text = (description or "").strip()
    if not text:
        return ExtractedIncidentInfo(
            raw_description="",
            detected_os=None,
            device_type=None,
            matched_keywords={"hardware": [], "os": [], "network": []},
            safety_keywords_detected=[],
            error_codes=[],
        )

    detected_os: str | None = None
    for os_name, pattern in OS_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            detected_os = os_name
            break

    device_type: str | None = None
    for dev_name, pattern in DEVICE_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            device_type = dev_name
            break

    matched_keywords: dict[str, list[str]] = {}
    for category, rules in CATEGORY_PATTERNS.items():
        hits: list[str] = []
        for label, pattern in rules:
            if re.search(pattern, text, re.IGNORECASE):
                hits.append(label)
        matched_keywords[category] = hits

    safety_hits: list[str] = [
        label
        for label, pattern in SAFETY_PATTERNS
        if re.search(pattern, text, re.IGNORECASE)
    ]

    error_codes = sorted(set(ERROR_CODE_PATTERN.findall(text)))

    return ExtractedIncidentInfo(
        raw_description=text,
        detected_os=detected_os,
        device_type=device_type,
        matched_keywords=matched_keywords,
        safety_keywords_detected=safety_hits,
        error_codes=error_codes,
    )
