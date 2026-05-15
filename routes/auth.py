from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from extensions import bcrypt, db
from models.user import User

bp = Blueprint("auth", __name__)


def _normalize_email(value):
    return (value or "").strip().lower()


def _safe_next_url(target):
    """Allow same-site relative paths or full URLs (used after login from @login_required)."""
    if not target:
        return False
    if target.startswith("/") and not target.startswith("//"):
        return True
    ref = urlparse(request.host_url)
    dest = urlparse(urljoin(request.host_url, target))
    return dest.scheme in ("http", "https") and ref.netloc == dest.netloc


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = _normalize_email(request.form.get("email"))
        password = request.form.get("password") or ""
        password_confirm = request.form.get("password_confirm") or ""

        if not email or "@" not in email:
            flash("Please enter a valid email address.", "danger")
            return render_template("auth/signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/signup.html")

        if password != password_confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/signup.html")

        if User.query.filter_by(email=email).first():
            flash("That email is already registered. Try logging in.", "warning")
            return render_template("auth/signup.html")

        user = User(
            email=email,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That email is already registered.", "warning")
            return render_template("auth/signup.html")

        login_user(user)
        flash("Account created. You are now logged in.", "success")
        return redirect(url_for("home"))

    return render_template("auth/signup.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = _normalize_email(request.form.get("email"))
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if user is None or not bcrypt.check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        login_user(user, remember=remember)
        flash("Logged in successfully.", "success")
        next_url = request.args.get("next")
        if next_url and _safe_next_url(next_url):
            return redirect(next_url)
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
