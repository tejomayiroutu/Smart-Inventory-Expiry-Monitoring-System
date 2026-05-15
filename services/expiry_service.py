"""
Shared expiry rules used by the dashboard and by scheduled email alerts.

Keeping date logic in one place avoids the dashboard and emails disagreeing
about what "expiring within 7 days" means.
"""
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Tuple

from models.product import Product


def expiry_window() -> Tuple[date, date]:
    """Return (today, week_end) where week_end is today + 7 days (inclusive window)."""
    today = date.today()
    week_end = today + timedelta(days=7)
    return today, week_end


def products_expired_for_user(user_id: int) -> List[Product]:
    today, _ = expiry_window()
    return (
        Product.query.filter(Product.user_id == user_id, Product.expiry_date < today)
        .order_by(Product.expiry_date.asc(), Product.name.asc())
        .all()
    )


def products_expiring_within_7_days_for_user(user_id: int) -> List[Product]:
    """Same rule as the dashboard 'soon' list: today <= expiry <= today+7."""
    today, week_end = expiry_window()
    return (
        Product.query.filter(
            Product.user_id == user_id,
            Product.expiry_date >= today,
            Product.expiry_date <= week_end,
        )
        .order_by(Product.expiry_date.asc(), Product.name.asc())
        .all()
    )


def soon_products_by_user_id() -> Dict[int, List[Product]]:
    """
    All products (any user) expiring within the next 7 days, grouped by owner.
    Used by the daily email job so we can send one digest per user.
    """
    today, week_end = expiry_window()
    rows = (
        Product.query.filter(
            Product.expiry_date >= today,
            Product.expiry_date <= week_end,
        )
        .order_by(Product.user_id, Product.expiry_date.asc(), Product.name.asc())
        .all()
    )
    grouped: Dict[int, List[Product]] = defaultdict(list)
    for p in rows:
        grouped[p.user_id].append(p)
    return dict(grouped)
