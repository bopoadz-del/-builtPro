"""Content scanning utilities for PDP."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import re

from .schemas import Severity


PROHIBITED_PATTERNS: Dict[str, List[str]] = {
    "pii": [
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b",
        r"[\w\.-]+@[\w\.-]+",
        r"\b\d{3}[- ]\d{3}[- ]\d{4}\b",
    ],
    "sql_injection": [
        r"\bunion\s+select\b",
        r"\bdrop\s+table\b",
        r"--",
        r";\s*drop\b",
    ],
    "xss": [
        r"<\s*script",
        r"onerror\s*=",
        r"javascript:",
        r"<\s*iframe",
    ],
    "command_injection": [
        r";\s*rm\s+-rf",
        r"\|\s*rm\s+-rf",
        r"`.+?`",
        r";\s*wget\b",
    ],
}


@dataclass
class ScanResult:
    safe: bool
    violations: List[str] = field(default_factory=list)
    severity: Severity = Severity.LOW
    sanitized_text: str | None = None
    details: Dict[str, List[str]] = field(default_factory=dict)


class ContentScanner:
    def __init__(self, db_session) -> None:
        self.db_session = db_session
        self.patterns = PROHIBITED_PATTERNS

    def scan(self, text: str) -> ScanResult:
        if not text:
            return ScanResult(safe=True, violations=[], severity=Severity.LOW)

        violations: List[str] = []
        details: Dict[str, List[str]] = {}

        pii = self.check_pii(text)
        if pii:
            violations.extend(pii)
            details["pii"] = pii

        sql = self.check_injection(text, "sql_injection")
        if sql:
            violations.extend(sql)
            details["sql_injection"] = sql

        xss = self.check_injection(text, "xss")
        if xss:
            violations.extend(xss)
            details["xss"] = xss

        cmd = self.check_injection(text, "command_injection")
        if cmd:
            violations.extend(cmd)
            details["command_injection"] = cmd

        malicious = self.check_malicious(text)
        if malicious:
            violations.extend(malicious)
            details["malicious"] = malicious

        severity = self._severity_from_violations(details)
        safe = not violations
        sanitized = None
        if not safe:
            sanitized = self._sanitize(text)

        return ScanResult(
            safe=safe,
            violations=violations,
            severity=severity,
            sanitized_text=sanitized,
            details=details,
        )

    def check_pii(self, text: str) -> List[str]:
        violations: List[str] = []
        patterns = self.patterns.get("pii", [])
        if patterns:
            if re.search(patterns[0], text, re.IGNORECASE):
                violations.append("PII SSN detected")
            if re.search(patterns[1], text, re.IGNORECASE):
                violations.append("PII credit card detected")
            if re.search(patterns[2], text, re.IGNORECASE):
                violations.append("PII email detected")
            if re.search(patterns[3], text, re.IGNORECASE):
                violations.append("PII phone detected")
        return violations

    def check_injection(self, text: str, pattern_key: str) -> List[str]:
        violations: List[str] = []
        for pattern in self.patterns.get(pattern_key, []):
            if re.search(pattern, text, re.IGNORECASE):
                if pattern_key == "command_injection":
                    violations.append("Command injection detected")
                elif pattern_key == "xss":
                    violations.append("XSS detected")
                elif pattern_key == "sql_injection":
                    violations.append("SQL injection detected")
                else:
                    label = pattern_key.upper().replace("_", " ")
                    violations.append(f"{label} detected")
                break
        return violations

    def check_malicious(self, text: str) -> List[str]:
        violations: List[str] = []
        special_chars = re.findall(r"[^\w\s]", text)
        if len(special_chars) > 40:
            violations.append("excessive_special_chars")
        if "\x00" in text:
            violations.append("null_bytes")
        if text.count("%") > 10:
            violations.append("excessive_url_encoding")
        if re.match(r"^[A-Za-z0-9+/=]{40,}$", text.strip()):
            violations.append("base64_payload")
        return violations

    def _sanitize(self, text: str) -> str:
        sanitized = re.sub(r"<\s*script.*?>.*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r"on\w+\s*=\s*['\"].*?['\"]", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"<\s*iframe.*?>.*?<\s*/\s*iframe\s*>", "", sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = sanitized.replace("--", "")
        sanitized = sanitized.replace("\x00", "")
        return sanitized

    def _severity_from_violations(self, details: Dict[str, List[str]]) -> Severity:
        if "command_injection" in details:
            return Severity.CRITICAL
        if "sql_injection" in details or "xss" in details:
            return Severity.HIGH
        if "pii" in details:
            return Severity.MEDIUM
        if "malicious" in details:
            return Severity.MEDIUM
        return Severity.LOW
