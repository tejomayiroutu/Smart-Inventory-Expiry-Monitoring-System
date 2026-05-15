"""
Call Open Food Facts (OFF) from the server and normalize fields for our API.

We use the standard JSON endpoint documented at:
https://openfoodfacts.github.io/openfoodfacts-server/api/

Why server-side?
---------------
The browser could call OFF directly, but then you hit CORS limits and you cannot
add shared parsing/validation in one place. Flask calls OFF, then returns JSON
your own frontend understands.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


OFF_PRODUCT_URL = "https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
# OFF asks clients to identify themselves (fair use).
USER_AGENT = "ExpiryTracker/1.0 (https://github.com/local/expiry-tracker; contact: local-dev)"


def _clean_str(value: Any, max_len: Optional[int] = None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if max_len is not None and len(text) > max_len:
        text = text[:max_len]
    return text


def _pick_product_name(product: Dict[str, Any]) -> str:
    """OFF uses different keys per locale; try a few safe fallbacks."""
    for key in ("product_name", "product_name_en", "generic_name", "generic_name_en"):
        name = _clean_str(product.get(key), 255)
        if name:
            return name
    return ""


def _pick_category(product: Dict[str, Any]) -> str:
    """
    Prefer human-readable 'categories' string; else derive from categories_tags.
    """
    raw = _clean_str(product.get("categories"), 120)
    if raw:
        # Often "en:Snacks, en:..." — take first segment and strip language prefix
        first = raw.split(",")[0].strip()
        first = re.sub(r"^[a-z]{2}:", "", first, flags=re.IGNORECASE).strip()
        return first[:120]

    tags = product.get("categories_tags") or []
    if isinstance(tags, list) and tags:
        tag = str(tags[0])
        tag = re.sub(r"^[a-z]{2}:", "", tag, flags=re.IGNORECASE).replace("-", " ").strip()
        return tag[:120]
    return ""


def lookup_barcode(barcode: str, timeout_sec: float = 12.0) -> Dict[str, Any]:
    """
    Return a dict suitable for JSON response:
    - On success: success True + name, brand, ingredients, category (strings, may be empty).
    - On failure: success False + error short code + message for logs/UI.
    """
    code = _clean_str(barcode, 128).replace(" ", "")
    if not code or len(code) < 4 or len(code) > 128:
        return {
            "success": False,
            "error": "invalid_barcode",
            "message": "Enter a barcode at least 4 characters (digits are typical).",
        }

    url = OFF_PRODUCT_URL.format(barcode=urllib.parse.quote(code, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "error": "http_error",
            "message": f"Open Food Facts returned HTTP {e.code}.",
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": "network_error",
            "message": "Could not reach Open Food Facts. Check your internet connection.",
        }
    except TimeoutError:
        return {
            "success": False,
            "error": "timeout",
            "message": "Open Food Facts did not respond in time.",
        }

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "bad_json",
            "message": "Could not read response from Open Food Facts.",
        }

    if not isinstance(data, dict):
        return {"success": False, "error": "unexpected", "message": "Unexpected response shape."}

    # OFF: status 1 = found, 0 = not found
    if int(str(data.get("status", 0) or 0)) != 1:
        return {
            "success": False,
            "error": "not_found",
            "message": "No product found for this barcode.",
        }

    product = data.get("product")
    if not isinstance(product, dict):
        return {
            "success": False,
            "error": "missing_product",
            "message": "Product data missing in response.",
        }

    name = _pick_product_name(product)
    brand = _clean_str(product.get("brands"), 255)
    ingredients = _clean_str(product.get("ingredients_text"))  # TEXT in DB; trim very long for JSON
    if len(ingredients) > 8000:
        ingredients = ingredients[:8000] + "…"
    category = _pick_category(product)

    return {
        "success": True,
        "name": name,
        "brand": brand,
        "ingredients": ingredients,
        "category": category,
    }
