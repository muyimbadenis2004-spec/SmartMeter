#!/usr/bin/env python3

import os
import sys
from pathlib import Path

ROOT = Path("smartmart")

FILES = {}

# ============================================================
# requirements.txt
# ============================================================
FILES["requirements.txt"] = """Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Migrate==4.0.5
Werkzeug==3.0.1
SQLAlchemy-Utils==0.41.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0
reportlab==4.0.7
"""

# ============================================================
# config.py
# ============================================================
FILES["config.py"] = '''import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///smartmart.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    STORE_NAME = os.environ.get("STORE_NAME", "SmartMart")
    STORE_ADDRESS = os.environ.get("STORE_ADDRESS", "123 Market Street")
    STORE_PHONE = os.environ.get("STORE_PHONE", "+1 555 0100")
    STORE_TAX_RATE = float(os.environ.get("STORE_TAX_RATE", "0.16"))
    CURRENCY = os.environ.get("CURRENCY", "$")
    POINT_VALUE = 100


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
'''

# ============================================================
# models.py
# ============================================================
FILES["models.py"] = '''from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="cashier")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    @property
    def is_manager(self):
        return self.role in ("manager", "admin")

    @property
    def is_admin(self):
        return self.role == "admin"


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(200))


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    contact_name = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    barcode = db.Column(db.String(64), unique=True, index=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    cost = db.Column(db.Float, nullable=False, default=0.0)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    reorder_quantity = db.Column(db.Integer, default=20)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    taxable = db.Column(db.Boolean, default=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")
    supplier = db.relationship("Supplier")

    @property
    def low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def out_of_stock(self):
        return self.quantity <= 0

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "sku": self.sku,
            "barcode": self.barcode, "price": self.price, "cost": self.cost,
            "quantity": self.quantity, "reorder_level": self.reorder_level,
            "category": self.category.name if self.category else None,
            "supplier": self.supplier.name if self.supplier else None,
            "taxable": self.taxable, "low_stock": self.low_stock,
        }


class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), index=True)
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    loyalty_points = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "phone": self.phone,
            "email": self.email, "loyalty_points": self.loyalty_points,
            "total_spent": self.total_spent,
        }


class Shift(db.Model):
    __tablename__ = "shifts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    opening_float = db.Column(db.Float, default=0.0)
    closing_cash = db.Column(db.Float)
    expected_cash = db.Column(db.Float)
    difference = db.Column(db.Float)
    notes = db.Column(db.Text)

    user = db.relationship("User")


class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    subtotal = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    payment_method = db.Column(db.String(30), default="cash")
    amount_paid = db.Column(db.Float, default=0.0)
    change_given = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"))
    discount_code = db.Column(db.String(40))
    is_refund = db.Column(db.Boolean, default=False)
    refund_of_id = db.Column(db.Integer, db.ForeignKey("sales.id"))
    voided = db.Column(db.Boolean, default=False)
    voided_reason = db.Column(db.String(200))

    user = db.relationship("User", foreign_keys=[user_id])
    customer = db.relationship("Customer")
    items = db.relationship("SaleItem", backref="sale", cascade="all, delete-orphan",
                            foreign_keys="SaleItem.sale_id")

    def to_dict(self):
        return {
            "id": self.id, "timestamp": self.timestamp.isoformat(),
            "subtotal": self.subtotal, "discount": self.discount_amount,
            "tax": self.tax_amount, "total": self.total,
            "payment_method": self.payment_method,
            "cashier": self.user.username if self.user else None,
            "customer": self.customer.name if self.customer else None,
            "items": [i.to_dict() for i in self.items],
        }


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    product = db.relationship("Product")

    @property
    def subtotal(self):
        return self.quantity * self.unit_price - self.discount

    @property
    def profit(self):
        return self.subtotal - (self.quantity * (self.unit_cost or 0))

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.product.name if self.product else None,
            "sku": self.product.sku if self.product else None,
            "quantity": self.quantity, "unit_price": self.unit_price,
            "discount": self.discount, "subtotal": self.subtotal,
        }


class StockMovement(db.Model):
    __tablename__ = "stock_movements"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(60), nullable=False)
    reference = db.Column(db.String(80))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    note = db.Column(db.String(200))

    product = db.relationship("Product")
    user = db.relationship("User")


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    status = db.Column(db.String(20), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expected_at = db.Column(db.Date)
    received_at = db.Column(db.DateTime)
    total_cost = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    supplier = db.relationship("Supplier")
    items = db.relationship("PurchaseOrderItem", backref="po", cascade="all, delete-orphan")


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"
    id = db.Column(db.Integer, primary_key=True)
    po_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    product = db.relationship("Product")

    @property
    def subtotal(self):
        return self.quantity * self.unit_cost


class Discount(db.Model):
    __tablename__ = "discounts"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False)
    description = db.Column(db.String(120))
    kind = db.Column(db.String(10), default="percent")
    value = db.Column(db.Float, nullable=False)
    min_purchase = db.Column(db.Float, default=0.0)
    valid_from = db.Column(db.Date)
    valid_to = db.Column(db.Date)
    active = db.Column(db.Boolean, default=True)


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    category = db.Column(db.String(60), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(60), nullable=False)
    entity = db.Column(db.String(60))
    entity_id = db.Column(db.Integer)
    detail = db.Column(db.Text)
    ip = db.Column(db.String(45))

    user = db.relationship("User")
'''

# ============================================================
# utils.py
# ============================================================
FILES["utils.py"] = '''from datetime import date
from flask import current_app
from flask_login import current_user
from models import db, AuditLog, StockMovement, Shift


def fmt_money(v):
    cur = current_app.config.get("CURRENCY", "$")
    return f"{cur}{v or 0:,.2f}"


def log_action(action, entity=None, entity_id=None, detail=None, ip=None):
    db.session.add(AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action, entity=entity, entity_id=entity_id,
        detail=detail, ip=ip,
    ))


def apply_stock(product, change, reason, reference=None, note=None):
    product.quantity += change
    db.session.add(StockMovement(
        product_id=product.id, change=change, reason=reason,
        reference=reference, note=note,
        user_id=current_user.id if current_user.is_authenticated else None,
    ))


def get_open_shift(user_id):
    return Shift.query.filter_by(user_id=user_id, closed_at=None)\\
                      .order_by(Shift.opened_at.desc()).first()


def calc_tax(subtotal, taxable_items):
    rate = current_app.config.get("STORE_TAX_RATE", 0.0)
    taxable_subtotal = sum(i["qty"] * i["price"] for i in taxable_items)
    return round(taxable_subtotal * rate, 2), rate


def apply_discount(discount, subtotal):
    if not discount or not discount.active:
        return 0.0
    today = date.today()
    if discount.valid_from and today < discount.valid_from:
        return 0.0
    if discount.valid_to and today > discount.valid_to:
        return 0.0
    if subtotal < (discount.min_purchase or 0):
        return 0.0
    if discount.kind == "percent":
        return round(subtotal * (discount.value / 100.0), 2)
    return min(discount.value, subtotal)


def earn_points(customer, total):
    if not customer:
        return 0
    per = current_app.config.get("POINT_VALUE", 100)
    points = int(total // per)
    customer.loyalty_points = (customer.loyalty_points or 0) + points
    customer.total_spent = (customer.total_spent or 0) + total
    return points
'''

# ============================================================
# routes/__init__.py
# ============================================================
FILES["routes/__init__.py"] = ""

# ============================================================
# routes/decorators.py
# ============================================================
FILES["routes/decorators.py"] = '''from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def manager_required(fn):
    return role_required("manager", "admin")(fn)


def admin_required(fn):
    return role_required("admin")(fn)
'''

# ============================================================
# routes/auth.py
# ============================================================
FILES["routes/auth.py"] = '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from routes.decorators import admin_required
from utils import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(username=request.form["username"]).first()
        if u and u.active and u.check_password(request.form["password"]):
            login_user(u)
            log_action("login", "user", u.id, ip=request.remote_addr)
            db.session.commit()
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    log_action("logout", "user", current_user.id)
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/users")
@login_required
@admin_required
def users():
    return render_template("users.html", users=User.query.order_by(User.username).all())


@auth_bp.route("/users/add", methods=["POST"])
@login_required
@admin_required
def add_user():
    if User.query.filter_by(username=request.form["username"]).first():
        flash("Username already exists", "error")
        return redirect(url_for("auth.users"))
    u = User(username=request.form["username"],
             full_name=request.form.get("full_name", ""),
             role=request.form.get("role", "cashier"))
    u.set_password(request.form["password"])
    db.session.add(u)
    log_action("create_user", "user", detail=u.username)
    db.session.commit()
    flash("User created", "success")
    return redirect(url_for("auth.users"))


@auth_bp.route("/users/<int:uid>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(uid):
    u = User.query.get_or_404(uid)
    if u.id == current_user.id:
        flash("Cannot deactivate yourself", "error")
    else:
        u.active = not u.active
        log_action("toggle_user", "user", u.id, detail=f"active={u.active}")
        db.session.commit()
        flash("User updated", "success")
    return redirect(url_for("auth.users"))


@auth_bp.route("/users/<int:uid>/password", methods=["POST"])
@login_required
@admin_required
def reset_password(uid):
    u = User.query.get_or_404(uid)
    u.set_password(request.form["password"])
    log_action("reset_password", "user", u.id)
    db.session.commit()
    flash("Password reset", "success")
    return redirect(url_for("auth.users"))
'''

# ============================================================
# routes/products.py
# ============================================================
FILES["routes/products.py"] = '''import csv
import io
from flask import (Blueprint, render_template, request, redirect, url_for,
                   jsonify, flash, Response)
from flask_login import login_required
from models import db, Product, Category, Supplier
from routes.decorators import manager_required
from utils import log_action

products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("/")
@login_required
def list_products():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", type=int)
    query = Product.query.filter_by(active=True)
    if q:
        query = query.filter(
            Product.name.ilike(f"%{q}%") |
            Product.sku.ilike(f"%{q}%") |
            Product.barcode.ilike(f"%{q}%")
        )
    if cat:
        query = query.filter(Product.category_id == cat)
    return render_template("products.html",
                           products=query.order_by(Product.name).all(),
                           categories=Category.query.order_by(Category.name).all(),
                           suppliers=Supplier.query.filter_by(active=True).all(),
                           q=q, current_cat=cat)


@products_bp.route("/add", methods=["POST"])
@login_required
@manager_required
def add_product():
    p = Product(
        name=request.form["name"],
        sku=request.form["sku"],
        barcode=request.form.get("barcode") or None,
        price=float(request.form["price"]),
        cost=float(request.form.get("cost", 0)),
        quantity=int(request.form.get("quantity", 0)),
        reorder_level=int(request.form.get("reorder_level", 10)),
        reorder_quantity=int(request.form.get("reorder_quantity", 20)),
        category_id=request.form.get("category_id", type=int),
        supplier_id=request.form.get("supplier_id", type=int),
        taxable="taxable" in request.form,
    )
    db.session.add(p)
    try:
        db.session.flush()
        log_action("create_product", "product", p.id, detail=p.name)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("SKU or barcode already exists.", "error")
        return redirect(url_for("products.list_products"))
    flash("Product added", "success")
    return redirect(url_for("products.list_products"))


@products_bp.route("/<int:pid>/edit", methods=["POST"])
@login_required
@manager_required
def edit_product(pid):
    p = Product.query.get_or_404(pid)
    p.name = request.form["name"]
    p.sku = request.form["sku"]
    p.barcode = request.form.get("barcode") or None
    p.price = float(request.form["price"])
    p.cost = float(request.form.get("cost", 0))
    p.reorder_level = int(request.form.get("reorder_level", 10))
    p.reorder_quantity = int(request.form.get("reorder_quantity", 20))
    p.category_id = request.form.get("category_id", type=int)
    p.supplier_id = request.form.get("supplier_id", type=int)
    p.taxable = "taxable" in request.form
    log_action("edit_product", "product", p.id)
    db.session.commit()
    flash("Product updated", "success")
    return redirect(url_for("products.list_products"))


@products_bp.route("/<int:pid>/archive", methods=["POST"])
@login_required
@manager_required
def archive_product(pid):
    p = Product.query.get_or_404(pid)
    p.active = False
    log_action("archive_product", "product", p.id)
    db.session.commit()
    flash("Product archived", "success")
    return redirect(url_for("products.list_products"))


@products_bp.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "").strip()
    query = Product.query.filter_by(active=True)
    if q:
        query = query.filter(
            Product.name.ilike(f"%{q}%") |
            Product.barcode.ilike(f"%{q}%") |
            Product.sku.ilike(f"%{q}%")
        )
    return jsonify([p.to_dict() for p in query.limit(10).all()])


