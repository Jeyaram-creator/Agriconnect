from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ------------------------------------------------
# SECRET KEY
# ------------------------------------------------

app.secret_key = "agriculture_marketplace_secret_key"


# ------------------------------------------------
# MYSQL CONFIGURATION
# ------------------------------------------------

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "agriculture_marketplace"

mysql = MySQL(app)


# ------------------------------------------------
# HOME
# ------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# ------------------------------------------------
# LOGIN
# ------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT
                user_id,
                fullname,
                email,
                password,
                role,
                status
            FROM users
            WHERE email = %s
        """, (email,))

        user = cur.fetchone()

        cur.close()

        # User not found
        if not user:

            flash(
                "Invalid email or password.",
                "danger"
            )

            return redirect(url_for("login"))

        user_id = user[0]
        fullname = user[1]
        stored_password = user[3]

        # Convert role to lowercase
        role = str(user[4]).lower()

        status = user[5]

        # Check account status
        if status == "blocked":

            flash(
                "Your account has been blocked.",
                "danger"
            )

            return redirect(url_for("login"))

        # Check password
        if check_password_hash(
            stored_password,
            password
        ):

            # Clear old session
            session.clear()

            # Store login information
            session["user_id"] = user_id
            session["fullname"] = fullname
            session["email"] = email
            session["role"] = role

            # Farmer login
            if role == "farmer":

                flash(
                    "Farmer login successful!",
                    "success"
                )

                return redirect(
                    url_for("farmer_dashboard")
                )

            # Admin login
            elif role == "admin":

                flash(
                    "Admin login successful!",
                    "success"
                )

                return redirect(
                    url_for("admin_dashboard")
                )

            # Customer login
            elif role == "customer":

                flash(
                    "Customer login successful!",
                    "success"
                )

                return redirect(
                    url_for("customer_dashboard")
                )

            else:

                flash(
                    "Invalid user role.",
                    "danger"
                )

                return redirect(
                    url_for("login")
                )

        else:

            flash(
                "Invalid email or password.",
                "danger"
            )

    return render_template(
        "login.html"
    )

# ------------------------------------------------
# REGISTER
# ------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form.get("fullname")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        # Hash password
        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()

        try:

            # Check existing email
            cur.execute(
                "SELECT user_id FROM users WHERE email = %s",
                (email,)
            )

            existing_user = cur.fetchone()

            if existing_user:

                flash("Email already registered.", "warning")
                return redirect(url_for("register"))

            # Insert user
            cur.execute("""
                INSERT INTO users
                (
                    fullname,
                    email,
                    password,
                    role,
                    status
                )
                VALUES
                (%s, %s, %s, %s, %s)
            """, (
                fullname,
                email,
                hashed_password,
                role,
                "active"
            ))

            user_id = cur.lastrowid

            # Create farmer profile
            if role == "farmer":

                cur.execute("""
                    INSERT INTO farmers
                    (user_id)
                    VALUES (%s)
                """, (user_id,))

            # Create customer profile
            elif role == "customer":

                cur.execute("""
                    INSERT INTO customers
                    (user_id)
                    VALUES (%s)
                """, (user_id,))

            mysql.connection.commit()

            flash(
                "Registration successful! Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except Exception as e:

            mysql.connection.rollback()

            print("Registration error:", e)

            flash(
                "Registration failed: " + str(e),
                "danger"
            )

        finally:

            cur.close()

    return render_template("register.html")

# ------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------

def admin_required(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":

            flash("Admin access required.")

            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    cur = mysql.connection.cursor()


    # Total farmers
    cur.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'farmer'
    """)

    farmers_count = cur.fetchone()[0] or 0


    # Total customers
    cur.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'customer'
    """)

    customers_count = cur.fetchone()[0] or 0


    # Total products
    cur.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    products_count = cur.fetchone()[0] or 0


    # Total orders
    cur.execute("""
        SELECT COUNT(*)
        FROM orders
    """)

    orders_count = cur.fetchone()[0] or 0

# Total sales

    cur.execute("""
        SELECT COALESCE(
            SUM(total_amount), 0
        )

        FROM orders

        WHERE order_status = 'delivered'
    """)

    total_sales = cur.fetchone()[0]



    # Recent orders
    cur.execute("""
        SELECT
            o.order_id,
            u.fullname,
            o.total_amount,
            o.order_status
        FROM orders o

        JOIN customers c
            ON o.customer_id = c.customer_id

        JOIN users u
            ON c.user_id = u.user_id

        ORDER BY o.order_date DESC

        LIMIT 5
    """)

    recent_orders = cur.fetchall()

    cur.close()

    return render_template(
        "admin/dashboard.html",
        farmers_count=farmers_count,
        customers_count=customers_count,
        products_count=products_count,
        orders_count=orders_count,
        total_sales=total_sales,
        recent_orders=recent_orders
    )

@app.route("/admin/farmers")
@admin_required
def admin_farmers():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            f.farmer_id,
            u.fullname,
            u.email,
            f.farm_name,
            f.location

        FROM farmers f

        JOIN users u
            ON f.user_id = u.user_id

        ORDER BY f.farmer_id DESC
    """)

    farmers = cur.fetchall()

    cur.close()

    return render_template(
        "admin/farmers.html",
        farmers=farmers
    )

