import hashlib
import datetime


def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


class User:
    def __init__(self, username, password, role="user"):
        self.username = username
        self.password_hash = _hash(password)
        self.role = role
        self.created = datetime.datetime.now()
        self.last_login = None
        self.locked = False
        self.failed_attempts = 0

    def check_password(self, password):
        return self.password_hash == _hash(password)

    def __repr__(self):
        return f"<User: {self.username}, role={self.role}, locked={self.locked}>"


PERMISSIONS = {
    "admin": ["read", "write", "delete", "manage_users", "scheduler", "memory", "fs", "ipc", "driver"],
    "user":  ["read", "write", "scheduler", "memory", "fs", "ipc"],
    "guest": ["read", "fs"],
}

MAX_ATTEMPTS = 3


class Security:
    def __init__(self):
        self.users = {
            "admin": User("admin", "admin123", role="admin"),
            "guest": User("guest", "guest",  role="guest"),
        }
        self.sessions = {}
        self.audit_log = []

    def _log(self, event):
        self.audit_log.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
        })

    def register(self, username, password, role="user"):
        if username in self.users:
            return False, f"Username '{username}' already exists"
        if len(password) < 4:
            return False, "Password must be at least 4 characters"
        if role not in PERMISSIONS:
            return False, f"Invalid role '{role}'"
        self.users[username] = User(username, password, role=role)
        self._log(f"User '{username}' registered with role '{role}'")
        return True, f"User '{username}' created"

    def login(self, username, password):
        user = self.users.get(username)
        if user is None:
            self._log(f"Failed login: unknown user '{username}'")
            return False, "Invalid credentials"
        if user.locked:
            return False, f"Account '{username}' is locked"
        if not user.check_password(password):
            user.failed_attempts += 1
            if user.failed_attempts >= MAX_ATTEMPTS:
                user.locked = True
                self._log(f"Account '{username}' locked after {MAX_ATTEMPTS} failed attempts")
                return False, f"Account locked after {MAX_ATTEMPTS} failed attempts"
            self._log(f"Failed login for '{username}' ({user.failed_attempts}/{MAX_ATTEMPTS})")
            return False, f"Invalid credentials ({MAX_ATTEMPTS - user.failed_attempts} attempts left)"
        user.failed_attempts = 0
        user.last_login = datetime.datetime.now()
        token = _hash(username + str(user.last_login))[:16]
        self.sessions[token] = username
        self._log(f"User '{username}' logged in")
        return True, token

    def logout(self, token):
        username = self.sessions.pop(token, None)
        if username:
            self._log(f"User '{username}' logged out")
            return True, f"User '{username}' logged out"
        return False, "Invalid session"

    def is_authenticated(self, token):
        return token in self.sessions

    def get_user(self, token):
        username = self.sessions.get(token)
        if username:
            return self.users.get(username)
        return None

    def has_permission(self, token, action):
        user = self.get_user(token)
        if user is None:
            return False
        return action in PERMISSIONS.get(user.role, [])

    def change_password(self, token, old_password, new_password):
        user = self.get_user(token)
        if user is None:
            return False, "Not authenticated"
        if not user.check_password(old_password):
            return False, "Old password incorrect"
        if len(new_password) < 4:
            return False, "Password must be at least 4 characters"
        user.password_hash = _hash(new_password)
        self._log(f"User '{user.username}' changed password")
        return True, "Password changed"

    def unlock_user(self, admin_token, username):
        admin = self.get_user(admin_token)
        if admin is None or admin.role != "admin":
            return False, "Admin access required"
        user = self.users.get(username)
        if user is None:
            return False, f"User '{username}' not found"
        user.locked = False
        user.failed_attempts = 0
        self._log(f"Admin '{admin.username}' unlocked user '{username}'")
        return True, f"User '{username}' unlocked"

    def list_users(self, admin_token):
        admin = self.get_user(admin_token)
        if admin is None or admin.role != "admin":
            return False, "Admin access required"
        result = []
        for u in self.users.values():
            result.append({
                "username": u.username,
                "role": u.role,
                "locked": u.locked,
                "last_login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Never",
            })
        return True, result

    def get_audit_log(self, admin_token):
        admin = self.get_user(admin_token)
        if admin is None or admin.role != "admin":
            return False, "Admin access required"
        return True, self.audit_log
