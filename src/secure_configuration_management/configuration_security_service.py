"""
secure_config_manager_aws.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Light-weight secret/configuration manager that supports:

* Environment variables  (default, zero dependencies)
* AWS Secrets Manager    (via boto3)

Design goals
============
* Never log secret *values* – only the lookup keys / backend used.
* Transparent in-memory caching for repeated calls.
* Helpful DEBUG logs for troubleshooting; INFO logs for high-level flow.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

_LOG = logging.getLogger("security.config")


class SecureConfigManager:
    """Retrieve application secrets from *env* or *aws_secrets*.

    Parameters
    ----------
    config_source
        ``"env"`` (default) or ``"aws_secrets"``.
    region
        AWS region (only used with Secrets Manager).
    """

    # ------------------------------------------------------------------ #
    def __init__(self, *, config_source: str = "env", region: str = "us-east-1") -> None:
        self._source = config_source.lower()
        self._cache: dict[str, str] = {}

        if self._source == "aws_secrets":
            self._aws_client = boto3.client("secretsmanager", region_name=region)

        elif self._source != "env":
            raise ValueError(f"Unsupported config_source '{config_source}'")

        _LOG.info("SecureConfigManager(%s) initialised", self._source)

    # ------------------------------------------------------------------ #
    # Public helpers                                                     #
    # ------------------------------------------------------------------ #
    def get(self, key: str, default: str | None = None) -> str | None:
        """Return the secret for *key* or *default* when missing/failed."""
        try:
            if key in self._cache:
                _LOG.debug("cache hit for key %s", key)
                return self._cache[key]

            value: Optional[str]
            if self._source == "env":
                value = os.getenv(key)
            else:  # aws_secrets
                value = self._get_from_aws(key)

            if value:
                self._cache[key] = value
            else:
                value = default
                _LOG.warning("key %s not found – using default", key)

            return value

        except Exception as exc:  # pragma: no cover
            _LOG.error("failed retrieving %s from %s: %s", key, self._source, exc)
            return default

    def validate_presence(self, required: list[str]) -> Dict[str, bool]:
        """Check that *required* keys are present & non-empty."""
        return {k: bool(self.get(k)) for k in required}

    # Handy bundles ----------------------------------------------------- #
    def database_cfg(self) -> Dict[str, str | None]:
        return {
            "host": self.get("DB_HOST", "localhost"),
            "port": self.get("DB_PORT", "5432"),
            "name": self.get("DB_NAME"),
            "user": self.get("DB_USERNAME"),
            "password": self.get("DB_PASSWORD"),
            "ssl_mode": self.get("DB_SSL_MODE", "require"),
        }

    def api_cfg(self) -> Dict[str, str | None]:
        return {
            "api_key": self.get("API_KEY"),
            "api_secret": self.get("API_SECRET"),
            "jwt_secret": self.get("JWT_SECRET"),
            "encryption_key": self.get("ENCRYPTION_KEY"),
        }

    # ------------------------------------------------------------------ #
    # Private helpers                                                    #
    # ------------------------------------------------------------------ #
    def _get_from_aws(self, key: str) -> str | None:
        try:
            response = self._aws_client.get_secret_value(SecretId=key)
            return response.get("SecretString")
        except ClientError as err:
            _LOG.warning("AWS Secrets Manager lookup failed for %s: %s", key, err.response["Error"]["Code"])
            return None


# ---------------------------------------------------------------------- #
# Static validation helpers                                              #
# ---------------------------------------------------------------------- #
class ConfigValidator:
    """Stateless helpers for password / JWT / TLS checks."""

    @staticmethod
    def password_strength(pwd: str) -> Dict[str, bool]:
        checks = {
            "length": len(pwd) >= 12,
            "upper": any(c.isupper() for c in pwd),
            "lower": any(c.islower() for c in pwd),
            "digit": any(c.isdigit() for c in pwd),
            "special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd),
        }
        _LOG.debug("password strength → %s/%s passed", sum(checks.values()), len(checks))
        return checks

    @staticmethod
    def jwt_secret_strength(secret: str) -> bool:
        strong = len(secret) >= 32 and not secret.isalnum()
        _LOG.debug("jwt secret strong? %s", strong)
        return strong


# ---------------------------------------------------------------------- #
# Example / smoke-test                                                   #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")

    mgr = SecureConfigManager(config_source="env")        # or "aws_secrets"
    present = mgr.validate_presence(["JWT_SECRET", "DB_PASSWORD"])
    _LOG.info("presence check → %s", present)

    pwd_ok = ConfigValidator.password_strength("MySecureP@ssw0rd123!")
    jwt_ok = ConfigValidator.jwt_secret_strength("super$ecret!jwt_token_value!!")
    _LOG.info("pwd all good? %s  – jwt ok? %s", all(pwd_ok.values()), jwt_ok)

    Path("src/secure_configuration_management/secure_cfg_template.json").write_text(json.dumps(mgr.database_cfg(), indent=2))
    _LOG.info("wrote demo DB config to src/secure_configuration_management/secure_cfg_template.json")