@products_bp.route("/api/barcode/<code>")
@login_required
def api_barcode(code):
    p = Product.query.filter_by(barcode=code, active=True).first()
    if not p:
        return jsonify({"error": "not found"}), 404
    return jsonify(p.to_dict())


@products_bp.route("/export.csv")
@login_required
@manager_required
def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "name", "sku", "barcode", "category", "supplier",
                "price", "cost", "quantity", "reorder_level"])
    for p in Product.query.order_by(Product.name).all():
        w.writerow([p.id, p.name, p.sku, p.barcode or "",
                    p.category.name if p.category else "",
                    p.supplier.name if p.supplier else "",
                    p.price, p.cost, p.quantity, p.reorder_level])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=products.csv"})


@products_bp.route("/categories", methods=["GET", "POST"])
@login_required
@manager_required
def categories():
    if request.method == "POST":
        db.session.add(Category(name=request.form["name"],
                                description=request.form.get("description", "")))
        db.session.commit()
        flash("Category added", "success")
        return redirect(url_for("products.categories"))
    return render_template("categories.html",
                           categories=Category.query.order_by(Category.name).all())


@products_bp.route("/categories/<int:cid>/delete", methods=["POST"])
@login_required
@manager_required
def delete_category(cid):
    c = Category.query.get_or_404(cid)
    if Product.query.filter_by(category_id=c.id).count():
        flash("Cannot delete: category is in use", "error")
    else:
        db.session.delete(c)
        db.session.commit()
        flash("Category deleted", "success")
    return redirect(url_for("products.categories"))
'''

# ============================================================
# routes/suppliers.py
# ============================================================
FILES["routes/suppliers.py"] = '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Supplier
from routes.decorators import manager_required
from utils import log_action

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


@suppliers_bp.route("/")
@login_required
@manager_required
def index():
    return render_template("suppliers.html",
                           suppliers=Supplier.query.order_by(Supplier.name).all())


@suppliers_bp.route("/add", methods=["POST"])
@login_required
@manager_required
def add():
    s = Supplier(
        name=request.form["name"],
        contact_name=request.form.get("contact_name", ""),
        phone=request.form.get("phone", ""),
        email=request.form.get("email", ""),
        address=request.form.get("address", ""),
        notes=request.form.get("notes", ""),
    )
    db.session.add(s)
    db.session.flush()
    log_action("create_supplier", "supplier", s.id, detail=s.name)
    db.session.commit()
    flash("Supplier added", "success")
    return redirect(url_for("suppliers.index"))


@suppliers_bp.route("/<int:sid>/edit", methods=["POST"])
@login_required
@manager_required
def edit(sid):
    s = Supplier.query.get_or_404(sid)
    s.name = request.form["name"]
    s.contact_name = request.form.get("contact_name", "")
    s.phone = request.form.get("phone", "")
    s.email = request.form.get("email", "")
    s.address = request.form.get("address", "")
    s.notes = request.form.get("notes", "")
    db.session.commit()
    flash("Supplier updated", "success")
    return redirect(url_for("suppliers.index"))
'''

# ============================================================
# routes/purchases.py
# ============================================================
FILES["routes/purchases.py"] = '''from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, PurchaseOrder, PurchaseOrderItem, Product, Supplier
from routes.decorators import manager_required
from utils import apply_stock, log_action

purchases_bp = Blueprint("purchases", __name__, url_prefix="/purchases")


@purchases_bp.route("/")
@login_required
@manager_required
def index():
    pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return render_template("purchases.html", pos=pos,
                           suppliers=Supplier.query.filter_by(active=True).all())


@purchases_bp.route("/new", methods=["POST"])
@login_required
@manager_required
def new():
    po = PurchaseOrder(
        supplier_id=request.form.get("supplier_id", type=int),
        status="draft",
        expected_at=datetime.strptime(request.form["expected_at"], "%Y-%m-%d").date()
                    if request.form.get("expected_at") else None,
        notes=request.form.get("notes", ""),
        user_id=current_user.id,
    )
    db.session.add(po)
    db.session.flush()
    log_action("create_po", "po", po.id)
    db.session.commit()
    return redirect(url_for("purchases.detail", po_id=po.id))


@purchases_bp.route("/<int:po_id>")
@login_required
@manager_required
def detail(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template("purchase_detail.html", po=po, products=products)


@purchases_bp.route("/<int:po_id>/add_item", methods=["POST"])
@login_required
@manager_required
def add_item(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status != "draft":
        flash("Cannot modify a submitted PO", "error")
        return redirect(url_for("purchases.detail", po_id=po.id))
    pid = request.form.get("product_id", type=int)
    qty = int(request.form["quantity"])
    cost = float(request.form["unit_cost"])
    db.session.add(PurchaseOrderItem(po_id=po.id, product_id=pid,
                                     quantity=qty, unit_cost=cost))
    db.session.commit()
    _recalc_total(po)
    return redirect(url_for("purchases.detail", po_id=po.id))


@purchases_bp.route("/<int:po_id>/remove_item/<int:item_id>", methods=["POST"])
@login_required
@manager_required
def remove_item(po_id, item_id):
    item = PurchaseOrderItem.query.get_or_404(item_id)
    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status != "draft":
        flash("Cannot modify a submitted PO", "error")
    else:
        db.session.delete(item)
        db.session.commit()
        _recalc_total(po)
    return redirect(url_for("purchases.detail", po_id=po.id))


@purchases_bp.route("/<int:po_id>/submit", methods=["POST"])
@login_required
@manager_required
def submit(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not po.items:
        flash("Add items first", "error")
    else:
        po.status = "ordered"
        log_action("submit_po", "po", po.id)
        db.session.commit()
        flash("PO submitted to supplier", "success")
    return redirect(url_for("purchases.detail", po_id=po.id))


@purchases_bp.route("/<int:po_id>/receive", methods=["POST"])
@login_required
@manager_required
def receive(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status != "ordered":
        flash("Only ordered POs can be received", "error")
        return redirect(url_for("purchases.detail", po_id=po.id))

    for item in po.items:
        product = item.product
        product.cost = item.unit_cost
        apply_stock(product, item.quantity, "po", reference=f"po:{po.id}")
    po.status = "received"
    po.received_at = datetime.utcnow()
    log_action("receive_po", "po", po.id)
    db.session.commit()
    flash("PO received, stock updated", "success")
    return redirect(url_for("purchases.detail", po_id=po.id))


@purchases_bp.route("/<int:po_id>/cancel", methods=["POST"])
@login_required
@manager_required
def cancel(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status == "received":
        flash("Cannot cancel a received PO", "error")
    else:
        po.status = "cancelled"
        log_action("cancel_po", "po", po.id)
        db.session.commit()
        flash("PO cancelled", "success")
    return redirect(url_for("purchases.detail", po_id=po.id))


def _recalc_total(po):
    po.total_cost = sum(i.quantity * i.unit_cost for i in po.items)
    db.session.commit()
'''

# ============================================================
# routes/customers.py
# ============================================================
FILES["routes/customers.py"] = '''from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db, Customer, Sale
from utils import log_action

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


@customers_bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    query = Customer.query
    if q:
        query = query.filter(
            Customer.name.ilike(f"%{q}%") |
            Customer.phone.ilike(f"%{q}%") |
            Customer.email.ilike(f"%{q}%")
        )
    return render_template("customers.html", customers=query.order_by(Customer.name).all(), q=q)


@customers_bp.route("/add", methods=["POST"])
@login_required
def add():
    c = Customer(
        name=request.form["name"],
        phone=request.form.get("phone", ""),
        email=request.form.get("email", ""),
        address=request.form.get("address", ""),
    )
    db.session.add(c)
    db.session.flush()
    log_action("create_customer", "customer", c.id, detail=c.name)
    db.session.commit()
    flash("Customer added", "success")
    return redirect(url_for("customers.index"))


@customers_bp.route("/<int:cid>")
@login_required
def detail(cid):
    c = Customer.query.get_or_404(cid)
    sales = Sale.query.filter_by(customer_id=c.id).order_by(Sale.timestamp.desc()).limit(50).all()
    return render_template("customer_detail.html", customer=c, sales=sales)


@customers_bp.route("/api/search")
@login_required
def api_search():
    q = request.args.get("q", "").strip()
    query = Customer.query
    if q:
        query = query.filter(
            Customer.name.ilike(f"%{q}%") | Customer.phone.ilike(f"%{q}%")
        )
    return jsonify([c.to_dict() for c in query.limit(10).all()])
'''

