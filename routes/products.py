from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models.category import Category
from models.product import Product

bp = Blueprint("products", __name__)


def _product_owned_or_404(product_id):
    product = db.session.get(Product, product_id)
    if product is None or product.user_id != current_user.id:
        abort(404)
    return product


def _category_id_from_name(user_id, category_name):
    """Empty name → no category. Otherwise find or create a Category for this user."""
    name = (category_name or "").strip()[:120]
    if not name:
        return None
    existing = Category.query.filter_by(user_id=user_id, name=name).first()
    if existing:
        return existing.id
    cat = Category(user_id=user_id, name=name)
    db.session.add(cat)
    db.session.flush()
    return cat.id


def _parse_expiry_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_optional_date(value):
    """Empty string → None (optional field). Invalid format → sentinel object."""
    if not value or not str(value).strip():
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return False  # invalid


def _parse_quantity(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _optional_text(value, max_len):
    """Empty → None; otherwise strip and cap length for DB safety."""
    s = (value or "").strip()
    if not s:
        return None
    if max_len and len(s) > max_len:
        return s[:max_len]
    return s


@bp.route("/products")
@login_required
def list_products():
    items = (
        Product.query.filter_by(user_id=current_user.id)
        .order_by(Product.expiry_date.asc(), Product.name.asc())
        .all()
    )
    return render_template("products/list.html", products=items)


@bp.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        category_name = request.form.get("category_name") or ""
        barcode = _optional_text(request.form.get("barcode"), 128)
        brand = _optional_text(request.form.get("brand"), 255)
        ingredients = _optional_text(request.form.get("ingredients"), 65535)
        expiry_raw = request.form.get("expiry_date") or ""
        mfg_raw = request.form.get("manufacturing_date") or ""
        notes = (request.form.get("notes") or "").strip() or None

        errors = False
        if not name:
            flash("Product name is required.", "danger")
            errors = True

        expiry_date = _parse_expiry_date(expiry_raw)
        if expiry_date is None:
            flash("Please choose a valid expiry date.", "danger")
            errors = True

        manufacturing_date = _parse_optional_date(mfg_raw)
        if manufacturing_date is False:
            flash("Manufacturing date must be a valid date or left blank.", "danger")
            errors = True
        elif manufacturing_date is not None and expiry_date is not None and manufacturing_date > expiry_date:
            flash("Manufacturing date cannot be after the expiry date.", "danger")
            errors = True

        qty = _parse_quantity(request.form.get("quantity"))
        if qty is None or qty < 0:
            flash("Quantity must be a whole number zero or greater.", "danger")
            errors = True

        if errors:
            return render_template(
                "products/form.html",
                mode="add",
                product=None,
                form_name=name,
                form_category_name=category_name.strip(),
                form_barcode=request.form.get("barcode") or "",
                form_brand=request.form.get("brand") or "",
                form_ingredients=request.form.get("ingredients") or "",
                form_manufacturing_date=mfg_raw,
                form_expiry_date=expiry_raw,
                form_quantity=request.form.get("quantity") or "1",
                form_notes=request.form.get("notes") or "",
            )

        category_id = _category_id_from_name(current_user.id, category_name)
        product = Product(
            user_id=current_user.id,
            category_id=category_id,
            name=name,
            barcode=barcode,
            brand=brand,
            ingredients=ingredients,
            quantity=qty,
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            notes=notes,
        )
        db.session.add(product)
        db.session.commit()
        flash("Product added.", "success")
        return redirect(url_for("products.list_products"))

    return render_template(
        "products/form.html",
        mode="add",
        product=None,
        form_name="",
        form_category_name="",
        form_barcode="",
        form_brand="",
        form_ingredients="",
        form_manufacturing_date="",
        form_expiry_date="",
        form_quantity="1",
        form_notes="",
    )


@bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = _product_owned_or_404(product_id)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        category_name = request.form.get("category_name") or ""
        barcode = _optional_text(request.form.get("barcode"), 128)
        brand = _optional_text(request.form.get("brand"), 255)
        ingredients = _optional_text(request.form.get("ingredients"), 65535)
        expiry_raw = request.form.get("expiry_date") or ""
        mfg_raw = request.form.get("manufacturing_date") or ""
        notes = (request.form.get("notes") or "").strip() or None

        errors = False
        if not name:
            flash("Product name is required.", "danger")
            errors = True

        expiry_date = _parse_expiry_date(expiry_raw)
        if expiry_date is None:
            flash("Please choose a valid expiry date.", "danger")
            errors = True

        manufacturing_date = _parse_optional_date(mfg_raw)
        if manufacturing_date is False:
            flash("Manufacturing date must be a valid date or left blank.", "danger")
            errors = True
        elif manufacturing_date is not None and expiry_date is not None and manufacturing_date > expiry_date:
            flash("Manufacturing date cannot be after the expiry date.", "danger")
            errors = True

        qty = _parse_quantity(request.form.get("quantity"))
        if qty is None or qty < 0:
            flash("Quantity must be a whole number zero or greater.", "danger")
            errors = True

        if errors:
            return render_template(
                "products/form.html",
                mode="edit",
                product=product,
                form_name=name,
                form_category_name=category_name.strip(),
                form_barcode=request.form.get("barcode") or "",
                form_brand=request.form.get("brand") or "",
                form_ingredients=request.form.get("ingredients") or "",
                form_manufacturing_date=mfg_raw,
                form_expiry_date=expiry_raw,
                form_quantity=request.form.get("quantity") or "1",
                form_notes=request.form.get("notes") or "",
            )

        product.name = name
        product.category_id = _category_id_from_name(current_user.id, category_name)
        product.barcode = barcode
        product.brand = brand
        product.ingredients = ingredients
        product.manufacturing_date = manufacturing_date
        product.expiry_date = expiry_date
        product.quantity = qty
        product.notes = notes
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("products.list_products"))

    cat_name = product.category.name if product.category else ""
    mfg_val = product.manufacturing_date.isoformat() if product.manufacturing_date else ""
    return render_template(
        "products/form.html",
        mode="edit",
        product=product,
        form_name=product.name,
        form_category_name=cat_name,
        form_barcode=product.barcode or "",
        form_brand=product.brand or "",
        form_ingredients=product.ingredients or "",
        form_manufacturing_date=mfg_val,
        form_expiry_date=product.expiry_date.isoformat() if product.expiry_date else "",
        form_quantity=str(product.quantity),
        form_notes=product.notes or "",
    )


@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = _product_owned_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("products.list_products"))
