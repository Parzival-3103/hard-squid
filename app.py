import csv
import os
import secrets
from urllib.parse import urlparse
from datetime import datetime
from decimal import Decimal
from functools import wraps
from io import StringIO

import mysql.connector
from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, session, url_for)
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "hard-squid-cambiar-en-produccion"),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST") or os.getenv("MYSQLHOST") or "127.0.0.1",
    "port": int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT") or "3307"),
    "user": os.getenv("DB_USER") or os.getenv("MYSQLUSER") or "root",
    "password": os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD") or "",
    "database": os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE") or "hard_squid",
}

mysql_url = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL")
if mysql_url:
    parsed = urlparse(mysql_url)
    DB_CONFIG.update({
        "host": parsed.hostname or DB_CONFIG["host"],
        "port": parsed.port or DB_CONFIG["port"],
        "user": parsed.username or DB_CONFIG["user"],
        "password": parsed.password or DB_CONFIG["password"],
        "database": (parsed.path or "").lstrip("/") or DB_CONFIG["database"],
    })


def get_db(database=True):
    config = dict(DB_CONFIG)
    if not database:
        config.pop("database", None)
    return mysql.connector.connect(**config)


def query_all(sql, params=()):
    with get_db() as db:
        cursor = db.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()


def query_one(sql, params=()):
    with get_db() as db:
        cursor = db.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchone()


def execute(sql, params=()):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute(sql, params)
        db.commit()
        return cursor.lastrowid


def money(value):
    return f"${Decimal(value or 0):,.2f}"


app.jinja_env.filters["money"] = money


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") not in {"admin", "empleado"}:
            flash("No tienes permiso para entrar al panel.", "danger")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("La imagen debe ser PNG, JPG, JPEG o WEBP.")
    extension = secure_filename(file.filename).rsplit(".", 1)[1].lower()
    filename = f"{secrets.token_hex(12)}.{extension}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return f"uploads/{filename}"


@app.context_processor
def global_context():
    cart = session.get("cart", {})
    return {"cart_count": sum(int(q) for q in cart.values()), "current_year": datetime.now().year}


@app.errorhandler(Error)
def database_error(error):
    app.logger.exception("Database error")
    return render_template("error.html", message="No fue posible conectar con MySQL. Revisa que MySQL esté iniciado y ejecuta schema.sql."), 503


@app.route("/")
def index():
    featured = query_all("SELECT * FROM products WHERE active=1 ORDER BY featured DESC, created_at DESC LIMIT 8")
    best = query_all("""
        SELECT p.*, COALESCE(SUM(oi.quantity),0) sold
        FROM products p LEFT JOIN order_items oi ON p.id=oi.product_id
        WHERE p.active=1 GROUP BY p.id ORDER BY sold DESC, p.created_at DESC LIMIT 4
    """)
    return render_template("index.html", products=featured, best=best)


@app.route("/catalogo")
def catalog():
    category = request.args.get("categoria", "").strip()
    search = request.args.get("q", "").strip()
    sql = "SELECT * FROM products WHERE active=1"
    params = []
    if category in {"Dama", "Caballero", "Unisex"}:
        sql += " AND category=%s"
        params.append(category)
    if search:
        sql += " AND (name LIKE %s OR description LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    sql += " ORDER BY featured DESC, created_at DESC"
    return render_template("catalog.html", products=query_all(sql, tuple(params)), category=category, search=search)


@app.route("/producto/<int:product_id>")
def product_detail(product_id):
    product = query_one("SELECT * FROM products WHERE id=%s AND active=1", (product_id,))
    if not product:
        abort(404)
    related = query_all("SELECT * FROM products WHERE category=%s AND id<>%s AND active=1 LIMIT 4", (product["category"], product_id))
    return render_template("product.html", product=product, related=related)


@app.route("/nosotros")
def about():
    return render_template("about.html")


@app.route("/registro", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or "@" not in email or len(password) < 8:
            flash("Completa tus datos; la contraseña debe tener al menos 8 caracteres.", "danger")
        elif query_one("SELECT id FROM users WHERE email=%s", (email,)):
            flash("Ese correo ya está registrado.", "warning")
        else:
            user_id = execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'cliente')", (name, email, generate_password_hash(password)))
            session.update(user_id=user_id, name=name, role="cliente")
            flash("Tu cuenta está lista. ¡Bienvenido a Hard Squid!", "success")
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = query_one("SELECT * FROM users WHERE email=%s AND active=1", (email,))
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session.update(user_id=user["id"], name=user["name"], role=user["role"])
            flash(f"Qué gusto verte, {user['name']}.", "success")
            destination = "admin_dashboard" if user["role"] in {"admin", "empleado"} else "index"
            return redirect(request.args.get("next") or url_for(destination))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("index"))