# ============================================================
# routes/sales.py
# ============================================================
FILES["routes/sales.py"] = '''import csv
import io
from datetime import datetime
from flask import (Blueprint, render_template, request, jsonify, flash,
                   redirect, url_for, Response)
from flask_login import login_required, current_user
from models import db, Sale, SaleItem, Product, Customer, Discount
from routes.decorators import manager_required
from utils import (apply_stock, log_action, get_open_shift, calc_tax,
                   apply_discount, earn_points)

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


@sales_bp.route("/")
@login_required
def pos():
    discount_codes = Discount.query.filter_by(active=True).all()
    return render_template("sales.html", discount_codes=discount_codes,
                           shift=get_open_shift(current_user.id))


@sales_bp.route("/api/checkout", methods=["POST"])
@login_required
def checkout():
    data = request.get_json() or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"error": "Cart is empty"}), 400

    shift = get_open_shift(current_user.id)
    if not shift:
        return jsonify({"error": "No open shift. Please open a shift first."}), 400

    customer = None
    if data.get("customer_id"):
        customer = Customer.query.get(data["customer_id"])

    discount = None
    if data.get("discount_code"):
        discount = Discount.query.filter_by(code=data["discount_code"], active=True).first()

    sale = Sale(
        payment_method=data.get("payment_method", "cash"),
        user_id=current_user.id,
        customer_id=customer.id if customer else None,
        shift_id=shift.id,
        discount_code=discount.code if discount else None,
    )
    db.session.add(sale)

    subtotal = 0.0
    taxable_items = []
    for line in items:
        product = Product.query.get(line["product_id"])
        if not product or not product.active:
            db.session.rollback()
            return jsonify({"error": f"Product {line['product_id']} not found"}), 404
        qty = int(line["quantity"])
        if qty <= 0:
            db.session.rollback()
            return jsonify({"error": "Quantity must be positive"}), 400
        if product.quantity < qty:
            db.session.rollback()
            return jsonify({"error": f"Insufficient stock for {product.name}"}), 400

        line_discount = float(line.get("discount", 0) or 0)
        item = SaleItem(sale=sale, product_id=product.id, quantity=qty,
                        unit_price=product.price, unit_cost=product.cost,
                        discount=line_discount)
        db.session.add(item)

        apply_stock(product, -qty, "sale", reference="sale")
        subtotal += qty * product.price - line_discount
        if product.taxable:
            taxable_items.append({"qty": qty, "price": product.price})

    tax_amount, _rate = calc_tax(subtotal, taxable_items)
    discount_amount = apply_discount(discount, subtotal)
    total = round(subtotal - discount_amount + tax_amount, 2)

    sale.subtotal = round(subtotal, 2)
    sale.discount_amount = round(discount_amount, 2)
    sale.tax_amount = round(tax_amount, 2)
    sale.total = total

    paid = float(data.get("amount_paid", total) or total)
    sale.amount_paid = paid
    sale.change_given = round(paid - total, 2) if paid > total else 0.0

    if customer:
        earn_points(customer, total)

    log_action("sale", "sale", sale.id, detail=f"total={total}")
    db.session.commit()

    return jsonify({"sale_id": sale.id, "total": sale.total,
                    "subtotal": sale.subtotal, "tax": sale.tax_amount,
                    "discount": sale.discount_amount,
                    "change": sale.change_given,
                    "receipt_url": url_for("sales.receipt", sid=sale.id)})


@sales_bp.route("/history")
@login_required
def history():
    q = request.args.get("q", "").strip()
    query = Sale.query
    if q.isdigit():
        query = query.filter(Sale.id == int(q))
    sales = query.order_by(Sale.timestamp.desc()).limit(200).all()
    return render_template("sales.html", sales=sales, show_history=True, q=q)


@sales_bp.route("/<int:sid>/receipt")
@login_required
def receipt(sid):
    sale = Sale.query.get_or_404(sid)
    return render_template("receipt.html", sale=sale, now=datetime.utcnow())


@sales_bp.route("/<int:sid>/receipt.pdf")
@login_required
def receipt_pdf(sid):
    from reportlab.lib.pagesizes import A6
    from reportlab.pdfgen import canvas
    from io import BytesIO
    from flask import current_app

    sale = Sale.query.get_or_404(sid)
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A6)
    width, height = A6
    y = height - 30
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, y, current_app.config["STORE_NAME"])
    y -= 16
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, current_app.config["STORE_ADDRESS"])
    y -= 12
    c.drawCentredString(width / 2, y, current_app.config["STORE_PHONE"])
    y -= 18
    c.drawString(20, y, f"Receipt #{sale.id}")
    c.drawRightString(width - 20, y, sale.timestamp.strftime("%Y-%m-%d %H:%M"))
    y -= 14
    c.drawString(20, y, f"Cashier: {sale.user.username if sale.user else '-'}")
    y -= 12
    c.drawString(20, y, f"Payment: {sale.payment_method}")
    if sale.customer:
        y -= 12
        c.drawString(20, y, f"Customer: {sale.customer.name}")
    y -= 16
    c.line(20, y, width - 20, y)
    y -= 12
    for it in sale.items:
        c.drawString(20, y, f"{it.product.name[:26]}")
        y -= 11
        c.drawString(26, y, f"{it.quantity} x {it.unit_price:.2f}")
        c.drawRightString(width - 20, y, f"{it.subtotal:.2f}")
        y -= 13
        if y < 60:
            c.showPage(); y = height - 30
    c.line(20, y, width - 20, y)
    y -= 12
    c.drawString(20, y, "Subtotal");       c.drawRightString(width - 20, y, f"{sale.subtotal:.2f}"); y -= 11
    if sale.discount_amount:
        c.drawString(20, y, "Discount");   c.drawRightString(width - 20, y, f"-{sale.discount_amount:.2f}"); y -= 11
    c.drawString(20, y, "Tax");            c.drawRightString(width - 20, y, f"{sale.tax_amount:.2f}"); y -= 11
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20, y, "TOTAL");          c.drawRightString(width - 20, y, f"{sale.total:.2f}"); y -= 16
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, y, "Thank you!")
    c.showPage()
    c.save()
    buf.seek(0)
    return Response(buf.getvalue(), mimetype="application/pdf",
                    headers={"Content-Disposition": f"inline; filename=receipt_{sale.id}.pdf"})


@sales_bp.route("/<int:sid>/refund", methods=["POST"])
@login_required
@manager_required
def refund(sid):
    original = Sale.query.get_or_404(sid)
    if original.is_refund or original.voided:
        flash("This sale cannot be refunded", "error")
        return redirect(url_for("sales.history"))

    shift = get_open_shift(current_user.id)
    refund_sale = Sale(
        payment_method=original.payment_method,
        user_id=current_user.id,
        customer_id=original.customer_id,
        shift_id=shift.id if shift else None,
        is_refund=True,
        refund_of_id=original.id,
        subtotal=-original.subtotal,
        discount_amount=-original.discount_amount,
        tax_amount=-original.tax_amount,
        total=-original.total,
        amount_paid=-original.total,
    )
    db.session.add(refund_sale)
    for it in original.items:
        db.session.add(SaleItem(sale=refund_sale, product_id=it.product_id,
                                quantity=-it.quantity, unit_price=it.unit_price,
                                unit_cost=it.unit_cost, discount=-it.discount))
        apply_stock(it.product, it.quantity, "return", reference=f"sale:{original.id}")

    if original.customer:
        pts = int(original.total // 100)
        original.customer.loyalty_points = max(0, (original.customer.loyalty_points or 0) - pts)
        original.customer.total_spent = max(0, (original.customer.total_spent or 0) - original.total)

    log_action("refund", "sale", refund_sale.id, detail=f"of sale {original.id}")
    db.session.commit()
    flash("Refund processed", "success")
    return redirect(url_for("sales.receipt", sid=refund_sale.id))


@sales_bp.route("/<int:sid>/void", methods=["POST"])
@login_required
@manager_required
def void(sid):
    sale = Sale.query.get_or_404(sid)
    if sale.voided:
        flash("Already voided", "error")
        return redirect(url_for("sales.history"))
    for it in sale.items:
        apply_stock(it.product, it.quantity, "adjust",
                    reference=f"void:{sale.id}", note="Sale voided")
    sale.voided = True
    sale.voided_reason = request.form.get("reason", "")
    log_action("void_sale", "sale", sale.id)
    db.session.commit()
    flash("Sale voided", "success")
    return redirect(url_for("sales.history"))


@sales_bp.route("/export.csv")
@login_required
@manager_required
def export_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["sale_id", "timestamp", "cashier", "customer", "payment",
                "product", "sku", "qty", "unit_price", "discount", "subtotal",
                "sale_subtotal", "tax", "sale_total", "refund", "voided"])
    for s in Sale.query.order_by(Sale.timestamp).all():
        for it in s.items:
            w.writerow([s.id, s.timestamp.isoformat(),
                        s.user.username if s.user else "",
                        s.customer.name if s.customer else "",
                        s.payment_method,
                        it.product.name, it.product.sku, it.quantity,
                        f"{it.unit_price:.2f}", f"{it.discount:.2f}",
                        f"{it.subtotal:.2f}",
                        f"{s.subtotal:.2f}", f"{s.tax_amount:.2f}", f"{s.total:.2f}",
                        s.is_refund, s.voided])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=sales.csv"})
'''

# ============================================================
# routes/shifts.py
# ============================================================
FILES["routes/shifts.py"] = '''from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, Shift, Sale
from utils import get_open_shift, log_action

shifts_bp = Blueprint("shifts", __name__, url_prefix="/shifts")


@shifts_bp.route("/")
@login_required
def index():
    open_shift = get_open_shift(current_user.id)
    history = Shift.query.filter_by(user_id=current_user.id)\\
                         .order_by(Shift.opened_at.desc()).limit(30).all()
    return render_template("shifts.html", open_shift=open_shift, history=history)


@shifts_bp.route("/open", methods=["POST"])
@login_required
def open_shift():
    if get_open_shift(current_user.id):
        flash("A shift is already open", "error")
        return redirect(url_for("shifts.index"))
    s = Shift(user_id=current_user.id,
              opening_float=float(request.form.get("opening_float", 0)))
    db.session.add(s)
    log_action("open_shift", "shift", detail=f"float={s.opening_float}")
    db.session.commit()
    flash("Shift opened", "success")
    return redirect(url_for("sales.pos"))


@shifts_bp.route("/close", methods=["POST"])
@login_required
def close_shift():
    s = get_open_shift(current_user.id)
    if not s:
        flash("No open shift", "error")
        return redirect(url_for("shifts.index"))

    cash_sales = db.session.query(func.coalesce(func.sum(Sale.total), 0.0))\\
        .filter(Sale.shift_id == s.id, Sale.payment_method == "cash",
                Sale.voided == False, Sale.is_refund == False).scalar()

    expected = s.opening_float + cash_sales
    closing = float(request.form.get("closing_cash", 0))

    s.closed_at = datetime.utcnow()
    s.closing_cash = closing
    s.expected_cash = round(expected, 2)
    s.difference = round(closing - expected, 2)
    s.notes = request.form.get("notes", "")

    log_action("close_shift", "shift", s.id,
               detail=f"expected={expected:.2f} counted={closing:.2f}")
    db.session.commit()
    flash(f"Shift closed. Difference: {s.difference:+.2f}", "success")
    return redirect(url_for("shifts.index"))
'''

# ============================================================
# routes/discounts.py
# ============================================================
FILES["routes/discounts.py"] = '''from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Discount
from routes.decorators import manager_required
from utils import log_action

discounts_bp = Blueprint("discounts", __name__, url_prefix="/discounts")


@discounts_bp.route("/", methods=["GET", "POST"])
@login_required
@manager_required
def index():
    if request.method == "POST":
        try:
            d = Discount(
                code=request.form["code"].upper(),
                description=request.form.get("description", ""),
                kind=request.form.get("kind", "percent"),
                value=float(request.form["value"]),
                min_purchase=float(request.form.get("min_purchase", 0) or 0),
                valid_from=datetime.strptime(request.form["valid_from"], "%Y-%m-%d").date()
                           if request.form.get("valid_from") else None,
                valid_to=datetime.strptime(request.form["valid_to"], "%Y-%m-%d").date()
                         if request.form.get("valid_to") else None,
            )
            db.session.add(d)
            log_action("create_discount", "discount", detail=d.code)
            db.session.commit()
            flash("Discount created", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "error")
        return redirect(url_for("discounts.index"))
    return render_template("discounts.html",
                           discounts=Discount.query.order_by(Discount.code).all())


@discounts_bp.route("/<int:did>/toggle", methods=["POST"])
@login_required
@manager_required
def toggle(did):
    d = Discount.query.get_or_404(did)
    d.active = not d.active
    db.session.commit()
    return redirect(url_for("discounts.index"))
'''

