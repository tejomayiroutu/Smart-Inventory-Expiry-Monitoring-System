from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from extensions import db
from models.category import Category
from models.product import Product
from services.expiry_service import expiry_window, products_expired_for_user
from services.expiry_service import products_expiring_within_7_days_for_user

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def expiry_dashboard():
    """
    Snapshot for the logged-in user only:
    - "today" is the server's calendar date (same for everyone using this app).
    - Expired: expiry_date is strictly before today.
    - Soon: expiry is today through today+7 (still valid or borderline; not in expired).
    """
    today, week_end = expiry_window()
    uid = current_user.id

    expired_products = products_expired_for_user(uid)

    soon_products = products_expiring_within_7_days_for_user(uid)

    total_count = Product.query.filter(Product.user_id == uid).count()

    expired_count = len(expired_products)
    soon_count = len(soon_products)
    ok_count = max(0, total_count - expired_count - soon_count)

    # Category-wise: product count and total quantity per category (including uncategorized).
    grouped = (
        db.session.query(
            Product.category_id,
            func.count(Product.id).label("product_count"),
            func.coalesce(func.sum(Product.quantity), 0).label("qty_sum"),
        )
        .filter(Product.user_id == uid)
        .group_by(Product.category_id)
        .all()
    )

    category_labels = []
    category_product_counts = []
    category_qty_totals = []
    category_rows = []

    cat_ids = [row.category_id for row in grouped if row.category_id is not None]
    id_to_name = {}
    if cat_ids:
        for c in Category.query.filter(Category.id.in_(cat_ids), Category.user_id == current_user.id).all():
            id_to_name[c.id] = c.name

    for row in sorted(grouped, key=lambda r: (r.category_id is None, id_to_name.get(r.category_id, ""))):
        cid = row.category_id
        label = "Uncategorized" if cid is None else id_to_name.get(cid, "Unknown")
        category_labels.append(label)
        category_product_counts.append(int(row.product_count))
        category_qty_totals.append(int(row.qty_sum))
        category_rows.append(
            {
                "name": label,
                "product_count": int(row.product_count),
                "quantity_total": int(row.qty_sum),
            }
        )

    return render_template(
        "dashboard/expiry.html",
        today=today,
        week_end=week_end,
        total_count=total_count,
        expired_count=expired_count,
        soon_count=soon_count,
        ok_count=ok_count,
        expired_products=expired_products,
        soon_products=soon_products,
        category_rows=category_rows,
        chart_labels=category_labels,
        chart_product_counts=category_product_counts,
        chart_qty_totals=category_qty_totals,
    )
