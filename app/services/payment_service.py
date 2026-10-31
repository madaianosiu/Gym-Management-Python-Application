from datetime import datetime, timedelta, timezone
from uuid import uuid4
import re
from google.api_core.exceptions import GoogleAPICallError


class PaymentService:
    @staticmethod
    def list_user_payments(fb, user_id: str) -> list[dict]:
        if not fb or not fb.is_ready() or not user_id:
            return []

        try:
            docs = fb.db.collection("payments").where("user_id", "==", user_id).stream()
            payments = [doc.to_dict() or {} for doc in docs]
        except GoogleAPICallError:
            return []

        return sorted(
            payments,
            key=lambda payment: payment.get("created_at", ""),
            reverse=True,
        )

    @staticmethod
    def get_user_payment(fb, user_id: str, payment_id: str) -> dict:
        if not fb or not fb.is_ready() or not user_id or not payment_id:
            return {}

        try:
            snap = fb.db.collection("payments").document(payment_id).get()
        except GoogleAPICallError:
            return {}

        if not snap.exists:
            return {}
        payment = snap.to_dict() or {}
        return payment if payment.get("user_id") == user_id else {}

    @staticmethod
    def _validate_card(payload: dict) -> str | None:
        card_name = (payload.get("card_name") or "").strip()
        card_number = re.sub(r"\D", "", payload.get("card_number") or "")
        expiry = (payload.get("expiry") or "").strip()
        cvv = re.sub(r"\D", "", payload.get("cvv") or "")

        if not card_name:
            return "Cardholder name is required."

        if len(card_number) < 13 or len(card_number) > 19:
            return "Card number must have between 13 and 19 digits."

        match = re.fullmatch(r"(0[1-9]|1[0-2])\/(\d{2})", expiry)
        if not match:
            return "Expiry must be in MM/YY format."

        month = int(match.group(1))
        year = 2000 + int(match.group(2))
        now = datetime.now(timezone.utc)
        expiry_date = datetime(year, month, 1, tzinfo=timezone.utc)
        next_month = expiry_date.replace(day=28) + timedelta(days=4)
        expiry_end = next_month.replace(day=1) - timedelta(seconds=1)
        if expiry_end < now:
            return "Card expiry date is in the past."

        if len(cvv) not in {3, 4}:
            return "CVV must have 3 or 4 digits."

        return None

    @staticmethod
    def complete_checkout(fb, user: dict, plan: dict, payment_input: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Firebase is not available right now."}

        validation_error = PaymentService._validate_card(payment_input)
        if validation_error:
            return {"ok": False, "message": validation_error}

        user_id = user.get("id")
        if not user_id:
            return {"ok": False, "message": "You must be logged in to complete payment."}

        now = datetime.now(timezone.utc)
        end_at = now + timedelta(days=int(plan.get("duration_days", 30)))
        payment_id = f"pay_{uuid4().hex[:12]}"
        subscription_id = f"sub_{uuid4().hex[:12]}"
        card_digits = re.sub(r"\D", "", payment_input.get("card_number") or "")

        payment_record = {
            "id": payment_id,
            "user_id": user_id,
            "plan_id": plan.get("id"),
            "plan_name": plan.get("name"),
            "amount": int(plan.get("price", 0)),
            "currency": "USD",
            "status": "SUCCESS",
            "provider": PaymentService._detect_card_type(payment_input.get("card_number", "")),
            "cardholder_name": (payment_input.get("card_name") or "").strip(),
            "card_last4": card_digits[-4:],
            "created_at": now.isoformat(),
        }

        subscription_record = {
            "id": subscription_id,
            "user_id": user_id,
            "plan_id": plan.get("id"),
            "plan_name": plan.get("name"),
            "price": int(plan.get("price", 0)),
            "duration_days": int(plan.get("duration_days", 30)),
            "badge": plan.get("badge"),
            "description": plan.get("description"),
            "ideal_for": plan.get("ideal_for"),
            "access_level": plan.get("access_level"),
            "class_access": plan.get("class_access"),
            "coach_support": plan.get("coach_support"),
            "recovery_access": plan.get("recovery_access"),
            "guest_passes": int(plan.get("guest_passes", 0)),
            "features": plan.get("features", []),
            "status": "ACTIVE",
            "start_date": now.isoformat(),
            "end_date": end_at.isoformat(),
            "payment_id": payment_id,
            "updated_at": now.isoformat(),
        }

        user_membership = {
            "plan_id": plan.get("id"),
            "plan_name": plan.get("name"),
            "price": int(plan.get("price", 0)),
            "duration_days": int(plan.get("duration_days", 30)),
            "badge": plan.get("badge"),
            "description": plan.get("description"),
            "ideal_for": plan.get("ideal_for"),
            "access_level": plan.get("access_level"),
            "class_access": plan.get("class_access"),
            "coach_support": plan.get("coach_support"),
            "recovery_access": plan.get("recovery_access"),
            "guest_passes": int(plan.get("guest_passes", 0)),
            "features": plan.get("features", []),
            "status": "ACTIVE",
            "start_date": now.isoformat(),
            "end_date": end_at.isoformat(),
            "payment_id": payment_id,
            "subscription_id": subscription_id,
            "card_last4": card_digits[-4:],
            "updated_at": now.isoformat(),
        }

        try:
            batch = fb.db.batch()
            batch.set(fb.db.collection("payments").document(payment_id), payment_record)
            batch.set(fb.db.collection("subscriptions").document(subscription_id), subscription_record)
            batch.set(
                fb.db.collection("users").document(user_id),
                {
                    "id": user_id,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "active_membership": user_membership,
                    "updated_at": now.isoformat(),
                },
                merge=True,
            )
            batch.commit()
        except GoogleAPICallError:
            return {
                "ok": False,
                "message": "Firebase rejected the payment save. Check the project credentials and Firestore permissions.",
            }

        return {
            "ok": True,
            "payment": payment_record,
            "subscription": subscription_record,
            "membership": user_membership,
        }
    
    @staticmethod
    def _detect_card_type(card_number: str) -> str:
        digits = re.sub(r"\D", "", card_number)
        if digits.startswith("4"):
            return "Visa"
        if digits[:2] in {"51", "52", "53", "54", "55"} or 222100 <= int(digits[:6]) <= 272099:
            return "Mastercard"
        if digits[:2] in {"34", "37"}:
            return "Amex"
        return "Card"

    @staticmethod
    def complete_store_checkout(fb, user: dict, product: dict, payment_input: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Firebase is not available right now."}

        validation_error = PaymentService._validate_card(payment_input)
        if validation_error:
            return {"ok": False, "message": validation_error}

        user_id = user.get("id")
        if not user_id:
            return {"ok": False, "message": "You must be logged in to complete payment."}

        now = datetime.now(timezone.utc)
        order_id = f"ord_{uuid4().hex[:12]}"
        payment_id = f"pay_{uuid4().hex[:12]}"
        card_digits = re.sub(r"\D", "", payment_input.get("card_number") or "")

        payment_record = {
            "id": payment_id,
            "user_id": user_id,
            "item_type": "store",
            "item_id": product.get("id"),
            "item_name": product.get("name"),
            "amount": int(product.get("price", 0)),
            "currency": "USD",
            "status": "SUCCESS",
            "provider": PaymentService._detect_card_type(payment_input.get("card_number", "")),
            "cardholder_name": (payment_input.get("card_name") or "").strip(),
            "card_last4": card_digits[-4:],
            "created_at": now.isoformat(),
        }

        order_record = {
            "id": order_id,
            "user_id": user_id,
            "product_id": product.get("id"),
            "product_name": product.get("name"),
            "price": int(product.get("price", 0)),
            "status": "PAID",
            "payment_id": payment_id,
            "card_last4": card_digits[-4:],
            "created_at": now.isoformat(),
        }

        try:
            batch = fb.db.batch()
            batch.set(fb.db.collection("payments").document(payment_id), payment_record)
            batch.set(fb.db.collection("orders").document(order_id), order_record)
            batch.set(
                fb.db.collection("users").document(user_id),
                {
                    "id": user_id,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "updated_at": now.isoformat(),
                },
                merge=True,
            )
            batch.commit()
        except GoogleAPICallError:
            return {
                "ok": False,
                "message": "Firebase rejected the payment save. Check the project credentials and Firestore permissions.",
            }

        return {
            "ok": True,
            "payment": payment_record,
            "order": order_record,
        }

    @staticmethod
    def complete_cart_checkout(fb, user: dict, products: list[dict], payment_input: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Firebase is not available right now."}

        validation_error = PaymentService._validate_card(payment_input)
        if validation_error:
            return {"ok": False, "message": validation_error}

        user_id = user.get("id")
        if not user_id:
            return {"ok": False, "message": "You must be logged in to complete payment."}

        if not products:
            return {"ok": False, "message": "Your cart is empty."}

        now = datetime.now(timezone.utc)
        payment_id = f"pay_{uuid4().hex[:12]}"
        order_batch_id = f"cart_{uuid4().hex[:12]}"
        card_digits = re.sub(r"\D", "", payment_input.get("card_number") or "")
        total_amount = sum(int(product.get("price", 0)) for product in products)

        payment_record = {
            "id": payment_id,
            "user_id": user_id,
            "item_type": "cart",
            "item_count": len(products),
            "amount": total_amount,
            "currency": "USD",
            "status": "SUCCESS",
            "provider": PaymentService._detect_card_type(payment_input.get("card_number", "")),
            "cardholder_name": (payment_input.get("card_name") or "").strip(),
            "card_last4": card_digits[-4:],
            "created_at": now.isoformat(),
        }

        order_items = []
        for product in products:
            order_items.append(
                {
                    "product_id": product.get("id"),
                    "product_name": product.get("name"),
                    "price": int(product.get("price", 0)),
                }
            )

        order_record = {
            "id": order_batch_id,
            "user_id": user_id,
            "status": "PAID",
            "payment_id": payment_id,
            "card_last4": card_digits[-4:],
            "items": order_items,
            "item_count": len(order_items),
            "total": total_amount,
            "created_at": now.isoformat(),
        }

        try:
            batch = fb.db.batch()
            batch.set(fb.db.collection("payments").document(payment_id), payment_record)
            batch.set(fb.db.collection("orders").document(order_batch_id), order_record)
            batch.set(
                fb.db.collection("users").document(user_id),
                {
                    "id": user_id,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "updated_at": now.isoformat(),
                },
                merge=True,
            )
            batch.commit()
        except GoogleAPICallError:
            return {
                "ok": False,
                "message": "Firebase rejected the payment save. Check the project credentials and Firestore permissions.",
            }

        return {
            "ok": True,
            "payment": payment_record,
            "order": order_record,
        }