@app.route(
    "/admin/farmer/delete/<int:farmer_id>"
)
@admin_required
def admin_delete_farmer(farmer_id):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT user_id
        FROM farmers
        WHERE farmer_id = %s
    """, (farmer_id,))

    farmer = cur.fetchone()


    if farmer:

        user_id = farmer[0]

        cur.execute("""
            DELETE FROM farmers
            WHERE farmer_id = %s
        """, (farmer_id,))

        cur.execute("""
            DELETE FROM users
            WHERE user_id = %s
        """, (user_id,))


        mysql.connection.commit()

        flash(
            "Farmer deleted successfully."
        )


    cur.close()


    return redirect(
        url_for("admin_farmers")
    )


@app.route("/admin/customers")
@admin_required
def admin_customers():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            c.customer_id,
            u.fullname,
            u.email,
            c.phone,
            c.address

        FROM customers c

        JOIN users u
            ON c.user_id = u.user_id

        ORDER BY c.customer_id DESC
    """)

    customers = cur.fetchall()

    cur.close()


    return render_template(
        "admin/customers.html",
        customers=customers
    )

@app.route("/admin/products")
@admin_required
def admin_products():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.quantity,
            p.price,
            u.fullname,
            p.status
        FROM products p

        JOIN farmers f
            ON p.farmer_id = f.farmer_id

        JOIN users u
            ON f.user_id = u.user_id

        ORDER BY p.product_id DESC
    """)

    products = cur.fetchall()

    cur.close()

    return render_template(
        "admin/products.html",
        products=products
    )

@app.route("/admin/partnerships")
@admin_required
def admin_partnerships():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            p.partnership_id,
            u1.fullname,
            u2.fullname,
            p.status,
            p.created_at
        FROM partnerships p

        JOIN farmers f1
            ON p.farmer_id = f1.farmer_id

        JOIN users u1
            ON f1.user_id = u1.user_id

        JOIN farmers f2
            ON p.partner_farmer_id = f2.farmer_id

        JOIN users u2
            ON f2.user_id = u2.user_id

        ORDER BY p.partnership_id DESC
    """)

    partnerships = cur.fetchall()

    cur.close()

    return render_template(
        "admin/partnerships.html",
        partnerships=partnerships
    )

