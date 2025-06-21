import jwt
import datetime
import hashlib
import secrets
from functools import wraps
from flask import Flask, request, jsonify, session
import bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

class SecureAuth:
    def __init__(self, secret_key, token_expiration_hours=24):
        self.secret_key = secret_key
        self.token_expiration_hours = token_expiration_hours
        self.algorithm = 'HS256'
    
    def hash_password(self, password):
        """Securely hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)
    
    def generate_token(self, user_id, roles=None):
        """Generate JWT token with expiration"""
        payload = {
            'user_id': user_id,
            'roles': roles or [],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=self.token_expiration_hours),
            'iat': datetime.datetime.utcnow(),
            'jti': secrets.token_hex(16)  # Unique token ID for revocation
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
    
    def require_auth(self, required_roles=None):
        """Decorator for protected routes"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                token = request.headers.get('Authorization')
                if not token:
                    return jsonify({'error': 'No token provided'}), 401
                
                try:
                    # Remove 'Bearer ' prefix if present
                    if token.startswith('Bearer '):
                        token = token[7:]
                    
                    payload = self.verify_token(token)
                    
                    # Check roles if required
                    if required_roles:
                        user_roles = payload.get('roles', [])
                        if not any(role in user_roles for role in required_roles):
                            return jsonify({'error': 'Insufficient permissions'}), 403
                    
                    # Add user info to request context
                    request.current_user = payload
                    return f(*args, **kwargs)
                
                except ValueError as e:
                    return jsonify({'error': str(e)}), 401
            
            return decorated_function
        return decorator

# Initialize auth system
auth = SecureAuth(app.config['SECRET_KEY'])

# Example usage
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # In production, validate against database
    # This is a simplified example
    if username == 'admin' and password == 'secure_password':
        token = auth.generate_token(user_id=1, roles=['admin', 'user'])
        return jsonify({
            'token': token,
            'expires_in': auth.token_expiration_hours * 3600
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/protected')
@auth.require_auth()
def protected_route():
    return jsonify({
        'message': 'Access granted',
        'user_id': request.current_user['user_id']
    })

@app.route('/admin-only')
@auth.require_auth(required_roles=['admin'])
def admin_only():
    return jsonify({'message': 'Admin access granted'})