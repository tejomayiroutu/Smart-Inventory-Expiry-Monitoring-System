"""Small JSON API routes (kept separate from HTML product CRUD)."""

from flask import Blueprint, jsonify
from flask_login import login_required

from services.openfoodfacts import lookup_barcode

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/product-lookup/<barcode>", methods=["GET"])
@login_required
def product_lookup(barcode):
    """
    Proxy + parse Open Food Facts for the logged-in user.

    Returns JSON only (no HTML). The browser uses fetch() to read this and
    fill the add/edit product form.

    HTTP status is always 200 when the response body is JSON so the frontend
    can reliably parse { "success": true/false, ... } (login failures still 302).
    """
    result = lookup_barcode(barcode)
    return jsonify(result)