# ============================================================
# routes/stock.py
# ============================================================
FILES["routes/stock.py"] = '''from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import db, Product, StockMovement
from routes.decorators import manager_required
from utils import apply_stock, log_action

stock_bp = Blueprint("stock", __name__, url_prefix="/stock")


@stock_bp.route("/")
@login_required
def index():
    products = Product.query.filter_by(active=True).order_by(Product.quantity).all()
    low = [p for p in products if p.low_stock]
    return render_template("stock.html", products=products, low=low)


@stock_bp.route("/movements")
@login_required
@manager_required
def movements():
    product_id = request.args.get("product_id", type=int)
    query = StockMovement.query
    if product_id:
        query = query.filter_by(product_id=product_id)
    moves = query.order_by(StockMovement.timestamp.desc()).limit(300).all()
    return render_template("stock_movements.html", movements=moves,
                           products=Product.query.order_by(Product.name).all(),
                           current_product=product_id)


@stock_bp.route("/restock/<int:pid>", methods=["POST"])
@login_required
@manager_required
def restock(pid):
    p = Product.query.get_or_404(pid)
    amount = int(request.form["amount"])
    if amount <= 0:
        flash("Amount must be positive", "error")
    else:
        apply_stock(p, amount, "restock", note=request.form.get("note", ""))
        log_action("restock", "product", p.id, detail=f"+{amount}")
        db.session.commit()
        flash(f"Restocked {p.name} by {amount}", "success")
    return redirect(url_for("stock.index"))


@stock_bp.route("/adjust/<int:pid>", methods=["POST"])
@login_required
@manager_required
def adjust(pid):
    p = Product.query.get_or_404(pid)
    new_qty = int(request.form["quantity"])
    delta = new_qty - p.quantity
    if delta == 0:
        flash("No change", "error")
    else:
        apply_stock(p, delta, "adjust", note=request.form.get("note", ""))
        log_action("adjust_stock", "product", p.id, detail=f"{delta:+d}")
        db.session.commit()
        flash("Stock adjusted", "success")
    return redirect(url_for("stock.index"))
'''

# ============================================================
# routes/finance.py
# ============================================================
FILES["routes/finance.py"] = '''from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required
from sqlalchemy import func
from models import db, Expense, Sale, SaleItem
from routes.decorators import manager_required
from utils import log_action
import csv, io

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")


@finance_bp.route("/", methods=["GET", "POST"])
@login_required
@manager_required
def index():
    if request.method == "POST":
        e = Expense(
            date=datetime.strptime(request.form["date"], "%Y-%m-%d").date(),
            category=request.form["category"],
            amount=float(request.form["amount"]),
            note=request.form.get("note", ""),
        )
        db.session.add(e)
        log_action("add_expense", "expense", detail=f"{e.category} {e.amount}")
        db.session.commit()
        flash("Expense recorded", "success")
        return redirect(url_for("finance.index"))

    today = date.today()
    month_start = today.replace(day=1)

    revenue = db.session.query(func.coalesce(func.sum(Sale.total), 0.0))\\
        .filter(Sale.timestamp >= month_start,
                Sale.voided == False, Sale.is_refund == False).scalar()
    refunds = db.session.query(func.coalesce(func.sum(Sale.total), 0.0))\\
        .filter(Sale.timestamp >= month_start, Sale.is_refund == True).scalar()
    cogs = db.session.query(
        func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_cost), 0.0)
    ).join(Sale, Sale.id == SaleItem.sale_id)\\
     .filter(Sale.timestamp >= month_start,
             Sale.voided == False, Sale.is_refund == False).scalar()

    expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0.0))\\
        .filter(Expense.date >= month_start).scalar()
    gross_profit = revenue - cogs
    net_profit = gross_profit - expenses

    recent = Expense.query.order_by(Expense.date.desc()).limit(20).all()
    return render_template("finance.html",
                           revenue=revenue, refunds=refunds, cogs=cogs,
                           gross_profit=gross_profit, expenses=expenses,
                           net_profit=net_profit, recent=recent, today=today)


@finance_bp.route("/expenses.csv")
@login_required
@manager_required
def expenses_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "category", "amount", "note"])
    for e in Expense.query.order_by(Expense.date).all():
        w.writerow([e.date, e.category, f"{e.amount:.2f}", e.note])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=expenses.csv"})
'''

# ============================================================
# routes/reports.py
# ============================================================
FILES["routes/reports.py"] = '''import csv
import io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required
from sqlalchemy import func
from models import db, Sale, SaleItem, Product, Customer
from routes.decorators import manager_required

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _date_range(days):
    return datetime.utcnow() - timedelta(days=days)


@reports_bp.route("/")
@login_required
@manager_required
def index():
    days = int(request.args.get("days", 7))
    since = _date_range(days)

    daily = db.session.query(
        func.date(Sale.timestamp).label("day"),
        func.sum(Sale.total).label("total"),
        func.count(Sale.id).label("count")
    ).filter(Sale.timestamp >= since, Sale.voided == False)\\
     .group_by("day").order_by("day").all()

    top = db.session.query(
        Product.name, func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.quantity * SaleItem.unit_price).label("revenue")
    ).join(SaleItem, SaleItem.product_id == Product.id)\\
     .join(Sale, Sale.id == SaleItem.sale_id)\\
     .filter(Sale.timestamp >= since, Sale.voided == False,
             Sale.is_refund == False)\\
     .group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc())\\
     .limit(10).all()

    by_payment = db.session.query(
        Sale.payment_method,
        func.sum(Sale.total).label("total"),
        func.count(Sale.id).label("count")
    ).filter(Sale.timestamp >= since, Sale.voided == False)\\
     .group_by(Sale.payment_method).all()

    low_stock = Product.query.filter(Product.active == True,
                                     Product.quantity <= Product.reorder_level).all()
    stock_value = db.session.query(
        func.coalesce(func.sum(Product.quantity * Product.cost), 0.0)
    ).filter(Product.active == True).scalar()

    top_customers = db.session.query(
        Customer.name, Customer.total_spent, Customer.loyalty_points
    ).order_by(Customer.total_spent.desc()).limit(10).all()

    return render_template("reports.html",
                           daily=[{"day": str(d.day), "total": d.total, "count": d.count} for d in daily],
                           top=top, by_payment=by_payment,
                           low_stock=low_stock, stock_value=stock_value,
                           top_customers=top_customers, days=days)


@reports_bp.route("/api/daily")
@login_required
@manager_required
def api_daily():
    days = int(request.args.get("days", 7))
    rows = db.session.query(
        func.date(Sale.timestamp).label("day"),
        func.sum(Sale.total).label("total"),
        func.count(Sale.id).label("count")
    ).filter(Sale.timestamp >= _date_range(days)).group_by("day").order_by("day").all()
    return jsonify([{"day": str(r.day), "total": r.total, "count": r.count} for r in rows])


@reports_bp.route("/sales.csv")
@login_required
@manager_required
def sales_csv():
    days = int(request.args.get("days", 7))
    rows = db.session.query(
        func.date(Sale.timestamp).label("day"),
        func.sum(Sale.total).label("total"),
        func.count(Sale.id).label("count")
    ).filter(Sale.timestamp >= _date_range(days)).group_by("day").order_by("day").all()
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["day", "orders", "total"])
    for r in rows:
        w.writerow([str(r.day), r.count, f"{r.total:.2f}"])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=daily_sales_{days}d.csv"})


@reports_bp.route("/low_stock.csv")
@login_required
@manager_required
def low_stock_csv():
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["name", "sku", "quantity", "reorder_level"])
    for p in Product.query.filter(Product.active == True,
                                  Product.quantity <= Product.reorder_level).all():
        w.writerow([p.name, p.sku, p.quantity, p.reorder_level])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=low_stock.csv"})
'''

# ============================================================
# routes/audit.py
# ============================================================
FILES["routes/audit.py"] = '''import csv, io
from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from models import AuditLog, User
from routes.decorators import admin_required

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/")
@login_required
@admin_required
def index():
    user_id = request.args.get("user_id", type=int)
    action = request.args.get("action", "").strip()
    query = AuditLog.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    logs = query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return render_template("audit.html", logs=logs,
                           users=User.query.all(), current_user_id=user_id,
                           current_action=action)


@audit_bp.route("/export.csv")
@login_required
@admin_required
def export_csv():
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["timestamp", "user", "action", "entity", "entity_id", "detail", "ip"])
    for l in AuditLog.query.order_by(AuditLog.timestamp.desc()).all():
        w.writerow([l.timestamp.isoformat(),
                    l.user_id, l.action, l.entity or "",
                    l.entity_id or "", l.detail or "", l.ip or ""])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=audit_log.csv"})
'''

# ============================================================
# app.py
# ============================================================
FILES["app.py"] = '''from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_migrate import Migrate
from config import Config
from models import db, User

login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"

    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.suppliers import suppliers_bp
    from routes.purchases import purchases_bp
    from routes.customers import customers_bp
    from routes.sales import sales_bp
    from routes.stock import stock_bp
    from routes.finance import finance_bp
    from routes.shifts import shifts_bp
    from routes.discounts import discounts_bp
    from routes.reports import reports_bp
    from routes.audit import audit_bp

    for bp in (auth_bp, products_bp, suppliers_bp, purchases_bp, customers_bp,
               sales_bp, stock_bp, finance_bp, shifts_bp, discounts_bp,
               reports_bp, audit_bp):
        app.register_blueprint(bp)

    @app.route("/")
    @login_required
    def dashboard():
        from utils import get_open_shift
        from models import Sale, Product, Customer
        from sqlalchemy import func
        from datetime import datetime, timedelta

        since = datetime.utcnow() - timedelta(days=1)
        today_rev = db.session.query(func.coalesce(func.sum(Sale.total), 0.0))\\
            .filter(Sale.timestamp >= since, Sale.voided == False,
                    Sale.is_refund == False).scalar()
        low_count = Product.query.filter(Product.active == True,
                                         Product.quantity <= Product.reorder_level).count()
        cust_count = Customer.query.count()
        return render_template("dashboard.html", user=current_user,
                               today_rev=today_rev, low_count=low_count,
                               cust_count=cust_count,
                               open_shift=get_open_shift(current_user.id))

    @app.errorhandler(401)
    def unauth(e): return render_template("error.html", code=401, message="Please sign in."), 401

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403,
                               message="You do not have permission for this action."), 403

    @app.errorhandler(404)
    def notfound(e): return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(CSRFError)
    def csrf_err(e):
        return render_template("error.html", code=400,
                               message="Session expired. Please try again."), 400

    @app.context_processor
    def inject_globals():
        from flask_wtf.csrf import generate_csrf
        from utils import fmt_money
        return {
            "csrf_token": generate_csrf,
            "fmt_money": fmt_money,
            "STORE_NAME": app.config["STORE_NAME"],
            "CURRENCY": app.config["CURRENCY"],
        }

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", full_name="Administrator", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    return app


@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
'''

# ============================================================
# TEMPLATES
# ============================================================

FILES["templates/base.html"] = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="csrf-token" content="{{ csrf_token() }}">
  <title>{% block title %}{{ STORE_NAME }}{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
{% if current_user.is_authenticated %}
<nav class="navbar">
  <a class="brand" href="{{ url_for('dashboard') }}">{{ STORE_NAME }}</a>
  <button class="menu-toggle" onclick="document.querySelector('.navbar ul').classList.toggle('open')">Menu</button>
  <ul>
    <li><a href="{{ url_for('dashboard') }}">Dashboard</a></li>
    <li><a href="{{ url_for('sales.pos') }}">Sell</a></li>
    <li><a href="{{ url_for('sales.history') }}">Sales</a></li>
    <li><a href="{{ url_for('products.list_products') }}">Products</a></li>
    <li><a href="{{ url_for('stock.index') }}">Stock</a></li>
    <li><a href="{{ url_for('customers.index') }}">Customers</a></li>
    {% if current_user.is_manager %}
      <li><a href="{{ url_for('suppliers.index') }}">Suppliers</a></li>
      <li><a href="{{ url_for('purchases.index') }}">Purchases</a></li>
      <li><a href="{{ url_for('discounts.index') }}">Discounts</a></li>
      <li><a href="{{ url_for('finance.index') }}">Finance</a></li>
      <li><a href="{{ url_for('reports.index') }}">Reports</a></li>
      <li><a href="{{ url_for('stock.movements') }}">Movements</a></li>
    {% endif %}
    {% if current_user.is_admin %}
      <li><a href="{{ url_for('auth.users') }}">Users</a></li>
      <li><a href="{{ url_for('audit.index') }}">Audit</a></li>
    {% endif %}
    <li><a href="{{ url_for('shifts.index') }}">Shift</a></li>
    <li class="right"><a href="{{ url_for('auth.logout') }}">Logout ({{ current_user.username }})</a></li>
  </ul>
</nav>
{% endif %}
<main class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}<div class="flash {{ cat }}">{{ msg }}</div>{% endfor %}
  {% endwith %}
  {% block content %}{% endblock %}
