from datetime import datetime, timezone

from flask import render_template, request, redirect, url_for, flash, current_app, session, jsonify

from . import user_bp
from app.services.ai_coach_service import AICoachService
from app.services.booking_service import BookingService
from app.middleware.auth_guard import login_required
from app.services.membership_service import MembershipService
from app.services.payment_service import PaymentService
from app.services.session_service import SessionService
from app.services.store_service import StoreService
from app.services.user_service import UserService


def _current_user_context():
    fb = current_app.config.get("FIREBASE")
    user = SessionService.current_user() or {}
    uid = user.get("id")

    profile = {}
    membership = {}
    if fb and fb.is_ready() and uid:
        profile = UserService.get_profile(fb, uid)
        membership = UserService.get_active_membership(fb, uid)

    return fb, user, uid, profile, membership


def _cart_product_ids():
    fb = current_app.config.get("FIREBASE")
    user = SessionService.current_user() or {}
    uid = user.get("id")

    if fb and fb.is_ready() and uid:
        cart = UserService.get_cart(fb, uid)
        local_cart = session.get("cart", [])
        if not cart and local_cart:
            UserService.upsert_cart(fb, uid, local_cart)
            return local_cart

        session["cart"] = cart
        session.modified = True
        return cart

    return session.get("cart", [])


def _save_cart_product_ids(product_ids):
    cart = [str(product_id) for product_id in product_ids if product_id]
    session["cart"] = cart
    session.modified = True

    fb = current_app.config.get("FIREBASE")
    user = SessionService.current_user() or {}
    uid = user.get("id")
    if fb and fb.is_ready() and uid:
        UserService.upsert_cart(fb, uid, cart)


def _cart_products():
    fb = current_app.config.get("FIREBASE")
    return StoreService.get_products_by_ids(_cart_product_ids(), fb)


def _cart_count():
    return len(_cart_product_ids())


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _membership_days_remaining(membership):
    end_date = _parse_iso((membership or {}).get("end_date"))
    if not end_date:
        return None
    now = datetime.now(end_date.tzinfo or timezone.utc)
    return max((end_date.date() - now.date()).days, 0)


def _dashboard_notifications(fb, uid, profile, membership):
    notifications = []
    days_remaining = _membership_days_remaining(membership)
    if days_remaining is not None and days_remaining <= 7:
        notifications.append(
            {
                "tone": "warning",
                "title": "Membership reminder",
                "message": f"Your membership expires in {days_remaining} day{'s' if days_remaining != 1 else ''}.",
                "href": url_for("user.my_membership"),
                "action": "Review",
            }
        )

    cart_count = _cart_count()
    if cart_count:
        notifications.append(
            {
                "tone": "info",
                "title": "Cart saved",
                "message": f"{cart_count} item{'s' if cart_count != 1 else ''} are waiting in your cart.",
                "href": url_for("user.cart"),
                "action": "Open cart",
            }
        )

    completion = UserService.profile_completion(profile)
    if completion.get("percent", 100) < 100:
        notifications.append(
            {
                "tone": "info",
                "title": "Profile completion",
                "message": f"Your profile is {completion['percent']}% complete.",
                "href": url_for("user.profile"),
                "action": "Complete",
            }
        )

    products = StoreService.get_products(fb)
    if products:
        notifications.append(
            {
                "tone": "success",
                "title": "New product available",
                "message": f"{products[0].get('name')} is available in the store.",
                "href": url_for("public.store"),
                "action": "View",
            }
        )

    return notifications[:4]


@user_bp.get("/dashboard")
@login_required
def dashboard():
    fb, user, uid, profile, membership = _current_user_context()
    membership = MembershipService.enrich_membership(membership)
    ai_profile = UserService.get_ai_profile(fb, uid) if uid else {}
    saved_ai_plans = UserService.get_saved_ai_plans(fb, uid) if uid else []
    return render_template(
        "user/dashboard.html",
        user=user,
        membership=membership,
        cart_count=_cart_count(),
        profile=profile,
        ai_profile=ai_profile,
        saved_ai_plans=saved_ai_plans,
        notifications=_dashboard_notifications(fb, uid, profile, membership),
    )


@user_bp.get("/profile")
@login_required
def profile():
    _, _, _, profile_data, _ = _current_user_context()
    return render_template("user/profile.html", profile=profile_data)