def cart_details():
    raw_cart = session.get("cart", {})
    if not raw_cart:
        return [], Decimal("0")
    ids = [int(i) for i in raw_cart]
    placeholders = ",".join(["%s"] * len(ids))
    products = query_all(f"SELECT * FROM products WHERE id IN ({placeholders}) AND active=1", tuple(ids))
    items, total = [], Decimal("0")
    for product in products:
        quantity = min(int(raw_cart.get(str(product["id"]), 0)), product["stock"])
        if quantity <= 0:
            continue
        subtotal = Decimal(product["price"]) * quantity
        items.append({"product": product, "quantity": quantity, "subtotal": subtotal})
        total += subtotal
    return items, total


@app.post("/carrito/agregar/<int:product_id>")
def add_to_cart(product_id):
    product = query_one("SELECT id,stock FROM products WHERE id=%s AND active=1", (product_id,))
    if not product or product["stock"] <= 0:
        flash("Este producto no está disponible.", "warning")
    else:
        quantity = max(1, int(request.form.get("quantity", 1)))
        cart = session.get("cart", {})
        cart[str(product_id)] = min(int(cart.get(str(product_id), 0)) + quantity, product["stock"])
        session["cart"] = cart
        session.modified = True
        flash("Producto agregado al carrito.", "success")
    return redirect(request.referrer or url_for("catalog"))


@app.route("/carrito", methods=["GET", "POST"])
def cart():
    if request.method == "POST":
        cart_data = session.get("cart", {})
        for key in list(cart_data):
            quantity = max(0, int(request.form.get(f"qty_{key}", 0)))
            if quantity:
                cart_data[key] = quantity
            else:
                cart_data.pop(key, None)
        session["cart"] = cart_data
        session.modified = True
        flash("Carrito actualizado.", "success")
        return redirect(url_for("cart"))
    items, total = cart_details()
    return render_template("cart.html", items=items, total=total)


@app.get("/checkout")
@login_required
def checkout():
    items, total = cart_details()
    if not items:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for("catalog"))
    return render_template("checkout.html", items=items, total=total)


@app.post("/checkout/confirmar")
@login_required
def place_order():
    items, total = cart_details()
    if not items:
        return redirect(url_for("cart"))
    with get_db() as db:
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute("INSERT INTO orders(user_id,total,status,payment_method,shipping_address) VALUES(%s,%s,'pagada',%s,%s)",
                           (session["user_id"], total, request.form.get("payment_method", "Efectivo"), request.form.get("address", "Tienda física").strip()))
            order_id = cursor.lastrowid
            for item in items:
                product = item["product"]
                cursor.execute("SELECT stock FROM products WHERE id=%s FOR UPDATE", (product["id"],))
                current = cursor.fetchone()
                if not current or current["stock"] < item["quantity"]:
                    raise ValueError(f"Stock insuficiente para {product['name']}")
                cursor.execute("INSERT INTO order_items(order_id,product_id,product_name,unit_price,quantity,subtotal) VALUES(%s,%s,%s,%s,%s,%s)",
                               (order_id, product["id"], product["name"], product["price"], item["quantity"], item["subtotal"]))
                cursor.execute("UPDATE products SET stock=stock-%s WHERE id=%s", (item["quantity"], product["id"]))
            db.commit()
        except Exception as exc:
            db.rollback()
            flash(str(exc), "danger")
            return redirect(url_for("cart"))
    session["cart"] = {}
    flash("Compra realizada. Tu ticket ya está disponible.", "success")
    return redirect(url_for("ticket", order_id=order_id))


@app.get("/ticket/<int:order_id>")
@login_required
def ticket(order_id):
    order = query_one("""SELECT o.*,u.name,u.email FROM orders o JOIN users u ON u.id=o.user_id
                         WHERE o.id=%s AND (o.user_id=%s OR %s IN ('admin','empleado'))""", (order_id, session["user_id"], session["role"]))
    if not order:
        abort(404)
    items = query_all("SELECT * FROM order_items WHERE order_id=%s", (order_id,))
    return render_template("ticket.html", order=order, items=items)


