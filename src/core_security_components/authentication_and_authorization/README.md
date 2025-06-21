

# 1. (Re)start your Flask server
```bash
export SECRET_KEY=$(openssl rand -hex 32)
python src/core_security_components/authentication_and_authorization/web/app.py
```

# 2. Obtain a token
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/login \
           -H "Content-Type: application/json" \
           -d '{"username":"admin","password":"secure_password"}' | jq -r .access_token)

echo "Received JWT: $TOKEN"
```

# 3. Call a protected endpoint
```bash
curl -s http://127.0.0.1:5000/protected \
     -H "Authorization: Bearer $TOKEN" | jq

(.venv) @btholath ➜ /workspaces/mlops-ecommerce-recommendation-system-aws (main) $ curl -s http://127.0.0.1:5000/protected \
     -H "Authorization: Bearer $TOKEN" | jq
```
{
  "claims": {
    "exp": 1750611442,
    "iat": 1750525042,
    "jti": "563ffe1e22ff166b53ba6661b076d10d",
    "roles": [
      "admin"
    ],
    "user_id": "admin"
  },
  "message": "success"
}

---
(.venv) @btholath ➜ /workspaces/mlops-ecommerce-recommendation-system-aws (main) $ curl -s -X POST http://127.0.0.1:5000/login  -H "Content-Type: application/json"      -d '{"username":"admin", "password":"secure_password"}'
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NTA1MjQ4NjgsImV4cCI6MTc1MDYxMTI2OCwianRpIjoiY2I1YjE4YTA4MjNmMjk2ZTY2OGJjOTc4YTJkNTkyZGYiLCJ1c2VyX2lkIjoiYWRtaW4iLCJyb2xlcyI6WyJhZG1pbiJdfQ.JZ2wPtTJoy_lHUgoBl2jC5pBCAzFWZXEfA60gJyfIv4",
  "expires_in": 86400
}

