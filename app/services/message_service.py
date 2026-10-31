from datetime import datetime, timezone
from uuid import uuid4

from google.api_core.exceptions import GoogleAPICallError


class MessageService:
    @staticmethod
    def create_message(fb, payload: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Messaging storage is not available right now."}

        name = (payload.get("name") or "").strip()
        email = (payload.get("email") or "").strip()
        message = (payload.get("message") or "").strip()

        if not name or not email or not message:
            return {"ok": False, "message": "All message fields are required."}

        message_id = f"msg_{uuid4().hex[:12]}"
        record = {
            "id": message_id,
            "name": name,
            "email": email,
            "message": message,
            "status": "NEW",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            fb.db.collection("messages").document(message_id).set(record)
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the message save."}

        return {"ok": True, "message": "Message sent successfully.", "record": record}

    @staticmethod
    def list_messages(fb) -> list[dict]:
        if not fb or not fb.is_ready():
            return []

        try:
            messages = [doc.to_dict() or {} for doc in fb.db.collection("messages").stream()]
        except GoogleAPICallError:
            return []

        return sorted(messages, key=lambda item: item.get("created_at", ""), reverse=True)

    @staticmethod
    def reply_to_message(fb, message_id: str, reply: str, status: str = "REPLIED") -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Messaging storage is not available right now."}

        cleaned_reply = (reply or "").strip()
        if not cleaned_reply:
            return {"ok": False, "message": "Reply message cannot be empty."}

        normalized_status = (status or "REPLIED").strip().upper()
        if normalized_status not in {"NEW", "IN_REVIEW", "REPLIED", "CLOSED"}:
            normalized_status = "REPLIED"

        try:
            fb.db.collection("messages").document(message_id).set(
                {
                    "admin_reply": cleaned_reply,
                    "status": normalized_status,
                    "replied_at": datetime.now(timezone.utc).isoformat(),
                },
                merge=True,
            )
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the message update."}

        return {"ok": True, "message": "Reply saved successfully."}