@app.get("/mis-compras")
@login_required
def my_orders():
    return render_template("orders.html", orders=query_all("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC", (session["user_id"],)))


@app.get("/admin")
@admin_required
def admin_dashboard():
    stats = query_one("""SELECT
        (SELECT COALESCE(SUM(total),0) FROM orders WHERE status='pagada') revenue,
        (SELECT COUNT(*) FROM orders) orders_count,
        (SELECT COUNT(*) FROM users WHERE role='cliente' AND active=1) customers,
        (SELECT COUNT(*) FROM users WHERE role='empleado' AND active=1) employees,
        (SELECT COUNT(*) FROM products WHERE active=1) products,
        (SELECT COUNT(*) FROM products WHERE active=1 AND stock<=5) low_stock""")
    recent = query_all("SELECT o.*,u.name FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC LIMIT 6")
    best = query_all("""SELECT oi.product_name,SUM(oi.quantity) units,SUM(oi.subtotal) revenue
                        FROM order_items oi GROUP BY oi.product_name ORDER BY units DESC LIMIT 5""")
    monthly = query_all("""SELECT DATE_FORMAT(created_at,'%%Y-%%m') month,SUM(total) total
                           FROM orders WHERE created_at>=DATE_SUB(CURDATE(),INTERVAL 5 MONTH)
                           GROUP BY month ORDER BY month""")
    return render_template("admin/dashboard.html", stats=stats, recent=recent, best=best, monthly=monthly)


