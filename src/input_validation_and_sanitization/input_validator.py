"""
Robust input‐validation helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

• Email / phone / URL validation
• XSS and SQL-i detection
• Secure filename sanitisation
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import bleach

_LOG = logging.getLogger("security.input_validator")


# ---------------------------------------------------------------------- #
# Regex patterns                                                         #
# ---------------------------------------------------------------------- #
EMAIL_REGEX = re.compile(
    r"""^[A-Za-z0-9._%+-]+      # local part
        @                       # at
        [A-Za-z0-9.-]+?         # domain
        \.[A-Za-z]{2,}$         # TLD
    """,
    re.VERBOSE,
)

PHONE_REGEX = re.compile(
    r"""^\+?1?                  # optional country code
        [-.\s]?                 # optional separator
        (\d{3})                 # area code
        [-.\s]?                 # sep
        (\d{3})                 # prefix
        [-.\s]?                 # sep
        (\d{4})$                # line number
    """,
    re.VERBOSE,
)

URL_REGEX = re.compile(
    r"""^https?://                       # scheme
        (?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,} # hostname
        (?:\:\d+)?                       # optional port
        (?:/.*)?$                        # optional path / query
    """,
    re.VERBOSE | re.IGNORECASE,
)


SQL_INJECTION_PATTERNS = [
    r"(\bOR\b|\bAND\b).+?=",        # boolean OR/AND trick
    r"(--|#|/\*).*?$",              # comment sequence
    r";\s*(DROP|SELECT|INSERT|DELETE|UPDATE|CREATE|ALTER|EXEC)\b",
]

XSS_PATTERNS = [
    r"<script\b[^>]*>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"<iframe\b[^>]*>.*?</iframe>",
]


# ---------------------------------------------------------------------- #
# Public API                                                             #
# ---------------------------------------------------------------------- #
class InputValidator:
    """Collection of static validation utilities"""

    # -------------------------- basic types --------------------------- #
    @staticmethod
    def email(value: str) -> bool:
        out = bool(EMAIL_REGEX.match(value))
        _LOG.debug("email %s → %s", value, out)
        return out

    @staticmethod
    def phone(value: str) -> bool:
        out = bool(PHONE_REGEX.match(value))
        _LOG.debug("phone %s → %s", value, out)
        return out

    @staticmethod
    def url(value: str) -> bool:
        out = bool(URL_REGEX.match(value))
        _LOG.debug("url %s → %s", value, out)
        return out

    # -------------------------- security scans ------------------------ #
    @staticmethod
    def has_sql_injection(text: str) -> bool:
        for pat in SQL_INJECTION_PATTERNS:
            if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
                _LOG.warning("possible SQL-i found in %s by %s", text, pat)
                return True
        return False

    @staticmethod
    def has_xss(text: str) -> bool:
        for pat in XSS_PATTERNS:
            if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
                _LOG.warning("possible XSS found in %s by %s", text, pat)
                return True
        return False

    # -------------------------- helpers ------------------------------- #
    @staticmethod
    def sanitise_html(text: str, allowed: List[str] | None = None) -> str:
        cleaned = bleach.clean(text, tags=allowed or ["b", "i", "u", "strong", "em", "br", "p"], strip=True)
        _LOG.debug("sanitised HTML from %d→%d chars", len(text), len(cleaned))
        return cleaned

    @staticmethod
    def sanitise_filename(fname: str) -> str:
        fname = os.path.basename(fname)
        fname = re.sub(r"[^\w.\-]", "_", fname)
        if not fname or len(fname) > 255:
            fname = f"file_{datetime.utcnow():%Y%m%d_%H%M%S}"
        return fname

    @staticmethod
    def password_strength(pwd: str) -> Dict[str, bool]:
        checks = {
            "length": len(pwd) >= 12,
            "upper": bool(re.search(r"[A-Z]", pwd)),
            "lower": bool(re.search(r"[a-z]", pwd)),
            "digit": bool(re.search(r"\d", pwd)),
            "special": bool(re.search(r"[^\w]", pwd)),
        }
        _LOG.debug("password strength → %s/%s passed", sum(checks.values()), len(checks))
        return checks


# ---------------------------------------------------------------------- #
# Quick self-test                                                        #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")

    samples = {
        "email": ["user@example.com", "fail@bad", "weird@@foo.bar"],
        "phone": ["+1 212-555-1234", "123-456-7890", "bad-phone"],
        "url": ["https://aws.amazon.com", "ftp://bad", "http://foo"],
    }

    for typ, vals in samples.items():
        for v in vals:
            ok = getattr(InputValidator, typ)(v)
            print(f"{typ:<5} {v:<30} → {'✓' if ok else '✗'}")

    # SQL/XSS demo
    bad_sql = "admin' OR 1=1 --"
    bad_xss = "<script>alert(1)</script>"
    print("SQL-i?", InputValidator.has_sql_injection(bad_sql))
    print("XSS?", InputValidator.has_xss(bad_xss))
