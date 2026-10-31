from functools import wraps
from flask import session, redirect, url_for, request

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("auth.login_view", next=request.path))
        return fn(*args, **kwargs)
    return wrapper