@app.route("/admin/productos", methods=["GET", "POST"])
@admin_required
def admin_products():
    if request.method == "POST":
        try:
            image = save_image(request.files.get("image")) or "img/producto-unisex.jpg"
            execute("""INSERT INTO products(name,description,price,cost,stock,category,size,image,featured)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (request.form["name"].strip(), request.form["description"].strip(), request.form["price"], request.form.get("cost", 0),
                     request.form["stock"], request.form["category"], request.form.get("size", "Unitalla"), image, bool(request.form.get("featured"))))
            flash("Producto publicado.", "success")
            return redirect(url_for("admin_products"))
        except (ValueError, KeyError) as exc:
            flash(str(exc), "danger")
    return render_template("admin/products.html", products=query_all("SELECT * FROM products ORDER BY active DESC,created_at DESC"))


@app.route("/admin/productos/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    product = query_one("SELECT * FROM products WHERE id=%s", (product_id,))
    if not product:
        abort(404)
    if request.method == "POST":
        try:
            image = save_image(request.files.get("image")) or product["image"]
            execute("""UPDATE products SET name=%s,description=%s,price=%s,cost=%s,stock=%s,category=%s,size=%s,image=%s,featured=%s WHERE id=%s""",
                    (request.form["name"].strip(), request.form["description"].strip(), request.form["price"], request.form.get("cost", 0), request.form["stock"],
                     request.form["category"], request.form.get("size", "Unitalla"), image, bool(request.form.get("featured")), product_id))
            flash("Producto actualizado.", "success")
            return redirect(url_for("admin_products"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/product_form.html", product=product)


@app.post("/admin/productos/<int:product_id>/estado")
@admin_required
def admin_product_status(product_id):
    execute("UPDATE products SET active=NOT active WHERE id=%s", (product_id,))
    flash("Estado del producto actualizado.", "success")
    return redirect(url_for("admin_products"))


@app.post("/admin/productos/<int:product_id>/eliminar")
@admin_required
def admin_product_delete(product_id):
    product = query_one("SELECT id,name FROM products WHERE id=%s", (product_id,))
    if not product:
        flash("El producto ya no existe.", "warning")
        return redirect(url_for("admin_products"))

    execute("DELETE FROM products WHERE id=%s", (product_id,))
    cart = session.get("cart", {})
    if str(product_id) in cart:
        cart.pop(str(product_id), None)
        session["cart"] = cart
        session.modified = True
    flash(f"Producto eliminado definitivamente: {product['name']}.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/trabajadores", methods=["GET", "POST"])
@admin_required
def admin_workers():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if query_one("SELECT id FROM users WHERE email=%s", (email,)):
            flash("El correo ya está registrado.", "warning")
        else:
            execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'empleado')",
                    (request.form["name"].strip(), email, generate_password_hash(request.form["password"])))
            flash("Trabajador registrado.", "success")
            return redirect(url_for("admin_workers"))
    workers = query_all("SELECT id,name,email,active,created_at FROM users WHERE role='empleado' ORDER BY created_at DESC")
    return render_template("admin/workers.html", workers=workers)


@app.post("/admin/trabajadores/<int:user_id>/estado")
@admin_required
def admin_worker_status(user_id):
    execute("UPDATE users SET active=NOT active WHERE id=%s AND role='empleado'", (user_id,))
    flash("Estado del trabajador actualizado.", "success")
    return redirect(url_for("admin_workers"))


@app.route("/admin/venta", methods=["GET", "POST"])
@admin_required
def admin_sale():
    products = query_all("SELECT id,name,price,stock FROM products WHERE active=1 AND stock>0 ORDER BY name")
    if request.method == "POST":
        product = query_one("SELECT * FROM products WHERE id=%s AND active=1", (request.form["product_id"],))
        quantity = int(request.form["quantity"])
        if not product or quantity < 1 or quantity > product["stock"]:
            flash("Cantidad no disponible.", "danger")
        else:
            customer = query_one("SELECT id FROM users WHERE email='mostrador@hardsquid.local'")
            if not customer:
                customer_id = execute("INSERT INTO users(name,email,password_hash,role) VALUES('Venta de mostrador','mostrador@hardsquid.local',%s,'cliente')", (generate_password_hash(secrets.token_urlsafe(20)),))
            else:
                customer_id = customer["id"]
            total = Decimal(product["price"]) * quantity
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("INSERT INTO orders(user_id,total,status,payment_method,shipping_address) VALUES(%s,%s,'pagada','Mostrador','Tienda física')", (customer_id, total))
                order_id = cursor.lastrowid
                cursor.execute("INSERT INTO order_items(order_id,product_id,product_name,unit_price,quantity,subtotal) VALUES(%s,%s,%s,%s,%s,%s)", (order_id, product["id"], product["name"], product["price"], quantity, total))
                cursor.execute("UPDATE products SET stock=stock-%s WHERE id=%s", (quantity, product["id"]))
                db.commit()
            flash(f"Venta #{order_id} registrada.", "success")
            return redirect(url_for("ticket", order_id=order_id))
    return render_template("admin/sale.html", products=products)


@app.get("/admin/reportes")
@admin_required
def admin_reports():
    sales = query_all("""SELECT o.id,o.created_at,u.name,o.payment_method,o.status,o.total
                         FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC LIMIT 100""")
    return render_template("admin/reports.html", sales=sales)


@app.get("/admin/reportes/ventas.csv")
@admin_required
def sales_csv():
    sales = query_all("""SELECT o.id,o.created_at,u.name,u.email,o.payment_method,o.status,o.total
                         FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC""")
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Folio", "Fecha", "Cliente", "Correo", "Método", "Estado", "Total"])
    for sale in sales:
        writer.writerow([sale["id"], sale["created_at"], sale["name"], sale["email"], sale["payment_method"], sale["status"], sale["total"]])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=ventas-hard-squid.csv"})


def initialize_database():
    database_name = DB_CONFIG["database"]
    if not database_name.replace("_", "").replace("-", "").isalnum():
        raise RuntimeError("Nombre de base de datos inválido.")

    with open(os.path.join(BASE_DIR, "schema.sql"), encoding="utf-8") as schema:
        sql = schema.read()

    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
        and not statement.strip().upper().startswith("CREATE DATABASE")
        and not statement.strip().upper().startswith("USE ")
    ]

    try:
        db = get_db(database=False)
        cursor = db.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{database_name}`")
    except Exception:
        db = get_db(database=True)
        cursor = db.cursor()

    with db:
        for statement in statements:
            cursor.execute(statement)
        db.commit()

    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email='admin@hardsquid.mx'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users(name,email,password_hash,role) VALUES(%s,%s,%s,'admin')",
                           ("Administrador Hard Squid", "admin@hardsquid.mx", generate_password_hash("Admin123!")))
            db.commit()


@app.cli.command("init-db")
def init_db_command():
    initialize_database()
    print("Base de datos preparada. Admin: admin@hardsquid.mx / Admin123!")


if os.getenv("AUTO_INIT_DB", "0") == "1":
    try:
        initialize_database()
    except Exception as exc:
        print(f"No se pudo inicializar la base automáticamente: {exc}")


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1", port=int(os.getenv("PORT", "5000")))
