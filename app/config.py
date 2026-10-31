import os
from secrets import token_hex

class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    SECRET_KEY = (
        token_hex(32)
        if ENV == "development" and os.getenv("LOGOUT_ON_RESTART", "0") == "1"
        else os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    )

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"

    # Firebase (placeholder)
    FIREBASE_ENABLED = os.getenv("FIREBASE_ENABLED", "0") == "1"
