from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from . import auth_bp
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.services.user_service import UserService


def _is_admin_email(email: str) -> bool:
    normalized = (email or "").strip().lower()
    return normalized.endswith("@admin.com")


def _resolve_user_role(decoded: dict, fb, uid: str, email: str) -> str:
    firebase_role = (decoded.get("role") or "").strip().upper()
    if decoded.get("admin") is True or firebase_role == "ADMIN" or _is_admin_email(email):
        return "ADMIN"
    return UserService.get_role(fb, uid)


@auth_bp.get("/login")
def login_view():
    if SessionService.current_user():
        return redirect(url_for("public.home"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_submit():
    if SessionService.current_user():
        return redirect(url_for("public.home"))

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = request.args.get("next")

    result = AuthService.login(email, password)
    if not result["ok"]:
        flash(result["message"], "error")
        return redirect(url_for("auth.login_view"))

    SessionService.sign_in(result["user"])

    role = result["user"]["role"]
    if role == "ADMIN":
        return redirect("/admin/dashboard")

    return redirect(next_url or url_for("user.dashboard"))


@auth_bp.get("/register")
def register_view():
    if SessionService.current_user():
        return redirect(url_for("public.home"))
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_submit():
    if SessionService.current_user():
        return redirect(url_for("public.home"))

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    result = AuthService.register(full_name, email, password)
    if not result["ok"]:
        flash(result["message"], "error")
        return redirect(url_for("auth.register_view"))

    SessionService.sign_in(result["user"])
    return redirect(url_for("user.dashboard"))


@auth_bp.get("/forgot-password")
def forgot_view():
    if SessionService.current_user():
        return redirect(url_for("public.home"))
    return render_template("auth/forgot_password.html")


@auth_bp.post("/forgot-password")
def forgot_submit():
    flash("If the email exists, you will receive reset instructions.", "info")
    return redirect(url_for("auth.login_view"))


@auth_bp.get("/logout")
def logout():
    SessionService.sign_out()
    return redirect(url_for("public.home"))


@auth_bp.get("/firebase")
def firebase_login_view():
    if SessionService.current_user():
        return redirect(url_for("public.home"))
    return render_template("auth/firebase_login.html")


@auth_bp.post("/firebase/login")
def firebase_login():
    payload = request.get_json(silent=True) or {}
    id_token = payload.get("idToken")

    if not id_token:
        return jsonify({"ok": False, "message": "Missing idToken."}), 400

    fb = current_app.config.get("FIREBASE")
    if not fb or not fb.is_ready():
        return jsonify({"ok": False, "message": "Firebase is not initialized."}), 500

    try:
        decoded = fb.verify_id_token(id_token)
        email = decoded.get("email") or ""
        uid = decoded.get("uid")
        role = _resolve_user_role(decoded, fb, uid, email)
        user = {
            "id": uid,
            "email": email,
            "full_name": decoded.get("name") or email or "User",
            "role": role,
        }
        if role != "ADMIN":
            UserService.ensure_customer_account(fb, uid, user)

        SessionService.sign_in(user)
        return jsonify({"ok": True, "user": user}), 200
    except Exception:
        return jsonify({"ok": False, "message": "Invalid or expired token."}), 401
