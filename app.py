from flask import Flask, render_template

from config import Config
from extensions import bcrypt, csrf, db, login_manager, mail, migrate
from routes.api import bp as api_bp
from routes.auth import bp as auth_bp
from routes.dashboard import bp as dashboard_bp
from routes.products import bp as products_bp
from services.scheduler import init_scheduler


@login_manager.user_loader
def load_user(user_id):
    """Tell Flask-Login how to load a user from the session cookie (user id)."""
    from models.user import User

    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models so SQLAlchemy knows about tables (needed for migrations).
    import models  # noqa: F401

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(dashboard_bp)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from services.product_status import get_product_status

    app.jinja_env.filters["product_status"] = get_product_status

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.cli.command("send-expiry-digest")
    def cli_send_expiry_digest():
        """Run the daily digest once (prints to terminal if MAIL_CONSOLE=true)."""
        from services.expiry_alerts import send_daily_expiry_digests

        send_daily_expiry_digests(app)

    init_scheduler(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
