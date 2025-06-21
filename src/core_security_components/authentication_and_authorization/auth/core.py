"""
Reusable authentication / authorization utilities
-------------------------------------------------
 • Stateless JWT tokens (HS-256)
 • BCrypt password hashing & verification
 • Role-based decorator for Flask / FastAPI / etc.
"""

from __future__ import annotations

import datetime as _dt
import os
import secrets
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Iterable, Mapping, MutableMapping
import bcrypt
import jwt
from flask import Request, jsonify

from dotenv import load_dotenv
load_dotenv()               # grabs variables from .env before anything else
class AuthError(Exception):
    """Base authentication / authorization error."""


class TokenExpired(AuthError):
    pass


class TokenInvalid(AuthError):
    pass


@dataclass(slots=True)
class SecureAuth:
    secret_key: str
    token_expiration_hours: int = 24
    algorithm: str = "HS256"
    _now: Callable[[], _dt.datetime] = field(default=_dt.datetime.utcnow, repr=False)

    # ------------------------------------------------------------------ #
    # Password helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def hash_password(password: str) -> bytes:
        """Return a salted bcrypt hash of *password*."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    @staticmethod
    def verify_password(password: str, hashed: bytes) -> bool:
        """True if *password* matches a previously-hashed value."""
        return bcrypt.checkpw(password.encode(), hashed)

    # ------------------------------------------------------------------ #
    # JWT helpers
    # ------------------------------------------------------------------ #
    def _base_claims(self) -> dict[str, Any]:
        now = self._now()
        return {
            "iat": now,
            "exp": now + _dt.timedelta(hours=self.token_expiration_hours),
            "jti": secrets.token_hex(16),
        }

    def generate_token(self, user_id: str | int, *, roles: Iterable[str] | None = None,
                       extra: Mapping[str, Any] | None = None) -> str:
        """Return a signed JWT for *user_id*."""
        payload: dict[str, Any] = {
            **self._base_claims(),
            "user_id": user_id,
            "roles": list(roles or []),
        }
        if extra:
            payload.update(extra)
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> MutableMapping[str, Any]:
        """Decode *token* or raise a specific AuthError."""
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise TokenExpired("token expired") from exc
        except jwt.PyJWTError as exc:
            raise TokenInvalid("token invalid") from exc

    # ------------------------------------------------------------------ #
    # Flask decorator
    # ------------------------------------------------------------------ #
    def require_auth(self, *, roles: Iterable[str] | None = None) -> Callable:
        """@app.route decorator enforcing valid token & (optionally) role(s)."""
        wanted_roles = set(roles or [])

        def decorator(view: Callable):
            @wraps(view)
            def wrapper(*args, **kwargs):                           # type: ignore[override]
                from flask import request  # local import to keep the core library agnostic

                token = (request.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
                if not token:
                    return jsonify(error="missing token"), 401
                try:
                    claims = self.verify_token(token)
                except TokenExpired:
                    return jsonify(error="token expired"), 401
                except TokenInvalid:
                    return jsonify(error="invalid token"), 401

                if wanted_roles and not wanted_roles.intersection(claims.get("roles", [])):
                    return jsonify(error="insufficient permissions"), 403

                # attach user info to the request context
                request.claims = claims                                        # type: ignore[attr-defined]
                return view(*args, **kwargs)

            return wrapper

        return decorator


# ---------------------------------------------------------------------- #
# Factory helper – safe default for SECRET_KEY
# ---------------------------------------------------------------------- #
def auth_from_env() -> SecureAuth:
    secret = os.getenv("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY environment variable is required")
    return SecureAuth(secret_key=secret)