@app.route("/admin/orders")
@admin_required
def admin_orders():

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            o.order_id,
            u.fullname,
            o.total_amount,
            o.payment_method,
            o.order_status,
            o.order_date

        FROM orders o

        JOIN customers c
            ON o.customer_id = c.customer_id

        JOIN users u
            ON c.user_id = u.user_id

        ORDER BY o.order_date DESC
    """)

    orders = cur.fetchall()

    cur.close()


    return render_template(
        "admin/orders.html",
        orders=orders
    )

@app.route(
    "/admin/order/status/<int:order_id>",
    methods=["POST"]
)
@admin_required
def update_order_status(order_id):

    status = request.form["status"]


    allowed_status = [
        "pending",
        "confirmed",
        "shipped",
        "delivered",
        "cancelled"
    ]


    if status not in allowed_status:

        flash("Invalid order status.")

        return redirect(
            url_for("admin_orders")
        )


    cur = mysql.connection.cursor()


    cur.execute("""
        UPDATE orders

        SET order_status = %s

        WHERE order_id = %s
    """, (
        status,
        order_id
    ))


    mysql.connection.commit()

    cur.close()


    flash(
        "Order status updated successfully."
    )


    return redirect(
        url_for("admin_orders")
    )

@app.route("/admin/sales")
@admin_required
def admin_sales():

    cur = mysql.connection.cursor()


    # Total sales

    cur.execute("""
        SELECT COALESCE(
            SUM(total_amount), 0
        )

        FROM orders

        WHERE order_status = 'delivered'
    """)

    total_sales = cur.fetchone()[0]


    # Total delivered orders

    cur.execute("""
        SELECT COUNT(*)

        FROM orders

        WHERE order_status = 'delivered'
    """)

    delivered_orders = cur.fetchone()[0]


    # Farmer-wise sales

    cur.execute("""
        SELECT
            u.fullname,
            SUM(oi.subtotal)

        FROM order_items oi

        JOIN farmers f
            ON oi.farmer_id = f.farmer_id

        JOIN users u
            ON f.user_id = u.user_id

        JOIN orders o
            ON oi.order_id = o.order_id

        WHERE o.order_status = 'delivered'

        GROUP BY f.farmer_id, u.fullname

        ORDER BY SUM(oi.subtotal) DESC
    """)

    farmer_sales = cur.fetchall()


    cur.close()


    return render_template(
        "admin/sales.html",

        total_sales=total_sales,

        delivered_orders=delivered_orders,

        farmer_sales=farmer_sales
    )
# ------------------------------------------------
# FARMER DASHBOARD
# ------------------------------------------------

def farmer_required(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):

        # Check login
        if "user_id" not in session:
            flash("Please login first.", "danger")
            return redirect(url_for("login"))

        # Check farmer role
        role = str(session.get("role", "")).lower()

        if role != "farmer":
            flash("Farmer access required.", "danger")
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper

def get_farmer_id():
    
    # Check user login
    if "user_id" not in session:
        return None

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT farmer_id
        FROM farmers
        WHERE user_id = %s
    """, (session["user_id"],))

    farmer = cur.fetchone()

    cur.close()

    if farmer:
        return farmer[0]

    return None

@app.route("/farmer/dashboard")
@farmer_required
def farmer_dashboard():

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()


    # Product count

    cur.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE farmer_id = %s
    """, (farmer_id,))

    products_count = cur.fetchone()[0] or 0


    # Total stock

    cur.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM products
        WHERE farmer_id = %s
    """, (farmer_id,))

    total_stock = cur.fetchone()[0] or 0


    # Orders count

    cur.execute("""
        SELECT COUNT(DISTINCT oi.order_id)
        FROM order_items oi
        WHERE oi.farmer_id = %s
    """, (farmer_id,))

    orders_count = cur.fetchone()[0] or 0


     # Sales
    cur.execute("""
        SELECT COALESCE(SUM(oi.subtotal), 0)

        FROM order_items oi

        JOIN orders o
            ON oi.order_id = o.order_id

        WHERE oi.farmer_id = %s
        AND o.order_status = 'delivered'
    """, (farmer_id,))

    total_sales = cur.fetchone()[0]


    # Recent products

    cur.execute("""
        SELECT
            product_name,
            category,
            quantity,
            unit,
            price,
            status
        FROM products
        WHERE farmer_id = %s
        ORDER BY product_id DESC
        LIMIT 5
    """, (farmer_id,))

    recent_products = cur.fetchall()

    cur.close()


    return render_template(
        "farmer/dashboard.html",
        products_count=products_count,
        total_stock=total_stock,
        orders_count=orders_count,
        total_sales=total_sales,
        recent_products=recent_products
    )

