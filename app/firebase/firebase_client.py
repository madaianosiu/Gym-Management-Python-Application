import os
import firebase_admin
from firebase_admin import credentials, auth, firestore


class FirebaseClient:
    def __init__(self, enabled: bool = False, logger=None):
        self.enabled = enabled
        self.logger = logger
        self._app = None
        self._db = None
        self._last_error = None

    def init_app(self) -> bool:
        if not self.enabled:
            self._last_error = "Firebase is disabled (FIREBASE_ENABLED=0)."
            return False

        try:
            if firebase_admin._apps:
                self._app = firebase_admin.get_app()
            else:
                path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
                project_id = os.getenv("FIREBASE_PROJECT_ID", "")

                if not path:
                    raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_PATH is empty.")

                if not os.path.exists(path):
                    raise FileNotFoundError(f"Service account file not found: {path}")

                cred = credentials.Certificate(path)
                opts = {"projectId": project_id} if project_id else None
                self._app = firebase_admin.initialize_app(cred, opts)

            self._db = firestore.client()
            self._last_error = None
            return True

        except Exception as e:
            self._last_error = str(e)
            if self.logger:
                self.logger.exception("Firebase init failed: %s", e)
            return False

    def is_ready(self) -> bool:
        return self.enabled and self._app is not None

    def last_error(self) -> str | None:
        return self._last_error

    def verify_id_token(self, id_token: str) -> dict:
        return auth.verify_id_token(id_token)

    @property
    def db(self):
        return self._db