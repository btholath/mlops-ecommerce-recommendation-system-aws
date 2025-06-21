"""
Very small Flask app demonstrating SecureAuth usage.
"""
# ── web/app.py ────────────────────────────────────────────────────────────
import sys
from pathlib import Path

# 1.  <web/>               ← this file’s directory
# 2.  ..                   ← authentication_and_authorization/
# 3.  append(..) to sys.path so that `import auth.core` works
sys.path.append(str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()               # grabs variables from .env before anything else

from flask import Flask, jsonify, request
from auth.core import auth_from_env

app = Flask(__name__)
auth = auth_from_env()


# ---------------------------------------------------------------------- #
# Dummy in-memory user store (replace with real DB/ORM)
USERS = {"admin": auth.hash_password("secure_password")}
# ---------------------------------------------------------------------- #


@app.route("/login", methods=["POST"])
def login() -> tuple[dict, int]:
    username = request.json.get("username")
    password = request.json.get("password")

    stored_hash = USERS.get(username)
    if not stored_hash or not auth.verify_password(password, stored_hash):
        return {"error": "invalid credentials"}, 401

    token = auth.generate_token(user_id=username, roles=["admin" if username == "admin" else "user"])
    return {"access_token": token, "expires_in": auth.token_expiration_hours * 3600}, 200


@app.route("/protected")
@auth.require_auth()
def protected() -> dict:
    return {"message": "success", "claims": request.claims}      # type: ignore[attr-defined]


@app.route("/admin")
@auth.require_auth(roles=["admin"])
def admin() -> dict:
    return {"message": "admin endpoint reached"}

@app.route("/", methods=["GET"])
def index():
    """
    Lightweight health check / landing page.
    Returns 200 OK so load balancers and humans both know the service is up.
    """
    return jsonify(
        status="ok",
        message="Secure-Auth API – see /login to get a token."
    ), 200


if __name__ == "__main__":
    # export SECRET_KEY before running!  e.g.:
    # $ export SECRET_KEY=$(openssl rand -hex 32)
    app.run(debug=True, port=5000)
