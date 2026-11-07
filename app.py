import os
import sqlite3
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'college-devops-shopping-secret-key-2026')
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shopping.db')


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        address TEXT NOT NULL,
        phone TEXT NOT NULL,
        total_amount REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id)
    );
    """)

    # Seed Admin account if not present
    cursor.execute("SELECT id FROM users WHERE username = ?", ('admin',))
    if not cursor.fetchone():
        admin_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (name, email, username, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ('System Administrator', 'admin@shopping.local', 'admin', admin_hash, 'admin')
        )

    # Seed Customer account if not present
    cursor.execute("SELECT id FROM users WHERE username = ?", ('customer1',))
    if not cursor.fetchone():
        customer_hash = generate_password_hash('pass123')
        cursor.execute(
            "INSERT INTO users (name, email, username, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ('Alice Customer', 'customer1@shopping.local', 'customer1', customer_hash, 'customer')
        )

    # Seed products if empty
    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()['count'] == 0:
        sample_products = [
            (
                'Laptop Pro 15',
                'Electronics',
                'High-performance laptop featuring 16GB RAM, 512GB SSD, and fast Intel Core i7 processor.',
                899.99,
                15
            ),
            (
                'Wireless Noise-Cancelling Headphones',
                'Audio',
                'Premium over-ear Bluetooth headphones with active noise cancellation and 30-hour battery life.',
                129.99,
                30
            ),
            (
                'Mechanical Gaming Keyboard',
                'Accessories',
                'Tactile RGB backlit mechanical keyboard with blue switches and detachable USB-C braided cable.',
                69.50,
                25
            ),
            (
                'Smart Fitness Watch',
                'Wearables',
                'Waterproof smartwatch with continuous heart rate monitoring, sports modes, and GPS tracker.',
                49.99,
                40
            ),
            (
                'Ergonomic Office Chair',
                'Furniture',
                'High-back breathable mesh desk chair with adjustable lumbar support and flip-up armrests.',
                199.00,
                10
            ),
            (
                'Ultra HD 4K Monitor 27-inch',
                'Electronics',
                'Crisp 4K UHD IPS display with ultra-slim bezels, HDR 10 support, and dual HDMI ports.',
                299.99,
                20
            ),
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, description, price, stock) VALUES (?, ?, ?, ?, ?)",
            sample_products
        )

    db.commit()
    db.close()


# Ensure DB is created on startup
with app.app_context():
    init_db()


# Context Processors & Decorators
@app.context_processor
def inject_global_data():
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    return {
        'cart_count': cart_count,
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'name': session.get('name'),
            'role': session.get('role')
        } if 'user_id' in session else None
    }


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') == 'admin':
            flash('Administrators cannot perform customer shopping actions.', 'info')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- Routes ----------------

# 1. Product Catalogue / Home
@app.route('/')
def index():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    db = get_db()
    sql = "SELECT * FROM products WHERE 1=1"
    params = []

    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        term = f"%{query}%"
        params.extend([term, term, term])

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY id DESC"
    products = db.execute(sql, params).fetchall()

    # Get distinct categories for filter buttons
    categories = [row['category'] for row in db.execute("SELECT DISTINCT category FROM products ORDER BY category").fetchall()]

    return render_template('index.html', products=products, query=query, category=category, categories=categories)


# 2. Customer Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')



        if not name or not email or not username or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 4:
            flash('Password must be at least 4 characters long.', 'danger')
            return render_template('register.html')

        db = get_db()
        existing_user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing_user:
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (name, email, username, password_hash, role) VALUES (?, ?, ?, ?, 'customer')",
            (name, email, username, password_hash)
        )
        db.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# 3. Customer & Admin Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please provide both username and password.', 'danger')
            return render_template('login.html')

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            session['role'] = user['role']
            session['cart'] = {}

            flash(f"Welcome back, {user['name']}!", 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


# 4. Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# 5. Shopping Cart View
@app.route('/cart')
@customer_required
def cart_view():
    cart = session.get('cart', {})
    cart_items = []
    total_amount = 0.0

    if cart:
        db = get_db()
        product_ids = list(cart.keys())
        placeholders = ','.join(['?'] * len(product_ids))
        products = db.execute(
            f"SELECT * FROM products WHERE id IN ({placeholders})",
            product_ids
        ).fetchall()

        product_map = {str(p['id']): p for p in products}

        for pid_str, quantity in cart.items():
            if pid_str in product_map:
                prod = product_map[pid_str]
                subtotal = prod['price'] * quantity
                total_amount += subtotal
                cart_items.append({
                    'id': prod['id'],
                    'name': prod['name'],
                    'category': prod['category'],
                    'price': prod['price'],
                    'stock': prod['stock'],
                    'quantity': quantity,
                    'subtotal': subtotal
                })

    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)


# 6. Add to Cart
@app.route('/cart/add/<int:product_id>', methods=['POST'])
@customer_required
def add_to_cart(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('index'))

    if product['stock'] <= 0:
        flash(f"'{product['name']}' is currently out of stock.", 'warning')
        return redirect(url_for('index'))

    cart = session.get('cart', {})
    pid_str = str(product_id)
    current_qty = cart.get(pid_str, 0)

    if current_qty + 1 > product['stock']:
        flash(f"Cannot add more '{product['name']}'. Available stock is {product['stock']}.", 'warning')
    else:
        cart[pid_str] = current_qty + 1
        session['cart'] = cart
        flash(f"Added '{product['name']}' to your cart.", 'success')

    return redirect(request.referrer or url_for('cart_view'))


# 7. Update Cart Quantity
@app.route('/cart/update/<int:product_id>', methods=['POST'])
@customer_required
def update_cart(product_id):
    cart = session.get('cart', {})
    pid_str = str(product_id)

    try:
        new_qty = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        new_qty = 1

    if new_qty <= 0:
        cart.pop(pid_str, None)
        session['cart'] = cart
        flash('Item removed from cart.', 'info')
        return redirect(url_for('cart_view'))

    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        cart.pop(pid_str, None)
        session['cart'] = cart
        flash('Product no longer exists.', 'warning')
        return redirect(url_for('cart_view'))

    if new_qty > product['stock']:
        cart[pid_str] = product['stock']
        session['cart'] = cart
        flash(f"Requested quantity exceeds available stock. Adjusted to maximum available: {product['stock']}.", 'warning')
    else:
        cart[pid_str] = new_qty
        session['cart'] = cart
        flash(f"Updated quantity for '{product['name']}'.", 'success')

    return redirect(url_for('cart_view'))


# 8. Remove from Cart
@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@customer_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    pid_str = str(product_id)
    if pid_str in cart:
        cart.pop(pid_str)
        session['cart'] = cart
        flash('Item removed from cart.', 'info')
    return redirect(url_for('cart_view'))


# 9. Checkout & Order Placement
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
@customer_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty. Add products before proceeding to checkout.', 'warning')
        return redirect(url_for('cart_view'))

    db = get_db()
    product_ids = list(cart.keys())
    placeholders = ','.join(['?'] * len(product_ids))
    products = db.execute(
        f"SELECT * FROM products WHERE id IN ({placeholders})",
        product_ids
    ).fetchall()
    product_map = {str(p['id']): p for p in products}

    cart_items = []
    total_amount = 0.0

    for pid_str, quantity in cart.items():
        if pid_str in product_map:
            prod = product_map[pid_str]
            subtotal = prod['price'] * quantity
            total_amount += subtotal
            cart_items.append({
                'id': prod['id'],
                'name': prod['name'],
                'price': prod['price'],
                'stock': prod['stock'],
                'quantity': quantity,
                'subtotal': subtotal
            })

    if not cart_items:
        session['cart'] = {}
        flash('Your cart items are no longer available.', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        email = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()

        if not customer_name or not email or not address or not phone:
            flash('Please fill in all shipping details.', 'danger')
            return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)

        # Re-verify stock atomically before committing order
        for item in cart_items:
            current_prod = db.execute("SELECT stock, name FROM products WHERE id = ?", (item['id'],)).fetchone()
            if not current_prod or current_prod['stock'] < item['quantity']:
                flash(f"Insufficient stock for '{item['name']}'. Available: {current_prod['stock'] if current_prod else 0}. Please adjust your cart.", 'danger')
                return redirect(url_for('cart_view'))

        # Insert Order
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO orders (user_id, customer_name, email, address, phone, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session['user_id'], customer_name, email, address, phone, total_amount)
        )
        order_id = cursor.lastrowid

        # Insert Order Items & Update Stock
        for item in cart_items:
            cursor.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, price, quantity, subtotal)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (order_id, item['id'], item['name'], item['price'], item['quantity'], item['subtotal'])
            )
            cursor.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item['quantity'], item['id'])
            )

        db.commit()

        # Clear cart
        session['cart'] = {}
        flash('Order placed successfully! Thank you for your purchase.', 'success')
        return redirect(url_for('order_confirmation', order_id=order_id))

    return render_template('checkout.html', cart_items=cart_items, total_amount=total_amount)


# 10. Order Confirmation
@app.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('index'))

    # Ensure customers can only see their own order (admins can view any)
    if session.get('role') != 'admin' and order['user_id'] != session['user_id']:
        flash('Unauthorized access to order details.', 'danger')
        return redirect(url_for('index'))

    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return render_template('order_confirmation.html', order=order, items=items)


# 11. Customer Order History
@app.route('/orders')
@login_required
@customer_required
def order_history():
    db = get_db()
    orders = db.execute(
        """SELECT o.*, COUNT(oi.id) as item_count
           FROM orders o
           LEFT JOIN order_items oi ON o.id = oi.order_id
           WHERE o.user_id = ?
           GROUP BY o.id
           ORDER BY o.created_at DESC""",
        (session['user_id'],)
    ).fetchall()
    return render_template('order_history.html', orders=orders)


# 12. Order Details
@app.route('/orders/<int:order_id>')
@login_required
def order_details(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('order_history'))

    if session.get('role') != 'admin' and order['user_id'] != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('order_history'))

    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return render_template('order_details.html', order=order, items=items)


# 13. Admin Dashboard
@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    total_products = len(products)

    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    total_orders = len(orders)
    total_revenue = sum(order['total_amount'] for order in orders)

    customer_count = db.execute("SELECT COUNT(*) as count FROM users WHERE role = 'customer'").fetchone()['count']

    return render_template(
        'admin.html',
        products=products,
        orders=orders,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue,
        customer_count=customer_count
    )


# 14. Admin Add Product
@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '').strip()
        stock_raw = request.form.get('stock', '').strip()

        if not name or not category or not description or not price_raw or not stock_raw:
            flash('All product fields are required.', 'danger')
            return render_template('add_product.html')

        try:
            price = float(price_raw)
            stock = int(stock_raw)
            if price <= 0 or stock < 0:
                raise ValueError()
        except ValueError:
            flash('Price must be greater than 0 and stock cannot be negative.', 'danger')
            return render_template('add_product.html')

        db = get_db()
        db.execute(
            "INSERT INTO products (name, category, description, price, stock) VALUES (?, ?, ?, ?, ?)",
            (name, category, description, price, stock)
        )
        db.commit()

        flash(f"Product '{name}' added successfully!", 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_product.html')


# 15. Admin Edit Product
@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '').strip()
        stock_raw = request.form.get('stock', '').strip()

        if not name or not category or not description or not price_raw or not stock_raw:
            flash('All fields are required.', 'danger')
            return render_template('edit_product.html', product=product)

        try:
            price = float(price_raw)
            stock = int(stock_raw)
            if price <= 0 or stock < 0:
                raise ValueError()
        except ValueError:
            flash('Price must be greater than 0 and stock cannot be negative.', 'danger')
            return render_template('edit_product.html', product=product)

        db.execute(
            """UPDATE products
               SET name = ?, category = ?, description = ?, price = ?, stock = ?
               WHERE id = ?""",
            (name, category, description, price, stock, product_id)
        )
        db.commit()

        flash(f"Product '{name}' updated successfully!", 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_product.html', product=product)


# 16. Admin Delete Product
@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash(f"Product '{product['name']}' has been deleted.", 'info')
    else:
        flash('Product not found.', 'danger')

    return redirect(url_for('admin_dashboard'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
