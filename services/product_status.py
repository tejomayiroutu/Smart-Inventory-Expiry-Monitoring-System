"""
Reusable "freshness" status for a product (UI + emails + scheduler).

Why a helper?
-----------
If we copy the same if/else logic into routes, templates, and email code, they will
drift apart (one place says "yellow" and another says "green"). One function keeps
behavior consistent — including the scheduler, which runs outside HTTP requests.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models.product import Product


def get_product_status(product: "Product", today: Optional[date] = None) -> Dict[str, Any]:
    """
    Classify a product for display and alerts.

    Date arithmetic (beginner mental model):
    - (date_a - date_b).days gives an integer number of days between two calendar dates.
    - Example: expiry 2026-05-20 minus today 2026-05-11 => 9 days left.

    Shelf-life percentage (only when manufacturing_date is set and valid):
    - total shelf life (days) = expiry_date - manufacturing_date
    - elapsed (days) = today - manufacturing_date
    - completion % = (elapsed / total) * 100  → 0% at manufacture day, 100% at expiry day

    We clamp % to [0, 100] so tiny floating errors or odd edge dates never break the UI.
    """
    if today is None:
        today = date.today()

    expiry = product.expiry_date
    days_left = (expiry - today).days

    # --- Shelf-life completion % (None = unknown / not applicable) ---
    percent_complete: Optional[float] = None
    mfg = getattr(product, "manufacturing_date", None)
    if mfg is not None and expiry is not None:
        total_days = (expiry - mfg).days
        if total_days > 0:
            elapsed_days = (today - mfg).days
            raw = (elapsed_days / total_days) * 100.0
            percent_complete = max(0.0, min(100.0, raw))
        # total_days <= 0: would divide by zero or invert meaning — skip percentage

    week_end = today + timedelta(days=7)

    # Priority 1 — RED: expired OR expiry within the next 7 days (inclusive)
    is_expired = expiry < today
    in_seven_day_window = today <= expiry <= week_end
    if is_expired or in_seven_day_window:
        return {
            "status": "RED",
            "badge": "danger",
            "percentage": percent_complete,
            "days_left": days_left,
        }

    # Priority 2–4 — need a real shelf %; without manufacturing_date → NORMAL
    if percent_complete is None:
        return {
            "status": "NORMAL",
            "badge": "secondary",
            "percentage": None,
            "days_left": days_left,
        }

    if percent_complete >= 95.0:
        return {
            "status": "YELLOW",
            "badge": "warning",
            "percentage": percent_complete,
            "days_left": days_left,
        }
    if percent_complete >= 50.0:
        return {
            "status": "GREEN",
            "badge": "success",
            "percentage": percent_complete,
            "days_left": days_left,
        }

    return {
        "status": "NORMAL",
        "badge": "secondary",
        "percentage": percent_complete,
        "days_left": days_left,
    }