</main>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
{% block scripts %}{% endblock %}
</body>
</html>
'''

FILES["templates/login.html"] = '''{% extends "base.html" %}
{% block title %}Login{% endblock %}
{% block content %}
<div class="card login-card">
  <h2>Sign in to {{ STORE_NAME }}</h2>
  <form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Username <input name="username" required autofocus></label>
    <label>Password <input type="password" name="password" required></label>
    <button type="submit">Login</button>
  </form>
  <p class="hint">Default: admin / admin123</p>
</div>
{% endblock %}
'''

FILES["templates/dashboard.html"] = '''{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block content %}
<h1>Dashboard</h1>
<p>Welcome, <strong>{{ user.username }}</strong> ({{ user.role }}).</p>

{% if not open_shift %}
  <div class="flash error">No open shift. <a href="{{ url_for('shifts.index') }}">Open a shift</a> before selling.</div>
{% endif %}

<div class="grid">
  <div class="tile"><h3>Last 24h revenue</h3><p>{{ fmt_money(today_rev) }}</p></div>
  <div class="tile"><h3>Low stock items</h3><p>{{ low_count }}</p></div>
  <div class="tile"><h3>Customers</h3><p>{{ cust_count }}</p></div>
</div>

<div class="grid">
  <a class="tile" href="{{ url_for('sales.pos') }}"><h3>Sell</h3><p>Point of sale</p></a>
  <a class="tile" href="{{ url_for('products.list_products') }}"><h3>Products</h3><p>Catalog</p></a>
  <a class="tile" href="{{ url_for('stock.index') }}"><h3>Stock</h3><p>Inventory</p></a>
  <a class="tile" href="{{ url_for('customers.index') }}"><h3>Customers</h3><p>Loyalty</p></a>
  {% if current_user.is_manager %}
    <a class="tile" href="{{ url_for('purchases.index') }}"><h3>Purchase Orders</h3><p>Restock</p></a>
    <a class="tile" href="{{ url_for('finance.index') }}"><h3>Finance</h3><p>P&amp;L</p></a>
    <a class="tile" href="{{ url_for('reports.index') }}"><h3>Reports</h3><p>Analytics</p></a>
  {% endif %}
</div>
{% endblock %}
'''

FILES["templates/products.html"] = '''{% extends "base.html" %}
{% block title %}Products{% endblock %}
{% block content %}
<h1>Products</h1>

<div class="toolbar">
  <form method="get" class="inline">
    <input name="q" value="{{ q }}" placeholder="Search name, SKU or barcode">
    <button>Search</button>
  </form>
  {% if current_user.is_manager %}
    <a class="btn" href="{{ url_for('products.export_csv') }}">Export CSV</a>
    <a class="btn" href="{{ url_for('products.categories') }}">Categories</a>
  {% endif %}
</div>

{% if current_user.is_manager %}
<details class="card">
  <summary>Add product</summary>
  <form method="post" action="{{ url_for('products.add_product') }}" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Name <input name="name" required></label>
    <label>SKU <input name="sku" required></label>
    <label>Barcode <input name="barcode"></label>
    <label>Price <input type="number" step="0.01" name="price" required></label>
    <label>Cost <input type="number" step="0.01" name="cost" value="0"></label>
    <label>Quantity <input type="number" name="quantity" value="0"></label>
    <label>Reorder level <input type="number" name="reorder_level" value="10"></label>
    <label>Reorder qty <input type="number" name="reorder_quantity" value="20"></label>
    <label>Category
      <select name="category_id">
        <option value="">-- none --</option>
        {% for c in categories %}<option value="{{ c.id }}">{{ c.name }}</option>{% endfor %}
      </select>
    </label>
    <label>Supplier
      <select name="supplier_id">
        <option value="">-- none --</option>
        {% for s in suppliers %}<option value="{{ s.id }}">{{ s.name }}</option>{% endfor %}
      </select>
    </label>
    <label><input type="checkbox" name="taxable" checked> Taxable</label>
    <button type="submit">Add</button>
  </form>
</details>
{% endif %}

<table class="table">
  <thead><tr>
    <th>Name</th><th>SKU</th><th>Barcode</th><th>Price</th><th>Cost</th>
    <th>Qty</th><th>Category</th><th>Supplier</th><th>Actions</th>
  </tr></thead>
  <tbody>
  {% for p in products %}
    <tr class="{{ 'low' if p.low_stock }}">
      <td>{{ p.name }}</td>
      <td>{{ p.sku }}</td>
      <td>{{ p.barcode or '-' }}</td>
      <td>{{ fmt_money(p.price) }}</td>
      <td>{{ fmt_money(p.cost) }}</td>
      <td>{{ p.quantity }}</td>
      <td>{{ p.category.name if p.category else '-' }}</td>
      <td>{{ p.supplier.name if p.supplier else '-' }}</td>
      <td>
        {% if current_user.is_manager %}
          <form method="post" action="{{ url_for('products.archive_product', pid=p.id) }}"
                onsubmit="return confirm('Archive {{ p.name }}?')">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <button class="danger">Archive</button>
          </form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/categories.html"] = '''{% extends "base.html" %}
{% block title %}Categories{% endblock %}
{% block content %}
<h1>Categories</h1>

<div class="card">
  <form method="post" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Name <input name="name" required></label>
    <label>Description <input name="description"></label>
    <button type="submit">Add</button>
  </form>
</div>

<table class="table">
  <thead><tr><th>Name</th><th>Description</th><th></th></tr></thead>
  <tbody>
  {% for c in categories %}
    <tr>
      <td>{{ c.name }}</td>
      <td>{{ c.description }}</td>
      <td>
        <form method="post" action="{{ url_for('products.delete_category', cid=c.id) }}"
              onsubmit="return confirm('Delete?')">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <button class="danger">Delete</button>
        </form>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
<p><a class="btn" href="{{ url_for('products.list_products') }}">Back</a></p>
{% endblock %}
'''

FILES["templates/suppliers.html"] = '''{% extends "base.html" %}
{% block title %}Suppliers{% endblock %}
{% block content %}
<h1>Suppliers</h1>

<div class="card">
  <form method="post" action="{{ url_for('suppliers.add') }}" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Name <input name="name" required></label>
    <label>Contact <input name="contact_name"></label>
    <label>Phone <input name="phone"></label>
    <label>Email <input name="email"></label>
    <label>Address <input name="address"></label>
    <label>Notes <input name="notes"></label>
    <button type="submit">Add</button>
  </form>
</div>

