import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

from .config import Config
from .routes import register_blueprints
from .firebase.firebase_client import FirebaseClient


def create_app(config_object=Config) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_object)

    _configure_logging(app)
    register_blueprints(app)

    firebase = FirebaseClient(
        enabled=app.config.get("FIREBASE_ENABLED", False),
        logger=app.logger
    )
    firebase.init_app()
    app.config["FIREBASE"] = firebase

    _register_error_handlers(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "env": app.config.get("ENV", "unknown")}

    return app


def _configure_logging(app: Flask) -> None:
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    app.logger.setLevel(log_level)

    if app.logger.handlers:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sh = logging.StreamHandler()
    sh.setLevel(log_level)
    sh.setFormatter(formatter)
    app.logger.addHandler(sh)

    logs_dir = os.path.join(os.getcwd(), "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
        fh = RotatingFileHandler(
            os.path.join(logs_dir, "app.log"),
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        app.logger.addHandler(fh)
    except Exception:
        pass


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Unhandled exception: %s", e)
        return render_template("errors/500.html"), 500