from flask import render_template, current_app, request, redirect, url_for, flash

from . import admin_bp
from app.middleware.auth_guard import login_required
from app.middleware.role_guard import roles_required
from app.services.admin_service import AdminService
from app.services.message_service import MessageService
from app.services.store_service import StoreService


@admin_bp.get("/dashboard")
@login_required
@roles_required("ADMIN")
def dashboard():
    fb = current_app.config.get("FIREBASE")
    StoreService.seed_defaults(fb)
    admin_data = AdminService.get_dashboard_data(fb)
    return render_template("admin/dashboard.html", admin_data=admin_data)


@admin_bp.get("/customers")
@login_required
@roles_required("ADMIN")
def customers():
    fb = current_app.config.get("FIREBASE")
    customers_data = AdminService.get_customers_data(fb)
    return render_template("admin/customers.html", customers=customers_data)


@admin_bp.get("/payments")
@login_required
@roles_required("ADMIN")
def payments():
    fb = current_app.config.get("FIREBASE")
    payments_data = AdminService.list_payments(fb)
    return render_template("admin/payments.html", payments=payments_data)


@admin_bp.get("/bookings")
@login_required
@roles_required("ADMIN")
def bookings():
    fb = current_app.config.get("FIREBASE")
    bookings_data = AdminService.list_bookings(fb)
    return render_template("admin/bookings.html", bookings=bookings_data)


@admin_bp.get("/messages")
@login_required
@roles_required("ADMIN")
def messages():
    fb = current_app.config.get("FIREBASE")
    messages = MessageService.list_messages(fb)
    return render_template("admin/messages.html", messages=messages)


@admin_bp.post("/messages/<message_id>/reply")
@login_required
@roles_required("ADMIN")
def message_reply(message_id):
    fb = current_app.config.get("FIREBASE")
    result = MessageService.reply_to_message(
        fb,
        message_id,
        request.form.get("admin_reply", ""),
        request.form.get("status", "REPLIED"),
    )
    flash(result.get("message") or "Message updated.", "success" if result.get("ok") else "error")
    return redirect(url_for("admin.messages"))


@admin_bp.get("/store")
@login_required
@roles_required("ADMIN")
def store():
    fb = current_app.config.get("FIREBASE")
    StoreService.seed_defaults(fb)
    products = StoreService.get_products(fb)
    return render_template("admin/store.html", products=products)


@admin_bp.post("/store/add")
@login_required
@roles_required("ADMIN")
def store_add():
    fb = current_app.config.get("FIREBASE")
    result = StoreService.create_product(
        fb,
        {
            "name": request.form.get("name", ""),
            "price": request.form.get("price", 0),
            "tag": request.form.get("tag", ""),
            "description": request.form.get("description", ""),
            "image": request.form.get("image", ""),
            "features": request.form.get("features", ""),
        },
    )
    flash(result.get("message") or "Product saved.", "success" if result.get("ok") else "error")
    return redirect(url_for("admin.store"))


@admin_bp.post("/store/<product_id>/update")
@login_required
@roles_required("ADMIN")
def store_update(product_id):
    fb = current_app.config.get("FIREBASE")
    result = StoreService.update_product(
        fb,
        product_id,
        {
            "name": request.form.get("name", ""),
            "price": request.form.get("price", 0),
            "tag": request.form.get("tag", ""),
            "description": request.form.get("description", ""),
            "image": request.form.get("image", ""),
            "features": request.form.get("features", ""),
        },
    )
    flash(result.get("message") or "Product updated.", "success" if result.get("ok") else "error")
    return redirect(url_for("admin.store"))


@admin_bp.post("/store/<product_id>/delete")
@login_required
@roles_required("ADMIN")
def store_delete(product_id):
    fb = current_app.config.get("FIREBASE")
    result = StoreService.delete_product(fb, product_id)
    flash(result.get("message") or "Product deleted.", "success" if result.get("ok") else "error")
    return redirect(url_for("admin.store"))
