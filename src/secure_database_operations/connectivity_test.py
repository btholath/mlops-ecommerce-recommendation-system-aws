#!/usr/bin/env python3
"""
Quick Postgres smoke-test for Codespaces.
Run it with:  python test_db.py
"""

import os
import sys
import psycopg2
from psycopg2 import sql

# ---------------------------------------------------------------------------
# Connection details — override with env-vars if you like.
# Inside the Codespace the service host is simply "db"
# ---------------------------------------------------------------------------
DB_HOST = os.getenv("PGHOST", "db")
DB_PORT = os.getenv("PGPORT", "5432")
DB_NAME = os.getenv("PGDATABASE", "devdb")
DB_USER = os.getenv("PGUSER", "user")
DB_PASS = os.getenv("PGPASSWORD", "pass")

DDL = """
CREATE TABLE IF NOT EXISTS smoke_test (
    id   serial PRIMARY KEY,
    msg  text    NOT NULL
)
"""

def main() -> None:
    print(f"Connecting to postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        conn.autocommit = True
    except Exception as e:
        sys.exit(f"❌ connection failed: {e}")

    with conn, conn.cursor() as cur:
        cur.execute(DDL)
        cur.execute("TRUNCATE smoke_test")            # keep it idempotent
        cur.execute("INSERT INTO smoke_test (msg) VALUES (%s) RETURNING id", ("Hello world!",))
        inserted_id = cur.fetchone()[0]
        cur.execute(sql.SQL("SELECT msg FROM smoke_test WHERE id = %s"), [inserted_id])
        msg = cur.fetchone()[0]

    conn.close()

    if msg == "Hello world!":
        print("✅ Postgres round-trip succeeded!")
    else:
        sys.exit("❌ round-trip failed (unexpected result).")

if __name__ == "__main__":
    main()
