from collections import Counter
from google.api_core.exceptions import GoogleAPICallError


class AdminService:
    @staticmethod
    def _safe_collection_docs(fb, collection_name: str):
        if not fb or not fb.is_ready():
            return []

        try:
            rows = []
            for doc in fb.db.collection(collection_name).stream():
                data = doc.to_dict() or {}
                data.setdefault("id", doc.id)
                rows.append(data)
            return rows
        except GoogleAPICallError:
            return []

    @staticmethod
    def get_dashboard_data(fb):
        users = AdminService._safe_collection_docs(fb, "users")
        payments = AdminService._safe_collection_docs(fb, "payments")
        subscriptions = AdminService._safe_collection_docs(fb, "subscriptions")
        orders = AdminService._safe_collection_docs(fb, "orders")
        messages = AdminService._safe_collection_docs(fb, "messages")
        products = AdminService._safe_collection_docs(fb, "products")

        active_subscriptions = [sub for sub in subscriptions if sub.get("status") == "ACTIVE"]
        total_revenue = sum(int(payment.get("amount", 0)) for payment in payments)

        plan_counter = Counter()
        for sub in active_subscriptions:
            plan_counter[sub.get("plan_name") or "Unknown"] += 1

        product_counter = Counter()
        for order in orders:
            if order.get("product_name"):
                product_counter[order.get("product_name")] += 1
            for item in order.get("items", []):
                product_counter[item.get("product_name") or "Unknown"] += 1

        recent_orders = sorted(
            orders,
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )[:6]
        recent_messages = sorted(
            messages,
            key=lambda item: item.get("created_at", ""),
            reverse=True,
        )[:6]

        plan_rows = [{"name": name, "count": count} for name, count in plan_counter.items()]
        product_rows = [{"name": name, "count": count} for name, count in product_counter.items()]

        return {
            "stats": {
                "members": len(users),
                "active_memberships": len(active_subscriptions),
                "orders": len(orders),
                "messages": len(messages),
                "revenue": total_revenue,
                "products": len(products),
            },
            "plan_rows": plan_rows,
            "product_rows": product_rows,
            "recent_orders": recent_orders,
            "recent_messages": recent_messages,
        }

    @staticmethod
    def get_customers_data(fb):
        users = AdminService._safe_collection_docs(fb, "users")
        payments = AdminService._safe_collection_docs(fb, "payments")
        bookings = AdminService._safe_collection_docs(fb, "bookings")

        rows = []
        for user in users:
            user_id = user.get("id") or user.get("uid")
            user_payments = [payment for payment in payments if payment.get("user_id") == user_id]
            user_bookings = [booking for booking in bookings if booking.get("user_id") == user_id]
            membership = user.get("active_membership") if isinstance(user.get("active_membership"), dict) else {}
            rows.append(
                {
                    "id": user_id,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "role": user.get("role", "USER"),
                    "membership": membership,
                    "payments_count": len(user_payments),
                    "revenue": sum(int(payment.get("amount", 0)) for payment in user_payments),
                    "bookings_count": len(user_bookings),
                }
            )

        return sorted(rows, key=lambda row: (row.get("email") or "").lower())

    @staticmethod
    def list_payments(fb):
        payments = AdminService._safe_collection_docs(fb, "payments")
        return sorted(payments, key=lambda item: item.get("created_at", ""), reverse=True)

    @staticmethod
    def list_bookings(fb):
        bookings = AdminService._safe_collection_docs(fb, "bookings")
        return sorted(bookings, key=lambda item: item.get("created_at", ""), reverse=True)
