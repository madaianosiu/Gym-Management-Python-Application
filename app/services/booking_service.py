from datetime import datetime, timezone
from uuid import uuid4

from google.api_core.exceptions import GoogleAPICallError


class BookingService:
    DEFAULT_CLASSES = [
        {
            "id": "strength-foundation",
            "name": "Strength Foundation",
            "coach": "Mara",
            "day": "Monday",
            "time": "18:00",
            "duration": "50 min",
            "level": "Beginner",
            "spots": 14,
        },
        {
            "id": "hiit-conditioning",
            "name": "HIIT Conditioning",
            "coach": "Alex",
            "day": "Wednesday",
            "time": "19:00",
            "duration": "45 min",
            "level": "Intermediate",
            "spots": 12,
        },
        {
            "id": "mobility-recovery",
            "name": "Mobility Recovery",
            "coach": "Ioana",
            "day": "Friday",
            "time": "17:30",
            "duration": "40 min",
            "level": "All levels",
            "spots": 16,
        },
    ]

    @staticmethod
    def get_classes():
        return [dict(item) for item in BookingService.DEFAULT_CLASSES]

    @staticmethod
    def get_class(class_id: str | None):
        if not class_id:
            return None

        normalized = str(class_id).strip().lower()
        for class_item in BookingService.get_classes():
            if normalized == class_item.get("id"):
                return class_item
        return None

    @staticmethod
    def list_user_bookings(fb, user_id: str) -> list[dict]:
        if not fb or not fb.is_ready() or not user_id:
            return []

        try:
            docs = fb.db.collection("bookings").where("user_id", "==", user_id).stream()
            bookings = [doc.to_dict() or {} for doc in docs]
        except GoogleAPICallError:
            return []

        return sorted(bookings, key=lambda item: item.get("created_at", ""), reverse=True)

    @staticmethod
    def create_booking(fb, user: dict, class_item: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Booking storage is not available right now."}

        user_id = user.get("id")
        if not user_id:
            return {"ok": False, "message": "You must be logged in to book a class."}

        existing = BookingService.list_user_bookings(fb, user_id)
        if any(item.get("class_id") == class_item.get("id") and item.get("status") == "BOOKED" for item in existing):
            return {"ok": False, "message": "You already booked this class."}

        now = datetime.now(timezone.utc).isoformat()
        booking_id = f"book_{uuid4().hex[:12]}"
        record = {
            "id": booking_id,
            "user_id": user_id,
            "user_email": user.get("email"),
            "user_name": user.get("full_name"),
            "class_id": class_item.get("id"),
            "class_name": class_item.get("name"),
            "coach": class_item.get("coach"),
            "day": class_item.get("day"),
            "time": class_item.get("time"),
            "duration": class_item.get("duration"),
            "level": class_item.get("level"),
            "status": "BOOKED",
            "created_at": now,
        }

        try:
            fb.db.collection("bookings").document(booking_id).set(record)
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the booking save."}

        return {"ok": True, "booking": record}
