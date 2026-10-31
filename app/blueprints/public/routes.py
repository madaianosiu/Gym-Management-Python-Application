from flask import render_template, redirect, session, url_for, request, flash
from . import public_bp
from app.services.membership_service import MembershipService
from app.services.store_service import StoreService
from app.services.message_service import MessageService
from app.services.session_service import SessionService
from app.services.user_service import UserService
from flask import current_app

@public_bp.get("/firebase/ping")
def firebase_ping():
    fb = current_app.config.get("FIREBASE")
    return {
        "firebase_ready": bool(fb and fb.is_ready()),
        "error": None if not fb else fb.last_error(),
        "enabled": None if not fb else fb.enabled,
    }
@public_bp.get("/")
def home():
    return render_template("public/home.html")

@public_bp.get("/about")
def about():
    return render_template("public/about.html")

@public_bp.get("/pricing")
def pricing():
    if session.get("user"):
        return redirect(url_for("user.memberships"))

    plans = MembershipService.get_plans()
    return render_template("public/pricing.html", plans=plans)

@public_bp.get("/contact")
def contact():
    return render_template("public/contact.html")


@public_bp.post("/contact")
def contact_submit():
    fb = current_app.config.get("FIREBASE")
    result = MessageService.create_message(
        fb,
        {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "message": request.form.get("message", ""),
        },
    )

    if not result.get("ok"):
        flash(result.get("message") or "Message could not be sent.", "error")
        return redirect(url_for("public.contact"))

    flash("Thanks for reaching out. Your message was sent successfully.", "success")
    return redirect(url_for("public.contact"))


def _cart_count():
    fb = current_app.config.get("FIREBASE")
    user = SessionService.current_user() or {}
    uid = user.get("id")

    if fb and fb.is_ready() and uid:
        cart = UserService.get_cart(fb, uid)
        local_cart = session.get("cart", [])
        if not cart and local_cart:
            UserService.upsert_cart(fb, uid, local_cart)
            return len(local_cart)

        session["cart"] = cart
        session.modified = True
        return len(cart)

    return len(session.get("cart", []))


@public_bp.get("/store")
def store():
    fb = current_app.config.get("FIREBASE")
    StoreService.seed_defaults(fb)
    products = StoreService.get_products(fb)
    return render_template("public/store.html", products=products, cart_count=_cart_count())
