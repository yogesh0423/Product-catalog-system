from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DB Helper ----------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Home ----------
@app.route("/")
def index():
    conn = get_db()
    q = request.args.get("q")
    if q:
        products = conn.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", 
                                ('%'+q+'%', '%'+q+'%')).fetchall()
    else:
        products = conn.execute("SELECT * FROM products").fetchall()
    return render_template("index.html", products=products)

# ---------- Auth ----------
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        conn = get_db()
        conn.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                     (name,email,password,"user"))
        conn.commit()
        flash("Signup successful, login now!")
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Login successful!")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out!")
    return redirect(url_for("index"))

# ---------- Admin: Products ----------
@app.route("/admin/products")
def admin_products():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = get_db()
    products = conn.execute("SELECT * FROM products").fetchall()
    return render_template("admin_products.html", products=products)

@app.route("/admin/products/add", methods=["GET","POST"])
def add_product():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    if request.method == "POST":
        name = request.form["name"]
        desc = request.form["description"]
        price = request.form["price"]
        stock = request.form["stock"]
        conn = get_db()
        conn.execute("INSERT INTO products (name,description,price,stock) VALUES (?,?,?,?)",
                     (name,desc,price,stock))
        conn.commit()
        return redirect(url_for("admin_products"))
    return render_template("add_product.html")

# ---------- Orders ----------
@app.route("/cart/add/<int:id>")
def add_cart(id):
    if "cart" not in session:
        session["cart"] = []
    session["cart"].append(id)
    flash("Added to cart!")
    return redirect(url_for("index"))

@app.route("/cart")
def cart():
    if "cart" not in session:
        session["cart"] = []
    ids = tuple(session["cart"]) if session["cart"] else (-1,)
    conn = get_db()
    items = conn.execute("SELECT * FROM products WHERE id IN (%s)" % ",".join("?"*len(ids)), ids).fetchall()
    return render_template("cart.html", items=items)

@app.route("/order", methods=["POST"])
def order():
    if "user_id" not in session:
        return redirect(url_for("login"))
    address = request.form["address"]
    conn = get_db()
    for pid in session.get("cart", []):
        conn.execute("INSERT INTO orders (user_id,product_id,address,status) VALUES (?,?,?,?)",
                     (session["user_id"], pid, address, "Pending"))
        conn.execute("UPDATE products SET stock=stock-1 WHERE id=?",(pid,))
    conn.commit()
    session["cart"] = []
    flash("Order placed!")
    return redirect(url_for("index"))

@app.route("/admin/orders")
def admin_orders():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    conn = get_db()
    orders = conn.execute("""SELECT o.id, u.name, p.name as product, o.address, o.status
                             FROM orders o 
                             JOIN users u ON o.user_id=u.id 
                             JOIN products p ON o.product_id=p.id""").fetchall()
    return render_template("admin_orders.html", orders=orders)

if __name__ == "__main__":
    conn = get_db()
    # Setup tables if not exist
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT, role TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, stock INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, address TEXT, status TEXT)")
    conn.commit()
    app.run(debug=True)