@app.route("/farmer/profile", methods=["GET", "POST"])
@farmer_required
def farmer_profile():

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()


    if request.method == "POST":

        phone = request.form["phone"]
        farm_name = request.form["farm_name"]
        location = request.form["location"]
        farm_size = request.form["farm_size"]
        address = request.form["address"]


        cur.execute("""
            UPDATE farmers

            SET
                phone = %s,
                farm_name = %s,
                location = %s,
                farm_size = %s,
                address = %s

            WHERE farmer_id = %s
        """, (
            phone,
            farm_name,
            location,
            farm_size,
            address,
            farmer_id
        ))


        mysql.connection.commit()

        flash("Profile updated successfully.")


    cur.execute("""
        SELECT
            u.fullname,
            u.email,
            f.phone,
            f.farm_name,
            f.location,
            f.farm_size,
            f.address

        FROM farmers f

        JOIN users u
            ON f.user_id = u.user_id

        WHERE f.farmer_id = %s
    """, (farmer_id,))


    profile = cur.fetchone()

    cur.close()


    return render_template(
        "farmer/profile.html",
        profile=profile
    )

@app.route("/farmer/products/add", methods=["GET", "POST"])
@farmer_required
def add_product():

    # Get farmer ID
    farmer_id = get_farmer_id()

    # Farmer profile does not exist
    if farmer_id is None:

        flash(
            "Farmer profile not found.",
            "danger"
        )

        return redirect(
            url_for("farmer_profile")
        )

    # POST request
    if request.method == "POST":

        product_name = request.form.get(
            "product_name"
        )

        category = request.form.get(
            "category"
        )

        description = request.form.get(
            "description"
        )

        quantity = request.form.get(
            "quantity"
        )

        unit = request.form.get(
            "unit"
        )

        price = request.form.get(
            "price"
        )

        location = request.form.get(
            "location"
        )

        # Image
        image = request.files.get("image")

        filename = None

        if image and image.filename:

            filename = secure_filename(
                image.filename
            )

            upload_folder = os.path.join(
                "static",
                "uploads",
                "products"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            image.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

        cur = mysql.connection.cursor()

        try:

            cur.execute("""
                INSERT INTO products
                (
                    farmer_id,
                    product_name,
                    category,
                    description,
                    quantity,
                    unit,
                    price,
                    location,
                    image,
                    status
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """, (
                farmer_id,
                product_name,
                category,
                description,
                quantity,
                unit,
                price,
                location,
                filename,
                "available"
            ))

            mysql.connection.commit()

            flash(
                "Product added successfully!",
                "success"
            )

            return redirect(
                url_for("farmer_products")
            )

        except Exception as e:

            mysql.connection.rollback()

            print(
                "Product insert error:",
                e
            )

            flash(
                "Error adding product.",
                "danger"
            )

        finally:

            cur.close()

    return render_template(
        "farmer/add_product.html"
    )

@app.route("/farmer/products")
@farmer_required
def farmer_products():

    farmer_id = get_farmer_id()

    if not farmer_id:
        flash("Farmer profile not found.")
        return redirect(url_for("login"))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            product_id,
            product_name,
            category,
            quantity,
            unit,
            price,
            status,
            image

        FROM products

        WHERE farmer_id = %s

        ORDER BY product_id DESC
    """, (farmer_id,))

    products = cur.fetchall()

    cur.close()

    return render_template(
        "farmer/products.html",
        products=products
    )

@app.route(
    "/farmer/products/edit/<int:product_id>",
    methods=["GET", "POST"]
)
@farmer_required
def edit_product(product_id):

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()


    if request.method == "POST":

        product_name = request.form["product_name"]
        category = request.form["category"]
        description = request.form["description"]
        quantity = request.form["quantity"]
        unit = request.form["unit"]
        price = request.form["price"]
        location = request.form["location"]
        status = request.form["status"]


        cur.execute("""
            UPDATE products

            SET
                product_name = %s,
                category = %s,
                description = %s,
                quantity = %s,
                unit = %s,
                price = %s,
                location = %s,
                status = %s

            WHERE product_id = %s
            AND farmer_id = %s
        """, (
            product_name,
            category,
            description,
            quantity,
            unit,
            price,
            location,
            status,
            product_id,
            farmer_id
        ))


        mysql.connection.commit()

        cur.close()

        flash("Product updated successfully.")

        return redirect(
            url_for("farmer_products")
        )


    cur.execute("""
        SELECT
            product_id,
            product_name,
            category,
            description,
            quantity,
            unit,
            price,
            location,
            status

        FROM products

        WHERE product_id = %s
        AND farmer_id = %s
    """, (product_id, farmer_id))


    product = cur.fetchone()

    cur.close()


    if not product:

        flash("Product not found.")

        return redirect(
            url_for("farmer_products")
        )


    return render_template(
        "farmer/edit_product.html",
        product=product
    )

@app.route(
    "/farmer/products/delete/<int:product_id>"
)
@farmer_required
def delete_product(product_id):

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()


    cur.execute("""
        DELETE FROM products

        WHERE product_id = %s
        AND farmer_id = %s
    """, (
        product_id,
        farmer_id
    ))


    mysql.connection.commit()

    cur.close()


    flash("Product deleted successfully.")

    return redirect(
        url_for("farmer_products")
    )

@app.route("/farmer/orders")
@farmer_required
def farmer_orders():

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()


    cur.execute("""
        SELECT
            o.order_id,
            u.fullname,
            p.product_name,
            oi.quantity,
            oi.price,
            oi.subtotal,
            o.order_status,
            o.order_date

        FROM order_items oi

        JOIN orders o
            ON oi.order_id = o.order_id

        JOIN customers c
            ON o.customer_id = c.customer_id

        JOIN users u
            ON c.user_id = u.user_id

        JOIN products p
            ON oi.product_id = p.product_id

        WHERE oi.farmer_id = %s

        ORDER BY o.order_date DESC
    """, (farmer_id,))


    orders = cur.fetchall()

    cur.close()


    return render_template(
        "farmer/orders.html",
        orders=orders
    )

@app.route("/farmer/find-farmers")
@farmer_required
def find_farmers():

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            f.farmer_id,
            u.fullname,
            f.farm_name,
            f.location,
            f.farm_size

        FROM farmers f

        JOIN users u
            ON f.user_id = u.user_id

        WHERE f.farmer_id != %s

        ORDER BY u.fullname
    """, (farmer_id,))

    farmers = cur.fetchall()

    cur.close()

    return render_template(
        "farmer/farmers.html",
        farmers=farmers
    )

