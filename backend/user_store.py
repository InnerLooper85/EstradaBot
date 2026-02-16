"""
GCS-backed User Store for EstradaBot.
Persists user accounts to JSON in GCS (or local filesystem in dev mode).
Supports add, update, disable/enable, and password changes.
"""

import json
import threading
from datetime import datetime
from typing import Dict, List, Optional

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

import gcs_storage

# GCS path for user data
USERS_FILE = 'state/users.json'


class User(UserMixin):
    """User model for Flask-Login with persistent storage support."""

    def __init__(self, username, password_hash, role='user', active=True,
                 created_at=None, updated_at=None):
        self.id = username
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.active = active
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.active

    def to_dict(self):
        """Serialize user for JSON storage (excludes password_hash from API responses)."""
        return {
            'username': self.username,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

    def to_storage_dict(self):
        """Serialize user for persistent storage (includes password_hash)."""
        return {
            'password_hash': self.password_hash,
            'role': self.role,
            'active': self.active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


# Valid roles
VALID_ROLES = ('admin', 'planner', 'mfgeng', 'customer_service', 'operator', 'guest')


class UserStore:
    """Thread-safe, GCS-backed user store."""

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._lock = threading.Lock()

    def load(self):
        """Load users from GCS. Returns True if loaded successfully."""
        try:
            if gcs_storage.USE_LOCAL_STORAGE:
                data = gcs_storage._local_load_json(USERS_FILE)
            else:
                bucket = gcs_storage.get_bucket()
                blob = bucket.blob(USERS_FILE)
                try:
                    json_data = blob.download_as_text()
                    data = json.loads(json_data)
                except Exception:
                    data = None

            if data and isinstance(data, dict):
                with self._lock:
                    self._users = {}
                    for username, info in data.items():
                        self._users[username] = User(
                            username=username,
                            password_hash=info['password_hash'],
                            role=info.get('role', 'guest'),
                            active=info.get('active', True),
                            created_at=info.get('created_at'),
                            updated_at=info.get('updated_at'),
                        )
                print(f"[UserStore] Loaded {len(self._users)} users from storage")
                return True
            return False
        except Exception as e:
            print(f"[UserStore] Failed to load users: {e}")
            return False

    def save(self):
        """Persist current users to GCS."""
        with self._lock:
            data = {
                username: user.to_storage_dict()
                for username, user in self._users.items()
            }

        try:
            if gcs_storage.USE_LOCAL_STORAGE:
                gcs_storage._local_save_json(USERS_FILE, data)
            else:
                bucket = gcs_storage.get_bucket()
                blob = bucket.blob(USERS_FILE)
                blob.upload_from_string(
                    json.dumps(data, default=str),
                    content_type='application/json'
                )
            print(f"[UserStore] Saved {len(data)} users to storage")
            return True
        except Exception as e:
            print(f"[UserStore] Failed to save users: {e}")
            return False

    def seed_from_env(self, admin_username, admin_password, users_env=''):
        """Seed users from environment variables (first-run migration)."""
        now = datetime.utcnow().isoformat()

        # Always ensure admin exists
        if admin_username not in self._users:
            self._users[admin_username] = User(
                username=admin_username,
                password_hash=generate_password_hash(admin_password),
                role='admin',
                active=True,
                created_at=now,
                updated_at=now,
            )
            print(f"[UserStore] Seeded admin user: {admin_username}")

        # Parse additional users from USERS env var
        if users_env:
            for user_pair in users_env.split(','):
                parts = user_pair.strip().split(':')
                if len(parts) >= 2:
                    username = parts[0].strip()
                    password = parts[1].strip()
                    role = parts[2].strip().lower() if len(parts) > 2 else 'guest'
                    if username and username not in self._users:
                        self._users[username] = User(
                            username=username,
                            password_hash=generate_password_hash(password),
                            role=role,
                            active=True,
                            created_at=now,
                            updated_at=now,
                        )
                        print(f"[UserStore] Seeded user from env: {username} ({role})")

        self.save()

    def get(self, username) -> Optional[User]:
        """Get a user by username."""
        return self._users.get(username)

    def get_active(self, username) -> Optional[User]:
        """Get a user by username, only if active."""
        user = self._users.get(username)
        if user and user.active:
            return user
        return None

    def list_users(self) -> List[Dict]:
        """Return list of all users (without password hashes)."""
        with self._lock:
            return [user.to_dict() for user in self._users.values()]

    def add_user(self, username, password, role='guest') -> tuple:
        """Add a new user. Returns (success, message)."""
        username = username.strip()
        if not username:
            return False, 'Username is required.'
        if len(username) < 3:
            return False, 'Username must be at least 3 characters.'
        if username in self._users:
            return False, f'User "{username}" already exists.'
        if role not in VALID_ROLES:
            return False, f'Invalid role: {role}. Valid roles: {", ".join(VALID_ROLES)}'
        if len(password) < 6:
            return False, 'Password must be at least 6 characters.'

        now = datetime.utcnow().isoformat()
        with self._lock:
            self._users[username] = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                active=True,
                created_at=now,
                updated_at=now,
            )
        self.save()
        return True, f'User "{username}" created successfully.'

    def update_role(self, username, new_role) -> tuple:
        """Update a user's role. Returns (success, message)."""
        if username not in self._users:
            return False, f'User "{username}" not found.'
        if new_role not in VALID_ROLES:
            return False, f'Invalid role: {new_role}.'

        with self._lock:
            self._users[username].role = new_role
            self._users[username].updated_at = datetime.utcnow().isoformat()
        self.save()
        return True, f'Role updated to "{new_role}".'

    def disable_user(self, username) -> tuple:
        """Disable a user account. Returns (success, message)."""
        if username not in self._users:
            return False, f'User "{username}" not found.'
        user = self._users[username]
        if user.role == 'admin':
            # Prevent disabling the last admin
            admin_count = sum(1 for u in self._users.values() if u.role == 'admin' and u.active)
            if admin_count <= 1:
                return False, 'Cannot disable the last active admin account.'

        with self._lock:
            user.active = False
            user.updated_at = datetime.utcnow().isoformat()
        self.save()
        return True, f'User "{username}" has been disabled.'

    def enable_user(self, username) -> tuple:
        """Re-enable a disabled user account. Returns (success, message)."""
        if username not in self._users:
            return False, f'User "{username}" not found.'

        with self._lock:
            self._users[username].active = True
            self._users[username].updated_at = datetime.utcnow().isoformat()
        self.save()
        return True, f'User "{username}" has been re-enabled.'

    def reset_password(self, username, new_password) -> tuple:
        """Admin password reset (no current password required). Returns (success, message)."""
        if username not in self._users:
            return False, f'User "{username}" not found.'
        if len(new_password) < 6:
            return False, 'Password must be at least 6 characters.'

        with self._lock:
            self._users[username].password_hash = generate_password_hash(new_password)
            self._users[username].updated_at = datetime.utcnow().isoformat()
        self.save()
        return True, 'Password has been reset.'

    def change_password(self, username, current_password, new_password) -> tuple:
        """Self-service password change (requires current password). Returns (success, message)."""
        if username not in self._users:
            return False, 'User not found.'
        user = self._users[username]
        if not user.check_password(current_password):
            return False, 'Current password is incorrect.'
        if len(new_password) < 6:
            return False, 'New password must be at least 6 characters.'

        with self._lock:
            user.password_hash = generate_password_hash(new_password)
            user.updated_at = datetime.utcnow().isoformat()
        self.save()
        return True, 'Password changed successfully.'
