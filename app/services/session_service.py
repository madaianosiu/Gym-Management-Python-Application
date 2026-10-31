from flask import session

class SessionService:
    @staticmethod
    def sign_in(user_dict: dict) -> None:
        session["user"] = user_dict

    @staticmethod
    def sign_out() -> None:
        session.pop("user", None)

    @staticmethod
    def current_user() -> dict | None:
        return session.get("user")