@app.route(
    "/farmer/partnership/send/<int:partner_id>"
)
@farmer_required
def send_partnership(partner_id):

    farmer_id = get_farmer_id()

    if farmer_id == partner_id:

        flash(
            "You cannot partner with yourself."
        )

        return redirect(
            url_for("find_farmers")
        )


    cur = mysql.connection.cursor()


    # Check existing partnership

    cur.execute("""
        SELECT partnership_id

        FROM partnerships

        WHERE
        (
            farmer_id = %s
            AND partner_farmer_id = %s
        )

        OR

        (
            farmer_id = %s
            AND partner_farmer_id = %s
        )
    """, (
        farmer_id,
        partner_id,
        partner_id,
        farmer_id
    ))


    existing = cur.fetchone()


    if existing:

        cur.close()

        flash(
            "Partnership request already exists."
        )

        return redirect(
            url_for("find_farmers")
        )


    # Create request

    cur.execute("""
        INSERT INTO partnerships
        (
            farmer_id,
            partner_farmer_id,
            status
        )

        VALUES
        (
            %s,
            %s,
            'pending'
        )
    """, (
        farmer_id,
        partner_id
    ))


    mysql.connection.commit()

    cur.close()


    flash(
        "Partnership request sent successfully."
    )

    return redirect(
        url_for("find_farmers")
    )
