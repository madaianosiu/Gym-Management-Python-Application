class AuthService:
    _users = {
        "user@gym.com": {
            "id": "u1",
            "email": "user@gym.com",
            "full_name": "Demo User",
            "role": "USER",
            "password": "1234",
        },
    }

    @staticmethod
    def validate_customer_registration(full_name: str, email: str, password: str) -> str | None:
        email = (email or "").strip().lower()
        password = password or ""

        if not (full_name or "").strip():
            return "Full name is required."

        if not email or "@" not in email:
            return "A valid email address is required."

        if "admin" in email:
            return "Admin accounts cannot be created from customer registration."

        return AuthService.validate_password(password)

    @staticmethod
    def validate_password(password: str) -> str | None:
        password = password or ""
        if len(password) < 8:
            return "Password must be at least 8 characters."
        if not any(ch.isupper() for ch in password):
            return "Password must include at least one uppercase letter."
        if not any(ch.islower() for ch in password):
            return "Password must include at least one lowercase letter."
        if not any(ch.isdigit() for ch in password):
            return "Password must include at least one number."
        if not any(not ch.isalnum() for ch in password):
            return "Password must include at least one special character."
        return None

    @staticmethod
    def login(email: str, password: str) -> dict:
        u = AuthService._users.get(email)
        if not u or u.get("password") != password:
            return {"ok": False, "message": "Invalid email or password."}
        if u.get("role") == "ADMIN":
            return {"ok": False, "message": "Admin accounts must sign in through Firebase."}

        safe_user = {k: u[k] for k in ["id", "email", "full_name", "role"]}
        return {"ok": True, "user": safe_user}

    @staticmethod
    def register(full_name: str, email: str, password: str) -> dict:
        validation_error = AuthService.validate_customer_registration(full_name, email, password)
        if validation_error:
            return {"ok": False, "message": validation_error}

        if email in AuthService._users:
            return {"ok": False, "message": "An account with this email already exists."}

        AuthService._users[email] = {
            "id": f"u{len(AuthService._users) + 1}",
            "email": email,
            "full_name": full_name,
            "role": "USER",
            "password": password,
        }

        safe_user = {k: AuthService._users[email][k] for k in ["id", "email", "full_name", "role"]}
        return {"ok": True, "user": safe_user}
