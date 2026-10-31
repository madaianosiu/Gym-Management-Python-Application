from datetime import datetime, timezone
from google.api_core.exceptions import GoogleAPICallError


class UserService:
    @staticmethod
    def get_profile(fb, uid: str) -> dict:
        try:
            doc_ref = fb.db.collection("users").document(uid)
            snap = doc_ref.get()
        except GoogleAPICallError:
            return {}

        if not snap.exists:
            return {}
        data = snap.to_dict() or {}
        return data

    @staticmethod
    def upsert_profile(fb, uid: str, payload: dict) -> None:
        doc_ref = fb.db.collection("users").document(uid)
        safe = {
            "full_name": (payload.get("full_name") or "").strip(),
            "phone": (payload.get("phone") or "").strip(),
            "address_line1": (payload.get("address_line1") or "").strip(),
            "address_line2": (payload.get("address_line2") or "").strip(),
            "city": (payload.get("city") or "").strip(),
            "state": (payload.get("state") or "").strip(),
            "zip": (payload.get("zip") or "").strip(),
            "country": (payload.get("country") or "").strip(),
            "fitness_goal": (payload.get("fitness_goal") or "").strip(),
            "fitness_level": (payload.get("fitness_level") or "").strip(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            doc_ref.set(safe, merge=True)
        except GoogleAPICallError:
            return

    @staticmethod
    def get_role(fb, uid: str) -> str:
        profile = UserService.get_profile(fb, uid)
        role = (profile.get("role") or "").strip().upper()
        return role if role in {"ADMIN", "USER"} else "USER"

    @staticmethod
    def ensure_customer_account(fb, uid: str, user: dict) -> None:
        if not fb or not fb.is_ready() or not uid:
            return

        profile = UserService.get_profile(fb, uid)
        if (profile.get("role") or "").strip().upper() == "ADMIN":
            return

        try:
            fb.db.collection("users").document(uid).set(
                {
                    "id": uid,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "role": "USER",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                merge=True,
            )
        except GoogleAPICallError:
            return

    @staticmethod
    def get_active_membership(fb, uid: str) -> dict:
        profile = UserService.get_profile(fb, uid)
        membership = profile.get("active_membership")
        return membership if isinstance(membership, dict) else {}

    @staticmethod
    def get_ai_profile(fb, uid: str) -> dict:
        profile = UserService.get_profile(fb, uid)
        ai_profile = profile.get("ai_profile")
        return ai_profile if isinstance(ai_profile, dict) else {}

    @staticmethod
    def get_cart(fb, uid: str) -> list[str]:
        profile = UserService.get_profile(fb, uid)
        cart = profile.get("cart")
        if not isinstance(cart, list):
            return []
        return [str(product_id) for product_id in cart if product_id]

    @staticmethod
    def upsert_cart(fb, uid: str, product_ids: list[str]) -> None:
        if not fb or not fb.is_ready() or not uid:
            return

        safe_ids = [str(product_id) for product_id in product_ids if product_id]
        try:
            fb.db.collection("users").document(uid).set(
                {
                    "cart": safe_ids,
                    "cart_updated_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                merge=True,
            )
        except GoogleAPICallError:
            return

    @staticmethod
    def upsert_ai_profile(fb, uid: str, payload: dict) -> None:
        if not fb or not fb.is_ready():
            return

        safe = {
            "ai_profile": {
                "weight_kg": payload.get("weight_kg"),
                "height_cm": payload.get("height_cm"),
                "goal": (payload.get("goal") or "").strip(),
                "training_days": payload.get("training_days"),
                "level": (payload.get("level") or "").strip(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            fb.db.collection("users").document(uid).set(safe, merge=True)
        except GoogleAPICallError:
            return

    @staticmethod
    def profile_completion(profile: dict | None) -> dict:
        profile = profile or {}
        fields = [
            "full_name",
            "phone",
            "address_line1",
            "city",
            "country",
            "fitness_goal",
            "fitness_level",
        ]
        completed = [field for field in fields if profile.get(field)]
        missing = [field for field in fields if not profile.get(field)]
        percent = round((len(completed) / len(fields)) * 100)
        return {"percent": percent, "missing": missing}

    @staticmethod
    def get_saved_ai_plans(fb, uid: str) -> list[dict]:
        profile = UserService.get_profile(fb, uid)
        plans = profile.get("ai_saved_plans")
        return plans if isinstance(plans, list) else []

    @staticmethod
    def save_ai_plan(fb, uid: str, title: str, content: str) -> dict:
        if not fb or not fb.is_ready() or not uid:
            return {"ok": False, "message": "Plan storage is not available right now."}

        profile = UserService.get_profile(fb, uid)
        plans = profile.get("ai_saved_plans")
        plans = plans if isinstance(plans, list) else []
        now = datetime.now(timezone.utc).isoformat()
        plan = {
            "id": f"ai_plan_{len(plans) + 1}_{int(datetime.now(timezone.utc).timestamp())}",
            "title": (title or "Saved AI plan").strip(),
            "content": (content or "").strip(),
            "created_at": now,
        }

        if not plan["content"]:
            return {"ok": False, "message": "There is no AI plan to save yet."}

        plans.insert(0, plan)
        try:
            fb.db.collection("users").document(uid).set(
                {
                    "ai_saved_plans": plans[:8],
                    "updated_at": now,
                },
                merge=True,
            )
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the AI plan save."}

        return {"ok": True, "plan": plan}