@app.route("/farmer/partnerships")
@farmer_required
def my_partnerships():

    farmer_id = get_farmer_id()

    cur = mysql.connection.cursor()


    # Incoming requests

    cur.execute("""
        SELECT
            fp.partnership_id,
            u.fullname,
            f.farm_name,
            f.location,
            fp.status

        FROM partnerships fp

        JOIN farmers f
            ON fp.farmer_id = f.farmer_id

        JOIN users u
            ON f.user_id = u.user_id

        WHERE fp.partner_farmer_id = %s
        AND fp.status = 'pending'

        ORDER BY fp.created_at DESC
    """, (farmer_id,))


    requests = cur.fetchall()


    # Accepted partnerships

    cur.execute("""
        SELECT
            fp.partnership_id,
            u.fullname,
            f.farm_name,
            f.location,
            fp.status

        FROM partnerships fp

        JOIN farmers f
            ON (
                CASE
                    WHEN fp.farmer_id = %s
                    THEN fp.partner_farmer_id
                    ELSE fp.farmer_id
                END
            ) = f.farmer_id

        JOIN users u
            ON f.user_id = u.user_id

        WHERE
        (
            fp.farmer_id = %s
            OR fp.partner_farmer_id = %s
        )

        AND fp.status = 'accepted'

        ORDER BY fp.created_at DESC
    """, (
        farmer_id,
        farmer_id,
        farmer_id
    ))


    partnerships = cur.fetchall()

    cur.close()


    return render_template(
        "farmer/partnerships.html",
        requests=requests,
        partnerships=partnerships
    )

@app.route(
    "/farmer/partnership/respond/<int:partnership_id>/<action>"
)
@farmer_required
def respond_partnership(
    partnership_id,
    action
):

    farmer_id = get_farmer_id()


    if action not in ["accepted", "rejected"]:

        flash("Invalid action.")

        return redirect(
            url_for("my_partnerships")
        )


    cur = mysql.connection.cursor()


    cur.execute("""
        UPDATE partnerships

        SET status = %s

        WHERE partnership_id = %s

        AND partner_farmer_id = %s

        AND status = 'pending'
    """, (
        action,
        partnership_id,
        farmer_id
    ))


    mysql.connection.commit()

    cur.close()


    if action == "accepted":

        flash(
            "Partnership accepted successfully."
        )

    else:

        flash(
            "Partnership request rejected."
        )


    return redirect(
        url_for("my_partnerships")
    )

# ------------------------------------------------
# CUSTOMER DASHBOARD
# ------------------------------------------------

def customer_required(func):
    
    @wraps(func)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "customer":
            flash("Customer access required.")
            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper

def get_customer_id():
    
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT customer_id
        FROM customers
        WHERE user_id = %s
    """, (session["user_id"],))

    customer = cur.fetchone()

    cur.close()

    if customer:
        return customer[0]

    return None
@app.route("/customer/dashboard")
@customer_required
def customer_dashboard():

    cur = mysql.connection.cursor()

    # Get customer ID
    cur.execute("""
        SELECT customer_id
        FROM customers
        WHERE user_id = %s
    """, (session["user_id"],))

    customer = cur.fetchone()

    if not customer:
        cur.close()
        flash("Customer profile not found.", "danger")
        return redirect(url_for("logout"))

    customer_id = customer[0]

    # Total Orders
    cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE customer_id = %s
    """, (customer_id,))

    total_orders = cur.fetchone()[0] or 0


    # Pending Orders
    cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE customer_id = %s
        AND LOWER(order_status) = 'pending'
    """, (customer_id,))

    pending_orders = cur.fetchone()[0] or 0


    # Delivered Orders
    cur.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE customer_id = %s
        AND LOWER(order_status) = 'delivered'
    """, (customer_id,))

    delivered_orders = cur.fetchone()[0] or 0


    # Total Spent
    cur.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE customer_id = %s
        AND LOWER(order_status) != 'cancelled'
    """, (customer_id,))

    total_spent = cur.fetchone()[0] or 0


    cur.close()

    return render_template(
        "customer/dashboard.html",
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        total_spent=total_spent
    )

@app.route("/customer/products")
@customer_required
def customer_products():

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()


    cur = mysql.connection.cursor()


    query = """
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.quantity,
            p.unit,
            p.price,
            p.image,
            u.fullname

        FROM products p

        JOIN farmers f
            ON p.farmer_id = f.farmer_id

        JOIN users u
            ON f.user_id = u.user_id

        WHERE p.status = 'available'
        AND p.quantity > 0
    """


    params = []


    if search:

        query += """
            AND p.product_name LIKE %s
        """

        params.append(
            "%" + search + "%"
        )


    if category:

        query += """
            AND p.category = %s
        """

        params.append(category)


    query += """
        ORDER BY p.product_id DESC
    """


    cur.execute(
        query,
        tuple(params)
    )

    products = cur.fetchall()

    cur.close()


    return render_template(
        "customer/products.html",
        products=products,
        search=search
    )
@app.route(
    "/customer/product/<int:product_id>",
    methods=["GET", "POST"]
)
@customer_required
def product_details(product_id):

    cur = mysql.connection.cursor()


    if request.method == "POST":

        quantity = int(
            request.form["quantity"]
        )


        cur.execute("""
            SELECT
                quantity,
                price
            FROM products

            WHERE product_id = %s
            AND status = 'available'
        """, (product_id,))


        product_check = cur.fetchone()


        if not product_check:

            cur.close()

            flash("Product is not available.")

            return redirect(
                url_for("customer_products")
            )


        available_quantity = product_check[0]


        if quantity > available_quantity:

            cur.close()

            flash(
                "Requested quantity is not available."
            )

            return redirect(
                url_for(
                    "product_details",
                    product_id=product_id
                )
            )


        # Store cart in session

        cart = session.get(
            "cart",
            {}
        )


        product_key = str(product_id)


        if product_key in cart:

            new_quantity = (
                cart[product_key]["quantity"]
                + quantity
            )

            if new_quantity > available_quantity:

                cur.close()

                flash(
                    "Maximum available quantity exceeded."
                )

                return redirect(
                    url_for(
                        "product_details",
                        product_id=product_id
                    )
                )

            cart[product_key]["quantity"] = (
                new_quantity
            )

        else:

            cart[product_key] = {
                "quantity": quantity
            }


        session["cart"] = cart

        session.modified = True

        cur.close()


        flash("Product added to cart.")

        return redirect(
            url_for("customer_cart")
        )


    cur.execute("""
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            p.description,
            p.quantity,
            p.unit,
            p.price,
            p.location,
            p.image,
            u.fullname

        FROM products p

        JOIN farmers f
            ON p.farmer_id = f.farmer_id

        JOIN users u
            ON f.user_id = u.user_id

        WHERE p.product_id = %s
        AND p.status = 'available'
    """, (product_id,))


    product = cur.fetchone()

    cur.close()


    if not product:

        flash("Product not found.")

        return redirect(
            url_for("customer_products")
        )


    return render_template(
        "customer/product_details.html",
        product=product
    )
@app.route("/customer/cart")
@customer_required
def customer_cart():

    cart = session.get("cart", {})

    cart_items = []

    total = 0


    if cart:

        cur = mysql.connection.cursor()


        product_ids = [
            int(product_id)
            for product_id in cart.keys()
        ]


        for product_id in product_ids:

            cur.execute("""
                SELECT
                    p.product_id,
                    p.product_name,
                    p.price,
                    u.fullname

                FROM products p

                JOIN farmers f
                    ON p.farmer_id = f.farmer_id

                JOIN users u
                    ON f.user_id = u.user_id

                WHERE p.product_id = %s
            """, (product_id,))


            product = cur.fetchone()


            if product:

                quantity = cart[
                    str(product_id)
                ]["quantity"]


                subtotal = (
                    float(product[2])
                    * quantity
                )


                total += subtotal


                cart_items.append({
                    "product_id": product[0],
                    "product_name": product[1],
                    "price": product[2],
                    "farmer_name": product[3],
                    "quantity": quantity,
                    "subtotal": subtotal
                })


        cur.close()


    return render_template(
        "customer/cart.html",
        cart_items=cart_items,
        total=total
    )
@app.route(
    "/customer/cart/remove/<int:product_id>"
)
@customer_required
def remove_from_cart(product_id):

    cart = session.get("cart", {})

    product_key = str(product_id)


    if product_key in cart:

        del cart[product_key]

        session["cart"] = cart

        session.modified = True


    flash("Product removed from cart.")

    return redirect(
        url_for("customer_cart")
    )

@app.route(
    "/customer/checkout",
    methods=["GET", "POST"]
)
@customer_required
def checkout():

    customer_id = get_customer_id()

    cart = session.get("cart", {})


    if not cart:

        flash("Your cart is empty.")

        return redirect(
            url_for("customer_products")
        )


    cur = mysql.connection.cursor()

    cart_items = []

    total = 0


    # Get products

    for product_id, cart_data in cart.items():

        quantity = int(
            cart_data["quantity"]
        )


        cur.execute("""
            SELECT
                p.product_id,
                p.product_name,
                p.quantity,
                p.price,
                p.farmer_id

            FROM products p

            WHERE p.product_id = %s

            AND p.status = 'available'
        """, (int(product_id),))


        product = cur.fetchone()


        if not product:

            cur.close()

            flash(
                "One of the products is no longer available."
            )

            return redirect(
                url_for("customer_cart")
            )


        if quantity > product[2]:

            cur.close()

            flash(
                f"Only {product[2]} units of "
                f"{product[1]} are available."
            )

            return redirect(
                url_for("customer_cart")
            )


        subtotal = (
            float(product[3])
            * quantity
        )


        total += subtotal


        cart_items.append({
            "product_id": product[0],
            "product_name": product[1],
            "quantity": quantity,
            "price": product[3],
            "farmer_id": product[4],
            "subtotal": subtotal
        })


    if request.method == "POST":

        fullname = request.form["fullname"]
        phone = request.form["phone"]
        address = request.form["address"]
        payment_method = request.form[
            "payment_method"
        ]


        # Create order

        cur.execute("""
            INSERT INTO orders
            (
                customer_id,
                total_amount,
                delivery_address,
                phone,
                payment_method,
                order_status
            )

            VALUES
            (
                %s, %s, %s, %s, %s, %s
            )
        """, (
            customer_id,
            total,
            address,
            phone,
            payment_method,
            "pending"
        ))


        order_id = cur.lastrowid


        # Create order items

        for item in cart_items:

            cur.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    farmer_id,
                    quantity,
                    price,
                    subtotal
                )

                VALUES
                (
                    %s, %s, %s,
                    %s, %s, %s
                )
            """, (
                order_id,
                item["product_id"],
                item["farmer_id"],
                item["quantity"],
                item["price"],
                item["subtotal"]
            ))


            # Reduce stock

            cur.execute("""
                UPDATE products

                SET quantity =
                    quantity - %s

                WHERE product_id = %s
            """, (
                item["quantity"],
                item["product_id"]
            ))


        mysql.connection.commit()

        cur.close()


        # Empty cart

        session["cart"] = {}

        session.modified = True


        flash(
            "Order placed successfully!"
        )


        return redirect(
            url_for("customer_orders")
        )


    cur.close()


    return render_template(
        "customer/checkout.html",
        cart_items=cart_items,
        total=total
    )