@user_bp.post("/profile")
@login_required
def profile_save():
    fb, user, uid, _, _ = _current_user_context()

    if not (fb and fb.is_ready() and uid):
        flash("Profile storage is not available. Firebase is not ready.", "error")
        return redirect(url_for("user.profile"))

    payload = {
        "full_name": request.form.get("full_name", ""),
        "phone": request.form.get("phone", ""),
        "address_line1": request.form.get("address_line1", ""),
        "address_line2": request.form.get("address_line2", ""),
        "city": request.form.get("city", ""),
        "state": request.form.get("state", ""),
        "zip": request.form.get("zip", ""),
        "country": request.form.get("country", ""),
        "fitness_goal": request.form.get("fitness_goal", ""),
        "fitness_level": request.form.get("fitness_level", ""),
        "email": user.get("email", ""),
    }

    UserService.upsert_profile(fb, uid, payload)
    flash("Profile updated successfully.", "success")
    return redirect(url_for("user.profile"))


@user_bp.get("/memberships")
@login_required
def memberships():
    plans = MembershipService.get_plans()
    return render_template("user/memberships.html", plans=plans)


@user_bp.get("/my-membership")
@login_required
def my_membership():
    _, _, _, profile, membership = _current_user_context()
    membership = MembershipService.enrich_membership(membership)
    days_remaining = _membership_days_remaining(membership)
    return render_template(
        "user/my_membership.html",
        profile=profile,
        membership=membership,
        days_remaining=days_remaining,
    )


@user_bp.get("/classes")
@login_required
def classes():
    fb, user, uid, _, membership = _current_user_context()
    bookings = BookingService.list_user_bookings(fb, uid)
    return render_template(
        "user/classes.html",
        classes=BookingService.get_classes(),
        bookings=bookings,
        membership=MembershipService.enrich_membership(membership),
    )


@user_bp.get("/bookings")
@login_required
def my_bookings():
    fb, _, uid, _, _ = _current_user_context()
    bookings = BookingService.list_user_bookings(fb, uid)
    return render_template("user/bookings.html", bookings=bookings)


@user_bp.post("/classes/<class_id>/book")
@login_required
def class_book(class_id):
    fb, user, _, _, _ = _current_user_context()
    class_item = BookingService.get_class(class_id)
    if not class_item:
        flash("Selected class was not found.", "error")
        return redirect(url_for("user.classes"))

    result = BookingService.create_booking(fb, user, class_item)
    flash(result.get("message") or "Class booked successfully.", "success" if result.get("ok") else "error")
    return redirect(url_for("user.my_bookings" if result.get("ok") else "user.classes"))


@user_bp.post("/cart/add/<product_id>")
@login_required
def cart_add(product_id):
    fb = current_app.config.get("FIREBASE")
    product = StoreService.get_product(product_id, fb)
    if not product:
        flash("Selected product was not found.", "error")
        return redirect(url_for("public.store"))

    cart = _cart_product_ids()
    cart.append(product.get("id"))
    _save_cart_product_ids(cart)
    flash(f"{product.get('name')} was added to your cart.", "success")
    return redirect(url_for("user.cart"))


@user_bp.post("/cart/remove/<product_id>")
@login_required
def cart_remove(product_id):
    cart = _cart_product_ids()
    if product_id in cart:
        cart.remove(product_id)
        _save_cart_product_ids(cart)
        flash("Product removed from cart.", "info")
    return redirect(url_for("user.cart"))


@user_bp.get("/cart")
@login_required
def cart():
    products = _cart_products()
    total = StoreService.cart_total(products)
    return render_template("user/cart.html", products=products, total=total)


@user_bp.get("/checkout")
@login_required
def checkout():
    fb, user, _, profile, membership = _current_user_context()
    plan_key = request.args.get("plan") or request.args.get("plan_id")
    product_key = request.args.get("product") or request.args.get("product_id")
    checkout_mode = request.args.get("mode")
    selected_plan = MembershipService.get_plan(plan_key)
    selected_product = StoreService.get_product(product_key, fb)
    cart_products = _cart_products() if checkout_mode == "cart" else []

    if not selected_plan and not selected_product and not cart_products:
        flash("Choose a membership plan or a store product before checkout.", "error")
        return redirect(url_for("user.memberships"))

    cardholder_name = profile.get("full_name") or user.get("full_name") or ""
    return render_template(
        "user/checkout.html",
        selected_plan=selected_plan,
        selected_product=selected_product,
        cart_products=cart_products,
        cart_total=StoreService.cart_total(cart_products),
        membership=membership,
        cardholder_name=cardholder_name,
    )