<table class="table">
  <thead><tr><th>Name</th><th>Contact</th><th>Phone</th><th>Email</th><th>Address</th></tr></thead>
  <tbody>
  {% for s in suppliers %}
    <tr>
      <td>{{ s.name }}</td>
      <td>{{ s.contact_name }}</td>
      <td>{{ s.phone }}</td>
      <td>{{ s.email }}</td>
      <td>{{ s.address }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/purchases.html"] = '''{% extends "base.html" %}
{% block title %}Purchase Orders{% endblock %}
{% block content %}
<h1>Purchase Orders</h1>

<div class="card">
  <h3>New PO</h3>
  <form method="post" action="{{ url_for('purchases.new') }}" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Supplier
      <select name="supplier_id" required>
        {% for s in suppliers %}<option value="{{ s.id }}">{{ s.name }}</option>{% endfor %}
      </select>
    </label>
    <label>Expected date <input type="date" name="expected_at"></label>
    <label>Notes <input name="notes"></label>
    <button type="submit">Create</button>
  </form>
</div>

<table class="table">
  <thead><tr><th>#</th><th>Supplier</th><th>Status</th><th>Created</th><th>Total</th><th></th></tr></thead>
  <tbody>
  {% for p in pos %}
    <tr>
      <td>{{ p.id }}</td>
      <td>{{ p.supplier.name if p.supplier else '-' }}</td>
      <td><span class="status {{ p.status }}">{{ p.status }}</span></td>
      <td>{{ p.created_at.strftime("%Y-%m-%d") }}</td>
      <td>{{ fmt_money(p.total_cost) }}</td>
      <td><a class="btn" href="{{ url_for('purchases.detail', po_id=p.id) }}">Open</a></td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/purchase_detail.html"] = '''{% extends "base.html" %}
{% block title %}PO #{{ po.id }}{% endblock %}
{% block content %}
<h1>Purchase Order #{{ po.id }}</h1>
<p>Supplier: <strong>{{ po.supplier.name if po.supplier else '-' }}</strong> ·
   Status: <span class="status {{ po.status }}">{{ po.status }}</span> ·
   Total: <strong>{{ fmt_money(po.total_cost) }}</strong></p>

{% if po.status == "draft" %}
<div class="card">
  <h3>Add item</h3>
  <form method="post" action="{{ url_for('purchases.add_item', po_id=po.id) }}" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Product
      <select name="product_id" required>
        {% for p in products %}<option value="{{ p.id }}">{{ p.name }}</option>{% endfor %}
      </select>
    </label>
    <label>Quantity <input type="number" name="quantity" value="1" min="1"></label>
    <label>Unit cost <input type="number" step="0.01" name="unit_cost" value="0"></label>
    <button type="submit">Add</button>
  </form>
</div>
{% endif %}

<table class="table">
  <thead><tr><th>Product</th><th>Qty</th><th>Unit cost</th><th>Subtotal</th><th></th></tr></thead>
  <tbody>
  {% for it in po.items %}
    <tr>
      <td>{{ it.product.name }}</td>
      <td>{{ it.quantity }}</td>
      <td>{{ fmt_money(it.unit_cost) }}</td>
      <td>{{ fmt_money(it.subtotal) }}</td>
      <td>
        {% if po.status == "draft" %}
        <form method="post" action="{{ url_for('purchases.remove_item', po_id=po.id, item_id=it.id) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <button class="danger">Remove</button>
        </form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>

<div class="toolbar">
  {% if po.status == "draft" %}
    <form method="post" action="{{ url_for('purchases.submit', po_id=po.id) }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <button>Submit to supplier</button>
    </form>
  {% endif %}
  {% if po.status == "ordered" %}
    <form method="post" action="{{ url_for('purchases.receive', po_id=po.id) }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <button>Receive &amp; update stock</button>
    </form>
  {% endif %}
  {% if po.status in ("draft", "ordered") %}
    <form method="post" action="{{ url_for('purchases.cancel', po_id=po.id) }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <button class="danger">Cancel PO</button>
    </form>
  {% endif %}
  <a class="btn" href="{{ url_for('purchases.index') }}">Back</a>
</div>
{% endblock %}
'''

FILES["templates/customers.html"] = '''{% extends "base.html" %}
{% block title %}Customers{% endblock %}
{% block content %}
<h1>Customers</h1>

<form method="get" class="inline">
  <input name="q" value="{{ q }}" placeholder="Search name, phone or email">
  <button>Search</button>
</form>

<div class="card">
  <form method="post" action="{{ url_for('customers.add') }}" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Name <input name="name" required></label>
    <label>Phone <input name="phone"></label>
    <label>Email <input name="email"></label>
    <label>Address <input name="address"></label>
    <button type="submit">Add</button>
  </form>
</div>

<table class="table">
  <thead><tr><th>Name</th><th>Phone</th><th>Email</th><th>Points</th><th>Spent</th><th></th></tr></thead>
  <tbody>
  {% for c in customers %}
    <tr>
      <td>{{ c.name }}</td>
      <td>{{ c.phone }}</td>
      <td>{{ c.email }}</td>
      <td>{{ c.loyalty_points }}</td>
      <td>{{ fmt_money(c.total_spent) }}</td>
      <td><a class="btn" href="{{ url_for('customers.detail', cid=c.id) }}">Open</a></td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/customer_detail.html"] = '''{% extends "base.html" %}
{% block title %}{{ customer.name }}{% endblock %}
{% block content %}
<h1>{{ customer.name }}</h1>
<p>{{ customer.phone }} · {{ customer.email }} · {{ customer.address }}</p>
<p>Points: <strong>{{ customer.loyalty_points }}</strong> ·
   Total spent: <strong>{{ fmt_money(customer.total_spent) }}</strong></p>

<h3>Purchase history</h3>
<table class="table">
  <thead><tr><th>#</th><th>When</th><th>Total</th><th></th></tr></thead>
  <tbody>
  {% for s in sales %}
    <tr>
      <td>{{ s.id }}</td>
      <td>{{ s.timestamp.strftime("%Y-%m-%d %H:%M") }}</td>
      <td>{{ fmt_money(s.total) }}</td>
      <td><a href="{{ url_for('sales.receipt', sid=s.id) }}" target="_blank">Receipt</a></td>
    </tr>
  {% endfor %}
  </tbody>
</table>
<p><a class="btn" href="{{ url_for('customers.index') }}">Back</a></p>
{% endblock %}
'''

FILES["templates/sales.html"] = '''{% extends "base.html" %}
{% block title %}Sales{% endblock %}
{% block content %}
{% if show_history %}
  <h1>Sales history</h1>
  <form method="get" class="inline">
    <input name="q" value="{{ q or '' }}" placeholder="Sale #">
    <button>Search</button>
  </form>
  {% if current_user.is_manager %}
    <p><a class="btn" href="{{ url_for('sales.export_csv') }}">Export CSV</a></p>
  {% endif %}
  <table class="table">
    <thead><tr><th>#</th><th>When</th><th>Cashier</th><th>Customer</th><th>Total</th><th>Payment</th><th>Flags</th><th></th></tr></thead>
    <tbody>
    {% for s in sales %}
      <tr class="{{ 'low' if s.voided or s.is_refund }}">
        <td>{{ s.id }}</td>
        <td>{{ s.timestamp.strftime("%Y-%m-%d %H:%M") }}</td>
        <td>{{ s.user.username if s.user else '-' }}</td>
        <td>{{ s.customer.name if s.customer else '-' }}</td>
        <td>{{ fmt_money(s.total) }}</td>
        <td>{{ s.payment_method }}</td>
        <td>{% if s.is_refund %}REFUND{% endif %}{% if s.voided %} VOID{% endif %}</td>
        <td>
          <a href="{{ url_for('sales.receipt', sid=s.id) }}" target="_blank">View</a>
          {% if current_user.is_manager and not s.voided and not s.is_refund %}
            <form method="post" action="{{ url_for('sales.refund', sid=s.id) }}"
                  style="display:inline" onsubmit="return confirm('Refund sale #{{ s.id }}?')">
              <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
              <button class="danger">Refund</button>
            </form>
          {% endif %}
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
{% else %}
  <h1>Point of Sale</h1>
  {% if not shift %}
    <div class="flash error">No open shift. <a href="{{ url_for('shifts.index') }}">Open a shift</a> to sell.</div>
  {% endif %}
  <div class="pos">
    <div class="pos-left">
      <input id="search" placeholder="Search or scan barcode..." autofocus>
      <p class="hint">Tip: barcode scanners type the code and press Enter.</p>
      <ul id="results" class="results"></ul>
    </div>
    <div class="pos-right card">
      <h3>Cart</h3>
      <table class="table" id="cart">
        <thead><tr><th>Item</th><th>Qty</th><th>Price</th><th>Sub</th><th></th></tr></thead>
        <tbody></tbody>
      </table>
      <p class="total">Total: <strong id="total">{{ CURRENCY }}0.00</strong></p>
      <div class="grid-form">
        <label>Customer
          <input id="customer" placeholder="Search name/phone" autocomplete="off">
          <input type="hidden" id="customer_id">
        </label>
        <label>Discount code <input id="discount" placeholder="e.g. SAVE10"></label>
        <label>Payment
          <select id="payment">
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="mobile">Mobile</option>
          </select>
        </label>
        <label>Paid <input id="paid" type="number" step="0.01" placeholder="0.00"></label>
      </div>
      <ul id="customer_results" class="results"></ul>
      <button id="checkout" class="primary">Complete Sale</button>
    </div>
  </div>
{% endif %}
{% endblock %}

{% block scripts %}
{% if not show_history %}
<script>
const cart = [];
const $ = s => document.querySelector(s);
let lastResults = [];

function addToCart(product) {
  const existing = cart.find(c => c.id === product.id);
  if (existing) existing.qty = Math.min(existing.qty + 1, product.quantity);
  else cart.push({ id: product.id, name: product.name, price: product.price,
                   stock: product.quantity, qty: 1 });
  renderCart();
}

$("#search").addEventListener("input", async (e) => {
  const q = e.target.value.trim();
  if (!q) { $("#results").innerHTML = ""; return; }
  try {
    lastResults = await api("/products/api/search?q=" + encodeURIComponent(q));
    $("#results").innerHTML = lastResults.map(p =>
      `<li data-id="${p.id}">${p.name}
        <small>(${p.sku}) ${p.price.toFixed(2)} · stock ${p.quantity}</small>
      </li>`).join("");
  } catch (err) { console.error(err); }
});

$("#search").addEventListener("keydown", async (e) => {
  if (e.key !== "Enter") return;
  const code = e.target.value.trim();
  if (!code) return;
  e.preventDefault();
  try {
    const p = await api("/products/api/barcode/" + encodeURIComponent(code));
    addToCart(p);
  } catch {
    if (lastResults && lastResults.length === 1) addToCart(lastResults[0]);
    else alert("No product matched: " + code);
  }
  e.target.value = ""; $("#results").innerHTML = "";
});

$("#results").addEventListener("click", (e) => {
  const li = e.target.closest("li"); if (!li) return;
  const p = lastResults.find(x => x.id === +li.dataset.id);
  if (p) addToCart(p);
  $("#search").value = ""; $("#results").innerHTML = "";
});

function renderCart() {
  const tbody = $("#cart tbody");
  tbody.innerHTML = cart.map((c, i) => `
    <tr>
      <td>${c.name}</td>
      <td><input type="number" min="1" max="${c.stock}" value="${c.qty}" data-i="${i}"></td>
      <td>${c.price.toFixed(2)}</td>
      <td>${(c.qty * c.price).toFixed(2)}</td>
      <td><button class="danger" data-remove="${i}">x</button></td>
    </tr>`).join("");
  const total = cart.reduce((s, c) => s + c.qty * c.price, 0);
  $("#total").textContent = "{{ CURRENCY }}" + total.toFixed(2);
}

$("#cart").addEventListener("input", (e) => {
  if (e.target.tagName === "INPUT") {
    const i = +e.target.dataset.i;
    cart[i].qty = Math.max(1, Math.min(cart[i].stock, +e.target.value));
    renderCart();
  }
});

$("#cart").addEventListener("click", (e) => {
  const i = e.target.dataset.remove;
  if (i !== undefined) { cart.splice(+i, 1); renderCart(); }
});

// Customer autocomplete
$("#customer").addEventListener("input", async (e) => {
  const q = e.target.value.trim();
  if (!q) { $("#customer_results").innerHTML = ""; return; }
  try {
    const items = await api("/customers/api/search?q=" + encodeURIComponent(q));
    $("#customer_results").innerHTML = items.map(c =>
      `<li data-id="${c.id}" data-name="${c.name}">${c.name} <small>${c.phone || ""}</small></li>`
    ).join("");
  } catch (err) { console.error(err); }
});

$("#customer_results").addEventListener("click", (e) => {
  const li = e.target.closest("li"); if (!li) return;
  $("#customer").value = li.dataset.name;
  $("#customer_id").value = li.dataset.id;
  $("#customer_results").innerHTML = "";
});

$("#checkout").addEventListener("click", async () => {
  if (!cart.length) return alert("Cart is empty");
  try {
    const data = await api("/sales/api/checkout", {
      method: "POST",
      body: {
        payment_method: $("#payment").value,
        customer_id: $("#customer_id").value || null,
        discount_code: $("#discount").value.trim() || null,
        amount_paid: parseFloat($("#paid").value) || null,
        items: cart.map(c => ({ product_id: c.id, quantity: c.qty }))
      }
    });
    const open = confirm(
      "Sale #" + data.sale_id + " completed. Total " + data.total.toFixed(2) +
      "\\n\\nOpen printable receipt?"
    );
    if (open) window.open(data.receipt_url, "_blank");
    cart.length = 0; renderCart();
    $("#customer_id").value = ""; $("#customer").value = "";
    $("#discount").value = ""; $("#paid").value = "";
  } catch (err) {
    alert(err.message || "Checkout failed");
  }
});
</script>
{% endif %}
{% endblock %}
'''

FILES["templates/receipt.html"] = '''<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Receipt #{{ sale.id }}</title>
  <style>
    body { font-family: ui-monospace, Menlo, Consolas, monospace; max-width: 380px;
           margin: 1rem auto; padding: 1rem; color: #111; }
    h1 { font-size: 1.2rem; text-align: center; margin: 0; }
    .muted { color: #666; font-size: 0.8rem; text-align: center; }
    hr { border: none; border-top: 1px dashed #999; margin: 0.7rem 0; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    td { padding: 0.15rem 0; vertical-align: top; }
    .right { text-align: right; }
    .total { font-weight: bold; font-size: 1.05rem; }
    .actions { text-align: center; margin-top: 1rem; }
    button, a.btn { padding: 0.4rem 0.8rem; margin: 0.1rem; }
    @media print { .actions { display: none; } }
  </style>
</head>
<body>
  <h1>{{ STORE_NAME }}</h1>
  <p class="muted">{{ config.STORE_ADDRESS }}<br>{{ config.STORE_PHONE }}</p>
  <hr>
  <table>
    <tr><td>Receipt #</td><td class="right">{{ sale.id }}</td></tr>
    <tr><td>Date</td><td class="right">{{ sale.timestamp.strftime("%Y-%m-%d %H:%M") }}</td></tr>
    <tr><td>Cashier</td><td class="right">{{ sale.user.username if sale.user else '-' }}</td></tr>
    {% if sale.customer %}<tr><td>Customer</td><td class="right">{{ sale.customer.name }}</td></tr>{% endif %}
    <tr><td>Payment</td><td class="right">{{ sale.payment_method }}</td></tr>
    {% if sale.is_refund %}<tr><td colspan="2" class="right"><strong>REFUND</strong></td></tr>{% endif %}
  </table>
  <hr>
  <table>
    {% for it in sale.items %}
      <tr>
        <td>{{ it.product.name }}<br><span class="muted">{{ it.quantity }} x {{ fmt_money(it.unit_price) }}</span></td>
        <td class="right">{{ fmt_money(it.subtotal) }}</td>
      </tr>
    {% endfor %}
  </table>
  <hr>
  <table>
    <tr><td>Subtotal</td><td class="right">{{ fmt_money(sale.subtotal) }}</td></tr>
    {% if sale.discount_amount %}<tr><td>Discount</td><td class="right">-{{ fmt_money(sale.discount_amount) }}</td></tr>{% endif %}
    <tr><td>Tax</td><td class="right">{{ fmt_money(sale.tax_amount) }}</td></tr>
    <tr class="total"><td>TOTAL</td><td class="right">{{ fmt_money(sale.total) }}</td></tr>
    {% if sale.amount_paid %}<tr><td>Paid</td><td class="right">{{ fmt_money(sale.amount_paid) }}</td></tr>{% endif %}
    {% if sale.change_given %}<tr><td>Change</td><td class="right">{{ fmt_money(sale.change_given) }}</td></tr>{% endif %}
  </table>
  <hr>
  <p class="muted">Thank you for shopping at {{ STORE_NAME }}!</p>
  <div class="actions">
    <button onclick="window.print()">Print</button>
    <a class="btn" href="{{ url_for('sales.receipt_pdf', sid=sale.id) }}" target="_blank">PDF</a>
    <a class="btn" href="{{ url_for('sales.pos') }}">New sale</a>
  </div>
</body>
</html>
'''

FILES["templates/stock.html"] = '''{% extends "base.html" %}
{% block title %}Stock{% endblock %}
{% block content %}
<h1>Stock</h1>
{% if low %}
  <div class="flash error">{{ low|length }} product(s) at or below reorder level.</div>
{% endif %}

<table class="table">
  <thead><tr><th>Product</th><th>Qty</th><th>Reorder</th><th>Restock</th><th>Adjust</th></tr></thead>
  <tbody>
  {% for p in products %}
    <tr class="{{ 'low' if p.low_stock }}">
      <td>{{ p.name }}</td>
      <td>{{ p.quantity }}</td>
      <td>{{ p.reorder_level }}</td>
      <td>
        {% if current_user.is_manager %}
        <form method="post" action="{{ url_for('stock.restock', pid=p.id) }}" class="inline">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="number" name="amount" value="10" min="1" style="width:70px">
          <button>Add</button>
        </form>
        {% endif %}
      </td>
      <td>
        {% if current_user.is_manager %}
        <form method="post" action="{{ url_for('stock.adjust', pid=p.id) }}" class="inline">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="number" name="quantity" value="{{ p.quantity }}" style="width:70px">
          <button>Set</button>
        </form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/stock_movements.html"] = '''{% extends "base.html" %}
{% block title %}Stock Movements{% endblock %}
{% block content %}
<h1>Stock Movements</h1>

<form method="get" class="inline">
  <label>Product
    <select name="product_id" onchange="this.form.submit()">
      <option value="">All</option>
      {% for p in products %}
        <option value="{{ p.id }}" {{ "selected" if current_product == p.id }}>{{ p.name }}</option>
      {% endfor %}
    </select>
  </label>
</form>

<table class="table">
  <thead><tr><th>When</th><th>Product</th><th>Change</th><th>Reason</th><th>Ref</th><th>User</th><th>Note</th></tr></thead>
  <tbody>
  {% for m in movements %}
    <tr>
      <td>{{ m.timestamp.strftime("%Y-%m-%d %H:%M") }}</td>
      <td>{{ m.product.name if m.product else '-' }}</td>
      <td>{{ "%+d"|format(m.change) }}</td>
      <td>{{ m.reason }}</td>
      <td>{{ m.reference or '-' }}</td>
      <td>{{ m.user.username if m.user else '-' }}</td>
      <td>{{ m.note or '' }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/shifts.html"] = '''{% extends "base.html" %}
{% block title %}Shifts{% endblock %}
{% block content %}
<h1>Shifts</h1>

{% if open_shift %}
  <div class="card">
    <h3>Open shift #{{ open_shift.id }}</h3>
    <p>Opened at {{ open_shift.opened_at.strftime("%Y-%m-%d %H:%M") }} ·
       Opening float: {{ fmt_money(open_shift.opening_float) }}</p>
    <form method="post" action="{{ url_for('shifts.close_shift') }}" class="grid-form">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <label>Closing cash counted <input type="number" step="0.01" name="closing_cash" required></label>
      <label>Notes <input name="notes"></label>
      <button type="submit">Close shift</button>
    </form>
  </div>
{% else %}
  <div class="card">
    <h3>Open a new shift</h3>
    <form method="post" action="{{ url_for('shifts.open_shift') }}" class="grid-form">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <label>Opening float <input type="number" step="0.01" name="opening_float" value="0"></label>
      <button type="submit">Open shift</button>
    </form>
  </div>
{% endif %}

<h3>History</h3>
<table class="table">
  <thead><tr><th>#</th><th>Opened</th><th>Closed</th><th>Float</th><th>Expected</th><th>Counted</th><th>Diff</th></tr></thead>
  <tbody>
  {% for s in history %}
    <tr>
      <td>{{ s.id }}</td>
      <td>{{ s.opened_at.strftime("%Y-%m-%d %H:%M") }}</td>
      <td>{{ s.closed_at.strftime("%Y-%m-%d %H:%M") if s.closed_at else '-' }}</td>
      <td>{{ fmt_money(s.opening_float) }}</td>
      <td>{{ fmt_money(s.expected_cash) if s.expected_cash is not none else '-' }}</td>
      <td>{{ fmt_money(s.closing_cash) if s.closing_cash is not none else '-' }}</td>
      <td>{% if s.difference is not none %}{{ "%+.2f"|format(s.difference) }}{% else %}-{% endif %}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/discounts.html"] = '''{% extends "base.html" %}
{% block title %}Discounts{% endblock %}
{% block content %}
<h1>Discounts</h1>

<div class="card">
  <form method="post" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Code <input name="code" required></label>
    <label>Description <input name="description"></label>
    <label>Kind
      <select name="kind">
        <option value="percent">Percent</option>
        <option value="fixed">Fixed</option>
      </select>
    </label>
    <label>Value <input type="number" step="0.01" name="value" required></label>
    <label>Min purchase <input type="number" step="0.01" name="min_purchase" value="0"></label>
    <label>Valid from <input type="date" name="valid_from"></label>
    <label>Valid to <input type="date" name="valid_to"></label>
    <button type="submit">Add</button>
  </form>
</div>

<table class="table">
  <thead><tr><th>Code</th><th>Description</th><th>Kind</th><th>Value</th><th>Min</th><th>From</th><th>To</th><th>Active</th><th></th></tr></thead>
  <tbody>
  {% for d in discounts %}
    <tr>
      <td>{{ d.code }}</td>
      <td>{{ d.description }}</td>
      <td>{{ d.kind }}</td>
      <td>{{ d.value }}</td>
      <td>{{ d.min_purchase }}</td>
      <td>{{ d.valid_from or '-' }}</td>
      <td>{{ d.valid_to or '-' }}</td>
      <td>{{ "Yes" if d.active else "No" }}</td>
      <td>
        <form method="post" action="{{ url_for('discounts.toggle', did=d.id) }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <button>{{ "Disable" if d.active else "Enable" }}</button>
        </form>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/finance.html"] = '''{% extends "base.html" %}
{% block title %}Finance{% endblock %}
{% block content %}
<h1>Finance - This Month</h1>
<div class="grid">
  <div class="tile"><h3>Revenue</h3><p>{{ fmt_money(revenue) }}</p></div>
  <div class="tile"><h3>Refunds</h3><p>{{ fmt_money(refunds) }}</p></div>
  <div class="tile"><h3>COGS</h3><p>{{ fmt_money(cogs) }}</p></div>
  <div class="tile"><h3>Gross profit</h3><p>{{ fmt_money(gross_profit) }}</p></div>
  <div class="tile"><h3>Expenses</h3><p>{{ fmt_money(expenses) }}</p></div>
  <div class="tile"><h3>Net profit</h3><p>{{ fmt_money(net_profit) }}</p></div>
</div>

<div class="card">
  <h3>Record expense</h3>
  <form method="post" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Date <input type="date" name="date" value="{{ today }}" required></label>
    <label>Category <input name="category" required></label>
    <label>Amount <input type="number" step="0.01" name="amount" required></label>
    <label>Note <input name="note"></label>
    <button type="submit">Add</button>
  </form>
</div>

<p><a class="btn" href="{{ url_for('finance.expenses_csv') }}">Export expenses CSV</a></p>

<h3>Recent expenses</h3>
<table class="table">
  <thead><tr><th>Date</th><th>Category</th><th>Amount</th><th>Note</th></tr></thead>
  <tbody>
  {% for e in recent %}
    <tr><td>{{ e.date }}</td><td>{{ e.category }}</td>
        <td>{{ fmt_money(e.amount) }}</td><td>{{ e.note }}</td></tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/reports.html"] = '''{% extends "base.html" %}
{% block title %}Reports{% endblock %}
{% block content %}
<h1>Reports</h1>

<form method="get" class="inline">
  <label>Last
    <select name="days" onchange="this.form.submit()">
      {% for d in [7, 14, 30, 90] %}
        <option value="{{ d }}" {{ "selected" if d == days }}>{{ d }} days</option>
      {% endfor %}
    </select>
  </label>
  <a class="btn" href="{{ url_for('reports.sales_csv', days=days) }}">Daily CSV</a>
  <a class="btn" href="{{ url_for('reports.low_stock_csv') }}">Low stock CSV</a>
</form>

<h3>Daily sales</h3>
<canvas id="salesChart" height="100"></canvas>

<h3>By payment method</h3>
<table class="table">
  <thead><tr><th>Method</th><th>Orders</th><th>Total</th></tr></thead>
  <tbody>
  {% for r in by_payment %}
    <tr><td>{{ r.payment_method }}</td><td>{{ r.count }}</td><td>{{ fmt_money(r.total) }}</td></tr>
  {% endfor %}
  </tbody>
</table>

<h3>Top products ({{ days }} days)</h3>
<table class="table">
  <thead><tr><th>Product</th><th>Units</th><th>Revenue</th></tr></thead>
  <tbody>
  {% for t in top %}
    <tr><td>{{ t.name }}</td><td>{{ t.qty }}</td><td>{{ fmt_money(t.revenue) }}</td></tr>
  {% endfor %}
  </tbody>
</table>

<h3>Top customers</h3>
<table class="table">
  <thead><tr><th>Customer</th><th>Total spent</th><th>Points</th></tr></thead>
  <tbody>
  {% for c in top_customers %}
    <tr><td>{{ c.name }}</td><td>{{ fmt_money(c.total_spent) }}</td><td>{{ c.loyalty_points }}</td></tr>
  {% endfor %}
  </tbody>
</table>

<div class="grid">
  <div class="tile"><h3>Stock value (cost)</h3><p>{{ fmt_money(stock_value) }}</p></div>
  <div class="tile"><h3>Low stock items</h3><p>{{ low_stock|length }}</p></div>
</div>
{% endblock %}

{% block scripts %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const daily = {{ daily|tojson }};
new Chart(document.getElementById("salesChart"), {
  type: "bar",
  data: { labels: daily.map(d => d.day),
          datasets: [{ label: "Sales", data: daily.map(d => d.total),
                       backgroundColor: "#4f46e5" }] },
  options: { responsive: true, scales: { y: { beginAtZero: true } } }
});
</script>
{% endblock %}
'''

FILES["templates/audit.html"] = '''{% extends "base.html" %}
{% block title %}Audit Log{% endblock %}
{% block content %}
<h1>Audit Log</h1>

<form method="get" class="inline">
  <label>User
    <select name="user_id">
      <option value="">All</option>
      {% for u in users %}
        <option value="{{ u.id }}" {{ "selected" if current_user_id == u.id }}>{{ u.username }}</option>
      {% endfor %}
    </select>
  </label>
  <label>Action <input name="action" value="{{ current_action }}"></label>
  <button>Filter</button>
  <a class="btn" href="{{ url_for('audit.export_csv') }}">Export CSV</a>
</form>

<table class="table">
  <thead><tr><th>When</th><th>User</th><th>Action</th><th>Entity</th><th>ID</th><th>Detail</th><th>IP</th></tr></thead>
  <tbody>
  {% for l in logs %}
    <tr>
      <td>{{ l.timestamp.strftime("%Y-%m-%d %H:%M:%S") }}</td>
      <td>{{ l.user_id }}</td>
      <td>{{ l.action }}</td>
      <td>{{ l.entity or '' }}</td>
      <td>{{ l.entity_id or '' }}</td>
      <td>{{ l.detail or '' }}</td>
      <td>{{ l.ip or '' }}</td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/users.html"] = '''{% extends "base.html" %}
{% block title %}Users{% endblock %}
{% block content %}
<h1>Users</h1>

<div class="card">
  <h3>Add user</h3>
  <form method="post" action="{{ url_for('auth.add_user') }}" class="grid-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <label>Username <input name="username" required></label>
    <label>Full name <input name="full_name"></label>
    <label>Password <input type="password" name="password" required></label>
    <label>Role
      <select name="role">
        <option value="cashier">Cashier</option>
        <option value="manager">Manager</option>
        <option value="admin">Admin</option>
      </select>
    </label>
    <button type="submit">Add</button>
  </form>
</div>

<table class="table">
  <thead><tr><th>Username</th><th>Full name</th><th>Role</th><th>Active</th><th>Actions</th></tr></thead>
  <tbody>
  {% for u in users %}
    <tr>
      <td>{{ u.username }}</td>
      <td>{{ u.full_name }}</td>
      <td>{{ u.role }}</td>
      <td>{{ "Yes" if u.active else "No" }}</td>
      <td>
        <form method="post" action="{{ url_for('auth.toggle_user', uid=u.id) }}" style="display:inline">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <button>{{ "Deactivate" if u.active else "Activate" }}</button>
        </form>
        <form method="post" action="{{ url_for('auth.reset_password', uid=u.id) }}" class="inline">
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
          <input type="password" name="password" placeholder="New password" required>
          <button>Reset</button>
        </form>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% endblock %}
'''

FILES["templates/error.html"] = '''{% extends "base.html" %}
{% block title %}Error {{ code }}{% endblock %}
{% block content %}
<div class="card" style="text-align:center">
  <h1 style="font-size:3rem;margin:0">{{ code }}</h1>
  <p>{{ message }}</p>
  <a class="btn" href="{{ url_for('dashboard') }}">Back to dashboard</a>
</div>
{% endblock %}
'''

# ============================================================
# static/css/style.css
# ============================================================
FILES["static/css/style.css"] = ''':root {
  --primary: #4f46e5;
  --bg: #f6f7fb;
  --card: #fff;
  --border: #e5e7eb;
  --danger: #dc2626;
  --text: #111827;
  --muted: #6b7280;
}
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif;
       background: var(--bg); color: var(--text); }

.navbar { background: var(--primary); color: #fff; padding: 0.6rem 1.2rem;
          display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.navbar .brand { font-weight: 700; font-size: 1.15rem; color: #fff; text-decoration: none; }
.navbar ul { list-style: none; display: flex; gap: 1rem; margin: 0; padding: 0; flex-wrap: wrap; }
.navbar a { color: #e0e7ff; text-decoration: none; }
.navbar a:hover { color: #fff; }
.navbar .right { margin-left: auto; }
.navbar .menu-toggle { display: none; background: transparent; border: 1px solid #fff;
                       color: #fff; padding: 0.2rem 0.5rem; border-radius: 4px; }
@media (max-width: 900px) {
  .navbar ul { display: none; flex-direction: column; width: 100%; }
  .navbar ul.open { display: flex; }
  .navbar .menu-toggle { display: inline-block; }
}

.container { max-width: 1200px; margin: 1.5rem auto; padding: 0 1rem; }

.card { background: var(--card); border: 1px solid var(--border); border-radius: 10px;
        padding: 1rem; margin: 0.75rem 0; }

.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; }
.tile { display: block; background: var(--card); border: 1px solid var(--border);
        border-radius: 10px; padding: 1rem; text-decoration: none; color: var(--text); }
.tile:hover { border-color: var(--primary); }
.tile h3 { margin: 0 0 0.25rem; font-size: 1rem; }
.tile p { margin: 0; color: var(--muted); }

.grid-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
             gap: 0.5rem; align-items: end; }
label { display: flex; flex-direction: column; font-size: 0.85rem; color: var(--muted); gap: 0.2rem; }
input, select, button { font: inherit; padding: 0.45rem 0.6rem; border: 1px solid var(--border);
                        border-radius: 6px; background: #fff; }
button { cursor: pointer; background: var(--primary); color: #fff; border: none; }
button:hover { filter: brightness(1.05); }
button.danger { background: var(--danger); }

.inline { display: flex; gap: 0.4rem; align-items: end; flex-wrap: wrap; }
.toolbar { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; margin: 0.5rem 0; }

.table { width: 100%; border-collapse: collapse; background: var(--card);
         border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
.table th, .table td { padding: 0.55rem 0.7rem; text-align: left; border-bottom: 1px solid var(--border); }
.table th { background: #f3f4f6; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.03em; }
.table tr.low { background: #fef2f2; }

.flash { padding: 0.6rem 0.8rem; border-radius: 6px; margin-bottom: 0.6rem; }
.flash.success { background: #dcfce7; color: #166534; }
.flash.error { background: #fee2e2; color: #991b1b; }

.login-card { max-width: 360px; margin: 4rem auto; }
.login-card input { width: 100%; }
.hint { color: var(--muted); font-size: 0.85rem; }

.btn { display: inline-block; padding: 0.45rem 0.8rem; background: var(--primary);
       color: #fff; text-decoration: none; border-radius: 6px; }

.pos { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 720px) { .pos { grid-template-columns: 1fr; } }
.results { list-style: none; padding: 0; margin: 0.4rem 0; }
.results li { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px;
              margin-bottom: 0.3rem; cursor: pointer; background: #fff; }
.results li:hover { border-color: var(--primary); }
.results small { color: var(--muted); }
.total { font-size: 1.1rem; }

.status { padding: 0.15rem 0.5rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
.status.draft { background: #e5e7eb; }
.status.ordered { background: #dbeafe; color: #1e40af; }
.status.received { background: #dcfce7; color: #166534; }
.status.cancelled { background: #fee2e2; color: #991b1b; }
'''

# ============================================================
# static/js/app.js
# ============================================================
FILES["static/js/app.js"] = '''const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || "";

async function api(url, options = {}) {
  const opts = {
    method: options.method || "GET",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": CSRF_TOKEN,
      ...(options.headers || {}),
    },
    credentials: "same-origin",
  };
  if (options.body !== undefined) {
    opts.body = typeof options.body === "string"
      ? options.body : JSON.stringify(options.body);
  }
  const r = await fetch(url, opts);
  const isJson = (r.headers.get("content-type") || "").includes("application/json");
  const data = isJson ? await r.json() : await r.text();
  if (!r.ok) throw new Error((data && data.error) || ("HTTP " + r.status));
  return data;
}

document.querySelectorAll(".flash").forEach(el => {
  setTimeout(() => el.style.display = "none", 4000);
});
'''

# ============================================================
# tests/test_app.py
# ============================================================
FILES["tests/test_app.py"] = '''import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import TestConfig
from models import db, User, Product, Sale, SaleItem, Shift


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(username="admin", role="admin"); admin.set_password("admin123")
        cashier = User(username="cashier", role="cashier"); cashier.set_password("cash123")
        db.session.add_all([admin, cashier])
        db.session.add(Product(name="Widget", sku="W1", barcode="1111",
                               price=10.0, cost=4.0, quantity=5, reorder_level=2))
        db.session.commit()
    with app.test_client() as c:
        yield c


def login(c, username, password):
    return c.post("/login", data={"username": username, "password": password},
                  follow_redirects=True)


def open_shift_and_login(c, username, password):
    login(c, username, password)
    return c.post("/shifts/open", data={"opening_float": "100"}, follow_redirects=True)


def test_login_and_dashboard(client):
    r = login(client, "admin", "admin123")
    assert r.status_code == 200
    assert b"Dashboard" in r.data


def test_checkout_requires_open_shift(client):
    login(client, "cashier", "cash123")
    r = client.post("/sales/api/checkout", json={
        "payment_method": "cash",
        "items": [{"product_id": 1, "quantity": 2}]
    })
    assert r.status_code == 400
    assert b"shift" in r.data.lower()


def test_checkout_decrements_stock(client):
    open_shift_and_login(client, "cashier", "cash123")
    r = client.post("/sales/api/checkout", json={
        "payment_method": "cash",
        "items": [{"product_id": 1, "quantity": 2}]
    })
    assert r.status_code == 200, r.data
    data = r.get_json()
    assert data["subtotal"] == 20.0
    assert data["total"] >= data["subtotal"]

    with client.application.app_context():
        p = Product.query.get(1)
        assert p.quantity == 3
        assert Sale.query.count() == 1
        assert SaleItem.query.count() == 1


def test_checkout_rejects_insufficient_stock(client):
    open_shift_and_login(client, "cashier", "cash123")
    r = client.post("/sales/api/checkout", json={
        "items": [{"product_id": 1, "quantity": 999}]
    })
    assert r.status_code == 400
    assert b"stock" in r.data.lower()


def test_role_gate_manager_vs_cashier(client):
    login(client, "cashier", "cash123")
    r = client.post("/products/1/archive")
    assert r.status_code == 403

    client.get("/logout")
    login(client, "admin", "admin123")
    r = client.post("/products/1/archive", follow_redirects=True)
    assert r.status_code == 200


def test_csv_export_products(client):
    login(client, "admin", "admin123")
    r = client.get("/products/export.csv")
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("text/csv")
    assert b"Widget" in r.data


def test_receipt_view(client):
    open_shift_and_login(client, "cashier", "cash123")
    client.post("/sales/api/checkout", json={
        "items": [{"product_id": 1, "quantity": 1}]
    })
    r = client.get("/sales/1/receipt")
    assert r.status_code == 200
    assert b"Widget" in r.data
'''

# ============================================================
# .env.example
# ============================================================
FILES[".env.example"] = '''SECRET_KEY=change-me-to-something-random
STORE_NAME=SmartMart
STORE_ADDRESS=123 Market Street
STORE_PHONE=+1 555 0100
STORE_TAX_RATE=0.16
CURRENCY=$
'''

# ============================================================
# README.md
# ============================================================
FILES["README.md"] = '''# SmartMart Manager

A complete single-store retail management system built with Flask + SQLite.

## Features

- POS with barcode scanning, cart, discounts, tax, and change calculation
- Products, categories, suppliers, purchase orders
- Customers with loyalty points and purchase history
- Refunds, voids, shift / cash-drawer tracking
- Finance: revenue, COGS, expenses, gross/net profit
- Reports: daily sales, top products, top customers, low stock
- CSV exports for products, sales, expenses, audit, reports
- PDF receipts (ReportLab)
- Role-based access (cashier / manager / admin) + audit log
- CSRF protection, migrations, pytest suite

## Quick start

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
'''

# ============================================================
# PROJECT BUILDER
# ============================================================
def build_project():
    """Write all files defined above into the SmartMart project folder."""
    for relative_path, content in FILES.items():
        target = ROOT / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print(f"SmartMart project created in: {ROOT.resolve()}")
    print(f"Files written: {len(FILES)}")


if __name__ == "__main__":
    build_project()