@app.route("/customer/orders")
@customer_required
def customer_orders():

    customer_id = get_customer_id()

    cur = mysql.connection.cursor()


    cur.execute("""
        SELECT
            order_id,
            total_amount,
            payment_method,
            order_status,
            order_date

        FROM orders

        WHERE customer_id = %s

        ORDER BY order_date DESC
    """, (customer_id,))


    orders = cur.fetchall()

    cur.close()


    return render_template(
        "customer/orders.html",
        orders=orders
    )
@app.route(
    "/customer/profile",
    methods=["GET", "POST"]
)
@customer_required
def customer_profile():

    customer_id = get_customer_id()

    cur = mysql.connection.cursor()


    if request.method == "POST":

        phone = request.form["phone"]
        address = request.form["address"]


        cur.execute("""
            UPDATE customers

            SET
                phone = %s,
                address = %s

            WHERE customer_id = %s
        """, (
            phone,
            address,
            customer_id
        ))


        mysql.connection.commit()

        flash(
            "Profile updated successfully."
        )


    cur.execute("""
        SELECT
            u.fullname,
            u.email,
            c.phone,
            c.address

        FROM customers c

        JOIN users u
            ON c.user_id = u.user_id

        WHERE c.customer_id = %s
    """, (customer_id,))


    profile = cur.fetchone()

    cur.close()


    return render_template(
        "customer/profile.html",
        profile=profile
    )
# ------------------------------------------------
# LOGOUT
# ------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("login"))


# ------------------------------------------------
# RUN APPLICATION
# ------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)