@user_bp.post("/checkout")
@login_required
def checkout_submit():
    fb, user, _, profile, _ = _current_user_context()
    plan_key = request.form.get("plan_id") or request.form.get("plan")
    product_key = request.form.get("product_id") or request.form.get("product")
    checkout_mode = request.form.get("checkout_mode")
    selected_plan = MembershipService.get_plan(plan_key)
    selected_product = StoreService.get_product(product_key, fb)
    cart_products = _cart_products() if checkout_mode == "cart" else []
    payment_input = {
        "card_name": request.form.get("card_name", ""),
        "card_number": request.form.get("card_number", ""),
        "expiry": request.form.get("expiry", ""),
        "cvv": request.form.get("cvv", ""),
    }

    if not selected_plan and not selected_product and not cart_products:
        flash("Selected item is invalid.", "error")
        return redirect(url_for("user.memberships"))

    if selected_plan:
        result = PaymentService.complete_checkout(
            fb,
            user,
            selected_plan,
            payment_input,
        )
        checkout_summary = {
            "kind": "membership",
            "name": selected_plan.get("name"),
            "price": selected_plan.get("price"),
        }
    elif selected_product:
        result = PaymentService.complete_store_checkout(
            fb,
            user,
            selected_product,
            payment_input,
        )
        checkout_summary = {
            "kind": "store",
            "name": selected_product.get("name"),
            "price": selected_product.get("price"),
        }
    else:
        result = PaymentService.complete_cart_checkout(
            fb,
            user,
            cart_products,
            payment_input,
        )
        checkout_summary = {
            "kind": "cart",
            "items": [
                {"name": product.get("name"), "price": product.get("price")}
                for product in cart_products
            ],
            "price": StoreService.cart_total(cart_products),
        }

    if not result.get("ok"):
        session.pop("last_checkout", None)
        session.modified = True
        flash(result.get("message") or "Payment failed. Please try again.", "error")
        cardholder_name = profile.get("full_name") or user.get("full_name") or ""
        return render_template(
            "user/checkout.html",
            selected_plan=selected_plan,
            selected_product=selected_product,
            cart_products=cart_products,
            cart_total=StoreService.cart_total(cart_products),
            membership={},
            cardholder_name=cardholder_name,
        )

    payment = result.get("payment") or {}
    checkout_summary.update(
        {
            "payment_id": payment.get("id"),
            "status": payment.get("status") or "SUCCESS",
            "currency": payment.get("currency") or "USD",
            "card_last4": payment.get("card_last4"),
            "created_at": payment.get("created_at"),
        }
    )
    if result.get("membership"):
        checkout_summary["membership"] = result.get("membership")

    session["last_checkout"] = checkout_summary
    session.modified = True

    if checkout_mode == "cart":
        _save_cart_product_ids([])

    flash("Payment completed successfully.", "success")
    return redirect(url_for("user.payment_success"))


@user_bp.get("/payment/success")
@login_required
def payment_success():
    _, _, _, _, membership = _current_user_context()
    last_checkout = session.get("last_checkout")
    return render_template("user/payment_success.html", membership=membership, last_checkout=last_checkout)


@user_bp.get("/payment-history")
@login_required
def payment_history():
    fb, _, uid, _, _ = _current_user_context()
    payments = PaymentService.list_user_payments(fb, uid)
    return render_template("user/payment_history.html", payments=payments)


@user_bp.get("/payment-history/<payment_id>")
@login_required
def payment_receipt(payment_id):
    fb, _, uid, _, _ = _current_user_context()
    payment = PaymentService.get_user_payment(fb, uid, payment_id)
    if not payment:
        flash("Receipt was not found for this account.", "error")
        return redirect(url_for("user.payment_history"))
    return render_template("user/payment_receipt.html", payment=payment)


@user_bp.post("/ai-coach/chat")
@login_required
def ai_coach_chat():
    fb, _, uid, _, _ = _current_user_context()
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()

    if not message:
        return jsonify({"ok": False, "message": "Message is required."}), 400

    ai_profile = UserService.get_ai_profile(fb, uid) if uid else {}
    conversation_history = session.get("ai_coach_history", [])
    coach_result = AICoachService.build_response(message, ai_profile, conversation_history)

    if uid:
        UserService.upsert_ai_profile(fb, uid, coach_result.get("profile") or {})

    conversation_history.extend(
        [
            {"role": "user", "content": message},
            {"role": "assistant", "content": coach_result.get("reply") or ""},
        ]
    )
    session["ai_coach_history"] = conversation_history[-12:]
    session["last_ai_reply"] = coach_result.get("reply") or ""
    session.modified = True

    return jsonify(
        {
            "ok": True,
            "reply": coach_result.get("reply"),
            "profile": coach_result.get("profile") or {},
        }
    )


@user_bp.post("/ai-coach/save-plan")
@login_required
def ai_coach_save_plan():
    fb, _, uid, _, _ = _current_user_context()
    payload = request.get_json(silent=True) or {}
    content = (payload.get("content") or session.get("last_ai_reply") or "").strip()
    title = (payload.get("title") or "Saved AI Coach plan").strip()
    result = UserService.save_ai_plan(fb, uid, title, content)
    return jsonify(result), 200 if result.get("ok") else 400
