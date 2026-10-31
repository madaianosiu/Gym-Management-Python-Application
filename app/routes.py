from .blueprints.public import public_bp
from .blueprints.auth import auth_bp
from .blueprints.user import user_bp
from .blueprints.admin import admin_bp

def register_blueprints(app):
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(admin_bp, url_prefix="/admin")
