from functools import wraps
from flask import session
from werkzeug.exceptions import Forbidden

def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user or user.get("role") not in roles:
                raise Forbidden()
            return fn(*args, **kwargs)
        return wrapper
    return decorator