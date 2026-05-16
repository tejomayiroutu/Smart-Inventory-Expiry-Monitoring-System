"""Build and send (or print) freshness digest emails using Flask-Mail."""

from collections import defaultdict

from flask_mail import Message

from extensions import db, mail
from models.product import Product
from models.user import User
from services.expiry_service import expiry_window
from services.product_status import get_product_status


def _format_product_line(product):
    """One line per product for plain-text email."""
    st = get_product_status(product)
    cat = product.category.name if product.category else "-"
    pct = f"{st['percentage']:.1f}%" if st["percentage"] is not None else "n/a"
    return (
        f"  - {product.name} | expiry {product.expiry_date.isoformat()} "
        f"| days left {st['days_left']} | shelf {pct} | {st['status']} | qty {product.quantity} | {cat}"
    )


def _section_block(title, products):
    if not products:
        return ""
    lines = "\n".join(_format_product_line(p) for p in products)
    return f"{title}\n{lines}\n\n"


def _digest_for_user_products(products):
    """
    Split this user's products into RED / YELLOW / GREEN buckets using the same
    get_product_status() helper as the web UI (scheduler reuses business logic).
    """
    red, yellow, green = [], [], []
    for p in products:
        st = get_product_status(p)
        if st["status"] == "RED":
            red.append(p)
        elif st["status"] == "YELLOW":
            yellow.append(p)
        elif st["status"] == "GREEN":
            green.append(p)
    return red, yellow, green


def send_daily_expiry_digests(app):
    """
    Run inside Flask application context (see scheduler setup).

    Sends one email per user who has at least one RED, YELLOW, or GREEN product.
    NORMAL-only users are skipped (no noise).
    """
    with app.app_context():
        today, week_end = expiry_window()
        console = app.config.get("MAIL_CONSOLE", True)

        all_products = Product.query.order_by(Product.user_id, Product.expiry_date).all()
        by_user = defaultdict(list)
        for p in all_products:
            by_user[p.user_id].append(p)

        for user_id, plist in by_user.items():
            user = db.session.get(User, user_id)
            if user is None or not user.email:
                continue

            red, yellow, green = _digest_for_user_products(plist)
            if not (red or yellow or green):
                continue

            body_parts = [
                f"Hello,",
                f"",
                f"This is your Expiry Tracker digest for {today.isoformat()}.",
                f"(Critical expiry window on the dashboard is still through {week_end.isoformat()}.)",
                f"",
            ]
            body_parts.append(_section_block("RED ALERTS (95–100% shelf life used or expired/expiring within 7 days)", red))
            body_parts.append(_section_block("YELLOW ALERTS (50–95% shelf life used)", yellow))
            body_parts.append(_section_block("GREEN ALERTS (0–50% shelf life used)", green))
            body_parts.append("- Expiry Tracker")

            body = "\n".join(p for p in body_parts if p)
            n = len(red) + len(yellow) + len(green)
            subject = f"[Expiry Tracker] Freshness digest: {n} item(s) (R:{len(red)} Y:{len(yellow)} G:{len(green)})"

            msg = Message(
                subject=subject,
                recipients=[user.email],
                body=body,
            )

            if console:
                print("\n" + "=" * 72)
                print("[MAIL_CONSOLE] Email would be sent via SMTP if MAIL_CONSOLE=false")
                print(f"To: {user.email}")
                print(f"Subject: {subject}")
                print(body)
                print("=" * 72 + "\n")
            else:
                mail.send(msg)
