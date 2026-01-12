import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")

# Create tables
conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    price REAL,
    stock INTEGER
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    address TEXT,
    status TEXT
)
""")

# Insert admin user (only if not exists)
email = "admin@example.com"
password = "admin123"
hashed = generate_password_hash(password)

cur = conn.cursor()
cur.execute("SELECT * FROM users WHERE email=?", (email,))
if not cur.fetchone():
    conn.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                 ("Admin", email, hashed, "admin"))
    print("✅ Admin user created -> email: admin@example.com, password: admin123")

# Insert sample products
sample_products = [
    ("Laptop", "Powerful laptop for work and gaming", 60000, 10),
    ("Smartphone", "Latest 5G smartphone with AMOLED display", 30000, 15),
    ("Headphones", "Noise-cancelling over-ear headphones", 5000, 20),
    ("Smartwatch", "Track your health and fitness", 8000, 25),
]

for p in sample_products:
    conn.execute("INSERT INTO products (name,description,price,stock) VALUES (?,?,?,?)", p)

conn.commit()
conn.close()
print("✅ Database initialized with admin + sample products")
