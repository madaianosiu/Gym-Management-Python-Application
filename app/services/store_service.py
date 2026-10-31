from datetime import datetime, timezone
from uuid import uuid4

from google.api_core.exceptions import GoogleAPICallError


class StoreService:
    DEFAULT_PRODUCTS = [
        {
            "id": "whey-protein",
            "name": "Whey Protein",
            "price": 39,
            "tag": "Recovery",
            "description": "Clean protein blend for post-workout recovery and daily nutrition support.",
            "image": "img/store-protein.svg",
            "features": ["24g protein", "Smooth mix", "Gym+ favorite"],
        },
        {
            "id": "smart-shaker",
            "name": "Smart Shaker",
            "price": 14,
            "tag": "Essentials",
            "description": "Leak-resistant shaker with clean finish and easy carry design.",
            "image": "img/store-shaker.svg",
            "features": ["BPA-free", "Secure lid", "Easy to wash"],
        },
        {
            "id": "gym-cap",
            "name": "Performance Cap",
            "price": 22,
            "tag": "Apparel",
            "description": "Lightweight cap with a sport fit for training days and everyday wear.",
            "image": "img/store-cap.svg",
            "features": ["Breathable fit", "Adjustable strap", "Minimal look"],
        },
        {
            "id": "gym-tee",
            "name": "Training Tee",
            "price": 28,
            "tag": "Apparel",
            "description": "Soft athletic t-shirt built for movement, comfort, and a premium gym look.",
            "image": "img/store-shirt.svg",
            "features": ["Stretch fabric", "Clean cut", "All-day comfort"],
        },
        {
            "id": "training-gloves",
            "name": "Training Gloves",
            "price": 19,
            "tag": "Grip",
            "description": "Supportive gloves for stronger grip, comfort, and cleaner lifting sessions.",
            "image": "img/store-gloves.svg",
            "features": ["Better grip", "Palm support", "Secure feel"],
        },
    ]

    @staticmethod
    def _slugify(value: str) -> str:
        safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in (value or "").strip())
        while "--" in safe:
            safe = safe.replace("--", "-")
        return safe.strip("-")

    @staticmethod
    def _normalize_product(payload: dict, product_id: str | None = None) -> dict:
        features_raw = payload.get("features", [])
        if isinstance(features_raw, str):
            features = [item.strip() for item in features_raw.split(",") if item.strip()]
        else:
            features = [str(item).strip() for item in features_raw if str(item).strip()]

        image = (payload.get("image") or "").strip() or "img/store-shaker.svg"
        if image.startswith("/static/"):
            image = image.replace("/static/", "", 1)

        normalized_id = product_id or StoreService._slugify(payload.get("id") or payload.get("name") or uuid4().hex[:8])
        return {
            "id": normalized_id,
            "name": (payload.get("name") or "").strip(),
            "price": int(payload.get("price") or 0),
            "tag": (payload.get("tag") or "Essentials").strip(),
            "description": (payload.get("description") or "").strip(),
            "image": image,
            "features": features,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _safe_firestore_products(fb):
        if not fb or not fb.is_ready():
            return []

        try:
            docs = [doc.to_dict() or {} for doc in fb.db.collection("products").stream()]
        except GoogleAPICallError:
            return []

        return sorted(docs, key=lambda item: (item.get("name") or "").lower())

    @staticmethod
    def seed_defaults(fb):
        if not fb or not fb.is_ready():
            return False

        existing = StoreService._safe_firestore_products(fb)
        if existing:
            return False

        now = datetime.now(timezone.utc).isoformat()
        try:
            for product in StoreService.DEFAULT_PRODUCTS:
                record = {**product, "updated_at": now}
                fb.db.collection("products").document(product["id"]).set(record)
        except GoogleAPICallError:
            return False

        return True

    @staticmethod
    def get_products(fb=None):
        firestore_products = StoreService._safe_firestore_products(fb)
        if firestore_products:
            return firestore_products

        return [dict(product) for product in StoreService.DEFAULT_PRODUCTS]

    @staticmethod
    def get_product(product_key: str | None, fb=None):
        if not product_key:
            return None

        normalized = str(product_key).strip().lower()
        for product in StoreService.get_products(fb):
            product_id = str(product.get("id", "")).strip().lower()
            product_name = str(product.get("name", "")).strip().lower()
            if normalized in {product_id, product_name}:
                return product

        return None

    @staticmethod
    def get_products_by_ids(product_ids: list[str] | None, fb=None):
        if not product_ids:
            return []

        products = []
        for product_id in product_ids:
            product = StoreService.get_product(product_id, fb)
            if product:
                products.append(product)
        return products

    @staticmethod
    def cart_total(products: list[dict] | None):
        if not products:
            return 0
        return sum(int(product.get("price", 0)) for product in products)

    @staticmethod
    def create_product(fb, payload: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Product storage is not available right now."}

        normalized = StoreService._normalize_product(payload)
        if not normalized["name"] or normalized["price"] <= 0:
            return {"ok": False, "message": "Product name and price are required."}

        try:
            fb.db.collection("products").document(normalized["id"]).set(normalized)
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the product save."}

        return {"ok": True, "product": normalized}

    @staticmethod
    def update_product(fb, product_id: str, payload: dict) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Product storage is not available right now."}

        current = StoreService.get_product(product_id, fb)
        if not current:
            return {"ok": False, "message": "Product was not found."}

        merged = {**current, **payload}
        normalized = StoreService._normalize_product(merged, product_id=product_id)
        if not normalized["name"] or normalized["price"] <= 0:
            return {"ok": False, "message": "Product name and price are required."}

        try:
            fb.db.collection("products").document(product_id).set(normalized, merge=True)
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the product update."}

        return {"ok": True, "product": normalized}

    @staticmethod
    def delete_product(fb, product_id: str) -> dict:
        if not fb or not fb.is_ready():
            return {"ok": False, "message": "Product storage is not available right now."}

        try:
            fb.db.collection("products").document(product_id).delete()
        except GoogleAPICallError:
            return {"ok": False, "message": "Firebase rejected the product delete."}

        return {"ok": True}
