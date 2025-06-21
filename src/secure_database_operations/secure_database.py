"""
SecureDatabase
~~~~~~~~~~~~~~

• SQL-Alchemy engine hardened for TLS, time-outs and connection-pool limits  
• Prepared-statement helpers (`execute_safe_query`)  
• Password hashing / verification (bcrypt)  
• Account-lockout & audit-log utilities  
• Rich DEBUG / INFO / ERROR logging
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, MutableMapping, Optional

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

_LOG = logging.getLogger("security.db")


class SecureDatabase:
    """Wrapper around SQL-Alchemy that enforces best-practice defaults."""

    # ------------------------------------------------------------------ #
    # Construction                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        database_url: str,
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        echo_sql: bool = False,
    ) -> None:
        self._engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=echo_sql,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 30,
                "application_name": "secure_app",
            },
        )
        self._Session = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)
        _LOG.info("Database engine initialised (pool %s, overflow %s)", pool_size, max_overflow)

    # ------------------------------------------------------------------ #
    # Session helper                                                     #
    # ------------------------------------------------------------------ #
    @contextmanager
    def _session(self):
        sess = self._Session()
        try:
            yield sess
            sess.commit()
        except Exception as exc:           # noqa: BLE001
            sess.rollback()
            _LOG.exception("DB transaction rolled back – %s", exc)
            raise
        finally:
            sess.close()

    # ------------------------------------------------------------------ #
    # Generic query                                                      #
    # ------------------------------------------------------------------ #
    def execute_safe_query(self, sql_text: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        _LOG.debug("SQL EXEC: %s | %s", sql_text.strip().splitlines()[0][:80] + "...", params)
        with self._session() as sess:
            result = sess.execute(text(sql_text), params or {})
            if result.returns_rows:
                cols = result.keys()
                rows = [dict(zip(cols, r)) for r in result.fetchall()]
                _LOG.debug(" → %d row(s) returned", len(rows))
                return rows
            return []

    # ------------------------------------------------------------------ #
    # User helpers                                                       #
    # ------------------------------------------------------------------ #
    def insert_user_secure(self, user: MutableMapping[str, Any]) -> Optional[int]:
        try:
            user = dict(user)  # shallow-copy so we can mutate locally
            user["password_hash"] = self._hash(user.pop("password"))
            q = """
            INSERT INTO users (username, email, password_hash, first_name, last_name, created_at)
            VALUES (:username, :email, :password_hash, :first_name, :last_name, NOW())
            RETURNING id
            """
            row = self.execute_safe_query(q, user)
            new_id = row[0]["id"] if row else None
            _LOG.info("User %s created (id=%s)", user["username"], new_id)
            return new_id
        except Exception:
            _LOG.exception("insert_user_secure failed")
            raise

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        q = """
        SELECT id, username, email, password_hash, failed_attempts, locked_until
        FROM users WHERE username = :username AND active = TRUE
        """
        recs = self.execute_safe_query(q, {"username": username})
        if not recs:
            _LOG.warning("login failure – unknown user %s", username)
            return None

        user = recs[0]
        if user["locked_until"] and user["locked_until"] > datetime.utcnow():
            _LOG.warning("login rejected – account locked (%s)", username)
            raise ValueError("Account locked. Try again later.")

        if self._verify(password, user["password_hash"]):
            self._reset_failed_attempts(user["id"])
            _LOG.info("login success – %s", username)
            del user["password_hash"]
            return user

        _LOG.warning("bad password for %s", username)
        self._increment_failed_attempts(user["id"])
        return None

    # ------------------------------------------------------------------ #
    # Password utils                                                     #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _hash(pwd: str) -> str:
        return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def _verify(pwd: str, hashed: str) -> bool:
        return bcrypt.checkpw(pwd.encode(), hashed.encode())

    # ------------------------------------------------------------------ #
    # Lockout helpers                                                    #
    # ------------------------------------------------------------------ #
    def _increment_failed_attempts(self, user_id: int) -> None:
        q = """
        UPDATE users SET failed_attempts = failed_attempts + 1,
            locked_until = CASE WHEN failed_attempts + 1 >= 5
                                THEN NOW() + INTERVAL '15 minutes'
                                ELSE locked_until END
        WHERE id = :uid
        """
        self.execute_safe_query(q, {"uid": user_id})

    def _reset_failed_attempts(self, user_id: int) -> None:
        self.execute_safe_query("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = :uid", {"uid": user_id})

    # ------------------------------------------------------------------ #
    # Audit log                                                          #
    # ------------------------------------------------------------------ #
    def log_security_event(
        self,
        event_type: str,
        *,
        user_id: Optional[int],
        ip: str,
        details: Dict[str, Any] | None = None,
    ) -> None:
        q = """
        INSERT INTO security_logs (event_type, user_id, ip_address, details, created_at)
        VALUES (:event, :uid, :ip, :details, NOW())
        """
        self.execute_safe_query(
            q,
            {
                "event": event_type,
                "uid": user_id,
                "ip": ip,
                "details": json.dumps(details or {}),
            },
        )
        _LOG.info("security_event %s (user=%s, ip=%s)", event_type, user_id, ip)


# ---------------------------------------------------------------------- #
# Quick demo                                                             #
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")

    DB_URL = "postgresql://username:password@localhost/secure_db"
    db = SecureDatabase(DB_URL, echo_sql=False)

    # ------------------------------------------------------------------ #
    user_info = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "StrongP@ssw0rd!",
        "first_name": "John",
        "last_name": "Doe",
    }
    try:
        uid = db.insert_user_secure(user_info)
        auth_user = db.authenticate_user("john_doe", "StrongP@ssw0rd!")
        db.log_security_event("login_success", user_id=uid, ip="192.0.2.1", details={"ua": "curl/8.0"})
    except Exception as exc:                                                 # noqa: BLE001
        _LOG.error("sample flow failed – %s", exc)
