#
# This was CS50!
# The app is used as a Final Project for CS50's Introduction to Computer Science
# https://cs50.harvard.edu/x/2020/
# by igor_voltaic @ https://github.com/igorvoltaic
# year 2020
#
# NOT PRODUCTION SOFTWARE
# DEMO ONLY
#

import os
import json

from cs50 import SQL
from uuid import uuid4
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

from helpers import apology, login_required, create_db_tables

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL(os.environ['DATABASE_URL'])
# Create database schema
create_db_tables()


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Return orders page"""

    # Today's date
    today = str(date.today())

    # User reached route via POST by submitting "add new" form
    if request.method == "POST":

        # Ensure order number was submitted
        if not request.form.get("number"):
            return apology("must provide order number", 400)

        # Ensure order date was submitted
        if not request.form.get("date"):
            return apology("must provide order date", 400)

        # Ensure order type was submitted
        if not request.form.get("order_type"):
            return apology("must provide order type", 400)

        # Ensure sender's id was submitted
        if not request.form.get("from_id"):
            return apology("must provide sender", 400)

        # Ensure reciever's id was submitted
        if not request.form.get("to_id"):
            return apology("must provide reciever", 400)

        uuid = str(uuid4())

        # Insert new customer into DB
        db.execute("INSERT INTO order_list (uuid, number, date, type, from_id, to_id, status) "
                   + "VALUES (:uuid, :number, :date, :order_type, :from_id, :to_id, '0')",
                   uuid=uuid, number=request.form.get("number"), date=request.form.get("date"),
                   order_type=request.form.get("order_type"), from_id=request.form.get("from_id"),
                   to_id=request.form.get("to_id"))

        # user reached route via get (as by clicking a link or via redirect)
        return redirect("/edit_order?order_uuid=" + uuid)

    order_list = db.execute("SELECT id, number, uuid, date, type, status, IFNULL((SELECT SUM(qty * price) "
                            + "FROM order_items WHERE order_id = order_list.id), 0) AS amount FROM order_list")

    if not order_list:
        order_list = None

    return render_template("orders.html", today=today, order_list=order_list)


@app.route("/edit_order", methods=["GET", "POST"])
@login_required
def edit_order():
    """Return edit order page"""

    # Fetch order data
    order = db.execute("SELECT id, number, uuid, date, type, status, from_id, to_id FROM order_list WHERE uuid = :order_uuid",
                       order_uuid=request.args.get("order_uuid"))[0]

    # User reached route via POST by submitting "add new" form
    if request.method == "POST":

        # Ensure order item was submitted
        if request.form.get("new_order_item"):
            product_id, price = request.form.get("new_order_item").split(";")
            qty = request.form.get("qty")
            # Insert new customer into DB
            db.execute("INSERT INTO order_items (order_id, product_id, qty, price) "
                       + "VALUES (:order_id, :product_id, :qty, :price)",
                       order_id=order['id'], product_id=product_id, qty=qty, price=price)

    # Query database for sender and reciever name and address
    if order['type'] == 1:  # Sell order: WH -> Customer
        sender = db.execute("SELECT name, address FROM warehouses WHERE id = :from_id", from_id=order['from_id'])[0]
        reciever = db.execute("SELECT name, address  FROM customers WHERE id = :to_id", to_id=order['to_id'])[0]
    if order['type'] == 2:  # Buy order: Supplier -> WH, products are being added to WH stock
        sender = db.execute("SELECT name, address FROM suppliers WHERE id = :from_id", from_id=order['from_id'])[0]
        reciever = db.execute("SELECT name, address FROM warehouses WHERE id = :to_id", to_id=order['to_id'])[0]
    if order['type'] == 3:  # Move order: WH -> WH
        sender = db.execute("SELECT name, address FROM warehouses WHERE id = :from_id", from_id=order['from_id'])[0]
        reciever = db.execute("SELECT name, address FROM warehouses WHERE id = :to_id", to_id=order['to_id'])[0]

    # Fetch order items
    products = db.execute("SELECT id, name, price FROM products WHERE status = 1")

    # Fetch order items
    order_items = db.execute("SELECT order_items.id, product_id, qty, order_items.price, products.name, products.description, products.unit "
                             + "FROM order_items "
                             + "LEFT JOIN products ON order_items.product_id = products.id "
                             + "WHERE order_id = :order_id", order_id=order['id'])

    # calculate order total amount
    amount = 0
    for row in order_items:
        amount += row['qty'] * row['price']

    return render_template("edit_order.html", sender=sender, reciever=reciever, order=order, products=products, order_items=order_items, amount=amount)


@app.route("/update_order_item", methods=["POST"])
@login_required
def update_order_item():
    """ Update order item """

    db.execute("UPDATE order_items SET qty = :qty WHERE id = :item_id",
               item_id=request.form.get("id"), qty=request.form.get("qty"))

    # fetch uuid to redirect back to the order
    uuid = request.form.get("order_uuid")

    # redirect to back to the order
    return redirect("/edit_order?order_uuid=" + uuid)


@app.route("/remove_order_item", methods=["POST"])
@login_required
def remove_order_item():
    """ Remove order item """

    db.execute("DELETE FROM order_items WHERE id = :item_id",
               item_id=request.form.get("id"))

    # fetch uuid to redirect back to the order
    uuid = request.form.get("order_uuid")

    # redirect to back to the order
    return redirect("/edit_order?order_uuid=" + uuid)


@app.route("/order_status", methods=["POST"])
@login_required
def order_status():
    """ Update order status """

    order_route = request.form.get("order_status_route")

    db.execute("UPDATE order_list SET status=:status WHERE id=:order_id",
               order_id=request.form.get("id"), status=request.form.get("status"))

    # User reached route via GET (as by clicking a link or via redirect)
    if order_route:
        return redirect(order_route)
    else:
        return redirect("/")


@app.route("/ordertype", methods=["GET"])
def ordertype():
    """AJAX functionality which returns recievers' and senders' arrays in json format"""

    # Get order type form the query
    type = int(request.args.get("type"))

    # query database for warehouses, suppliers, customers
    warehouses = db.execute("SELECT id, name FROM warehouses WHERE status = 1")
    suppliers = db.execute("SELECT id, name FROM suppliers WHERE status = 1")
    customers = db.execute("SELECT id, name  FROM customers WHERE status = 1")

    # Ensure username not exists
    if type == 1:
        return jsonify(json.dumps({"from": warehouses, "to": customers})), 200
    if type == 2:
        return jsonify(json.dumps({"from": suppliers, "to": warehouses})), 200
    if type == 3:
        return jsonify(json.dumps({"from": warehouses, "to": warehouses})), 200


@app.route("/fetchunit", methods=["GET"])
def fetchunit():
    """AJAX functionality which returns product unit"""

    # fetch id (price is not needed)
    product_id, price = request.args.get("id").split(";")

    # query database for warehouses, suppliers, customers
    unit = db.execute("SELECT unit FROM products WHERE id = :product_id", product_id=int(product_id))[0]['unit']

    return unit, 200


@app.route("/inventorize", methods=["GET", "POST"])
@login_required
def inventorize():
    """ Return orders page """

    # Today's date
    today = str(date.today())

    # User reached route via POST by submitting "add new" form
    if request.method == "POST":

        # Ensure inventory date was submitted
        if not request.form.get("date"):
            return apology("must provide inventory date", 400)

        # Ensure warehouse id was submitted
        if not request.form.get("warehouse_id"):
            return apology("must provide warehouse", 400)

        uuid = str(uuid4())

        # Insert new inventory into DB
        db.execute("INSERT INTO inventory_list (uuid, date, warehouse_id, status) "
                   + "VALUES (:uuid, :date, :warehouse_id, '0')",
                   uuid=uuid, date=request.form.get("date"),
                   warehouse_id=request.form.get("warehouse_id"))

        # user reached route via get (as by clicking a link or via redirect)
        return redirect("/edit_inventory?inventory_uuid=" + uuid)

    inventory_list = db.execute("SELECT id, uuid, date, status FROM inventory_list")

    warehouses = db.execute("SELECT id, name FROM warehouses WHERE status = 1")

    if not inventory_list:
        inventory_list = None

    return render_template("inventory_list.html", today=today, inventory_list=inventory_list, warehouses=warehouses)


@app.route("/edit_inventory", methods=["GET", "POST"])
@login_required
def edit_inventory():
    """ Return edit inventory page """

    # Fetch inventory data
    inventory = db.execute("SELECT id, uuid, date, status, warehouse_id FROM inventory_list WHERE uuid = :inventory_uuid",
                           inventory_uuid=request.args.get("inventory_uuid"))[0]

    # User reached route via POST by submitting "add new" form
    if request.method == "POST":

        if not db.execute("SELECT inventory_items.id FROM inventory_items "
                          + "LEFT JOIN inventory_list ON inventory_items.inventory_id = inventory_list.id "
                          + "WHERE product_id = :product_id AND inventory_id = :inventory_id",
                          product_id=request.form.get("new_inventory_item"), inventory_id=inventory['id']):
            # Insert new item into DB
            db.execute("INSERT INTO inventory_items (inventory_id, product_id) "
                       + "VALUES (:inventory_id, :product_id)",
                       inventory_id=inventory['id'], product_id=request.form.get("new_inventory_item"))

    # Fetch product list
    products = db.execute("SELECT products.id, name FROM products LEFT JOIN inventory_items ON products.id = inventory_items.product_id "
                          + "WHERE products.status = 1 AND products.id NOT IN (SELECT product_id FROM inventory_items WHERE inventory_id = :inventory_id)",
                          inventory_id=inventory['id'])

    # Fetch warehouse name
    warehouse = db.execute("SELECT name FROM warehouses WHERE id = :warehouse_id",
                           warehouse_id=inventory['warehouse_id'])[0]['name']

    # Fetch order items
    inventory_items = db.execute("SELECT Z.product_id, ii.id AS inv_id, name, description, IFNULL(SUM(Z.qty),0) AS qty, IFNULL(ii.qty,0) AS inv_qty FROM ("
                                 + "SELECT product_id, SUM(qty) AS qty FROM inventory_items LEFT JOIN inventory_list ON inventory_id = inventory_list.id "
                                 + "WHERE status = 1 AND warehouse_id = :warehouse_id GROUP BY product_id "
                                 + "UNION "
                                 + "SELECT product_id, SUM(qty) AS qty FROM order_items LEFT JOIN order_list ON order_id = order_list.id "
                                 + "WHERE status = 1 AND type = 2 AND to_id = :warehouse_id GROUP BY product_id "
                                 + "UNION "
                                 + "SELECT product_id, -(SUM(qty)) AS qty FROM order_items LEFT JOIN order_list ON order_id = order_list.id "
                                 + "WHERE status = 1 AND type = 1 AND from_id = :warehouse_id GROUP BY product_id "
                                 + "UNION "
                                 + "SELECT product_id, SUM(qty) AS qty FROM order_items LEFT JOIN order_list ON order_id = order_list.id "
                                 + "WHERE status = 1 AND type = 3 AND to_id = :warehouse_id GROUP BY product_id "
                                 + "UNION "
                                 + "SELECT product_id, -(SUM(qty)) AS qty FROM order_items LEFT JOIN order_list ON order_id = order_list.id "
                                 + "WHERE status = 1 AND type = 3 AND from_id = :warehouse_id GROUP BY product_id"
                                 + "UNION "
                                 + "SELECT product_id, SUM(qty) AS qty FROM inventory_items LEFT JOIN inventory_list ON inventory_id = inventory_list.id "
                                 + "WHERE inventory_id = inventory_id GROUP BY product_id) AS Z "
                                 + "LEFT JOIN products ON products.id = Z.product_id "
                                 + "LEFT JOIN inventory_items AS ii ON ii.product_id = Z.product_id "
                                 + "WHERE ii.inventory_id = :inventory_id "
                                 + "GROUP BY Z.product_id",
                                 inventory_id=inventory['id'], warehouse_id=inventory['warehouse_id'])

    return render_template("edit_inventory.html", inventory=inventory, products=products, inventory_items=inventory_items, warehouse=warehouse)


@app.route("/inventory_status", methods=["POST"])
@login_required
def inventory_status():
    """ Update inventory status """

    inventory_route = request.form.get("inventory_status_route")

    db.execute("UPDATE inventory_list SET status = :status WHERE id = :inventory_id",
               inventory_id=request.form.get("id"), status=request.form.get("status"))

    # User reached route via GET (as by clicking a link or via redirect)
    if inventory_route:
        return redirect(inventory_route)
    else:
        return redirect("/")


@app.route("/update_inventory_item", methods=["POST"])
@login_required
def update_inventory_item():
    """ Update order item """

    # Fetch old and new quantity
    old_qty = request.form.get("old_qty")
    new_qty = request.form.get("new_qty")
    qty = float(new_qty) - float(old_qty)

    db.execute("UPDATE inventory_items SET qty = :qty WHERE id = :item_id",
               item_id=request.form.get("id"), qty=qty)

    # fetch uuid to redirect back to the inventory
    uuid = request.form.get("inventory_uuid")

    # redirect to back to the inventory
    return redirect("/edit_inventory?inventory_uuid=" + uuid)


@app.route("/remove_inventory_item", methods=["POST"])
@login_required
def remove_inventory_item():
    """ Remove inventory item """

    db.execute("DELETE FROM inventory_items WHERE id = :item_id",
               item_id=request.form.get("id"))

    # fetch uuid to redirect back to the inventory
    uuid = request.form.get("inventory_uuid")

    # redirect to back to the inventory
    return redirect("/edit_inventory?inventory_uuid=" + uuid)


@app.route("/customers", methods=["GET", "POST"])
@login_required
def customers():
    """Return customers page"""

    # User reached route via POST by submitting "add new" form
    if request.method == "POST":

        # Ensure customer's name was submitted
        if not request.form.get("name"):
            return apology("must provide customer's name", 403)

        # Ensure tax payer number was submitted
        if not request.form.get("tax"):
            return apology("must provide tax payer number", 403)

        # Insert new customer into DB
        db.execute("INSERT INTO customers (name, address, status, tax) VALUES (:name, :address, :status, :tax)",
                   name=request.form.get("name"), address=request.form.get("address"),
                   status=request.form.get("status"), tax=request.form.get("tax"))

        # User reached route via GET (as by clicking a link or via redirect)
        return redirect("/customers")

    customers = db.execute("SELECT id, name, address, tax, status FROM customers")

    if not customers:
        customers = None

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("customers.html", customers=customers)


@app.route("/edit_customer", methods=["POST"])
@login_required
def edit_customer():
    """ Update customer """

    db.execute("UPDATE customers SET status=:status WHERE id=:customer_id",
               customer_id=request.form.get("id"), status=request.form.get("status"))

    # User reached route via GET (as by clicking a link or via redirect)
    return redirect("/customers")


@app.route("/suppliers", methods=["GET", "POST"])
@login_required
def suppliers():
    """Return suppliers page"""

    # User reached route via POST by submitting "add new" form
    if request.method == "POST":

        # Ensure supplier's name was submitted
        if not request.form.get("name"):
            return apology("must provide supplier's name", 403)

        # Ensure tax payer number was submitted
        if not request.form.get("tax"):
            return apology("must provide tax payer number", 403)

        # Insert new supplier into DB
        db.execute("INSERT INTO suppliers (name, address, status, tax) VALUES (:name, :address, :status, :tax)",
                   name=request.form.get("name"), address=request.form.get("address"),
                   status=request.form.get("status"), tax=request.form.get("tax"))

        # User reached route via GET (as by clicking a link or via redirect)
        return redirect("/suppliers")

    suppliers = db.execute("SELECT id, name, address, tax, status FROM suppliers")

    if not suppliers:
        suppliers = None

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("suppliers.html", suppliers=suppliers)


@app.route("/edit_supplier", methods=["POST"])
@login_required
def edit_supplier():
    """ Update supplier """

    db.execute("UPDATE suppliers SET status=:status WHERE id=:supplier_id",
               supplier_id=request.form.get("id"), status=request.form.get("status"))

    # User reached route via GET (as by clicking a link or via redirect)
    return redirect("/suppliers")


@app.route("/products", methods=["GET", "POST"])
@login_required
def products():
    """Return products  page"""

    # User reached route via POST by submitting "add new products" form
    if request.method == "POST":

        # Ensure product_name was submitted
        if not request.form.get("product_name"):
            return apology("must provide product name", 403)

        # Ensure price was submitted
        if not request.form.get("price"):
            return apology("must provide price", 403)

        # Ensure price is a number
        if not str(request.form.get("price")).replace('.', '').replace(',', '').isnumeric():
            return apology("price must be a number", 403)

        # Ensure unit was submitted
        if not request.form.get("unit"):
            return apology("must provide unit", 403)

        # Insert new warehouse to DB
        db.execute("INSERT INTO products (name, price, barcode, description, unit, status) "
                   + "VALUES (:name, :price, :barcode, :description, :unit, :status)",
                   name=request.form.get("product_name"), price=request.form.get("price"),
                   unit=request.form.get("unit"), barcode=request.form.get("barcode"),
                   description=request.form.get("description"), status=request.form.get("status"))

        # User reached route via GET (as by clicking a link or via redirect)
        return redirect("/products")

    products = db.execute("SELECT id, name, price, barcode, description, unit, status FROM products")

    if not products:
        products = None

    return render_template("products.html", products=products)


@app.route("/edit_product", methods=["POST"])
@login_required
def edit_product():
    """ Update a product """

    # Ensure price was submitted
    if not request.form.get("price"):
        return apology("must provide price", 403)

    # Ensure price is a number
    if not str(request.form.get("price")).replace('.', '').replace(',', '').isnumeric():
        return apology("price must be a number", 403)

    db.execute("UPDATE products SET price=:price, status=:status WHERE id=:product_id",
               product_id=request.form.get("id"), price=request.form.get("price"),
               status=request.form.get("status"))

    # User reached route via GET (as by clicking a link or via redirect)
    return redirect("/products")


@app.route("/warehouses", methods=["GET", "POST"])
@login_required
def warehouses():
    """Return warehouses page"""

    # User reached route via POST by submitting "add new warehouse" form
    if request.method == "POST":

        # Ensure warehouse-name was submitted
        if not request.form.get("warehouse_name"):
            return apology("must provide warehouse name", 403)

        # Insert new warehouse to DB
        db.execute("INSERT INTO warehouses (name, address, status) VALUES (:name, :address, :status)",
                   name=request.form.get("warehouse_name"), address=request.form.get("warehouse_address"),
                   status=request.form.get("warehouse_status"))

        # User reached route via GET (as by clicking a link or via redirect)
        return redirect("/warehouses")

    warehouses = db.execute("SELECT id, name, address, status FROM warehouses")

    if not warehouses:
        warehouses = None

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("warehouses.html", warehouses=warehouses)


@app.route("/edit_warehouse", methods=["POST"])
@login_required
def edit_warehouse():
    """ Update a warehouse """

    db.execute("UPDATE warehouses SET status=:status WHERE id=:warehouse_id",
               warehouse_id=request.form.get("id"), status=request.form.get("status"))

    # User reached route via GET (as by clicking a link or via redirect)
    return redirect("/warehouses")


@app.route("/current_stock_report")
@login_required
def current_stock_report():
    """ Shows current stock report product """

    # Fetch current product stock grouped by warehouses and products
    current_stock = db.execute("SELECT Z.product_id AS p_id, w.name AS w_name, w.address AS w_addr, "
                               + "p.name AS p_name, p.description AS p_desc, IFNULL(SUM(Z.qty),0) AS qty FROM ("
                               # add all item quantities from inventories
                               + "SELECT product_id, warehouse_id, SUM(qty) AS qty FROM inventory_items "
                               + "LEFT JOIN inventory_list ON inventory_id = inventory_list.id "
                               + "WHERE status = 1 GROUP BY product_id,warehouse_id "
                               + "UNION "
                               # add all item quantities from BUY orders
                               + "SELECT product_id, to_id AS warehouse_id, SUM(qty) AS qty FROM order_items "
                               + "LEFT JOIN order_list ON order_id = order_list.id "
                               + "WHERE status = 1 AND type = 2 GROUP BY product_id,warehouse_id "
                               + "UNION "
                               # substract all items quantities from SELL orders
                               + "SELECT product_id, from_id AS warehouse_id, -(SUM(qty)) AS qty FROM order_items "
                               + "LEFT JOIN order_list ON order_id = order_list.id "
                               + "WHERE status = 1 AND type = 1 GROUP BY product_id,warehouse_id "
                               + "UNION "
                               # add all item quantities from MOVE orders
                               + "SELECT product_id, to_id AS warehouse_id, SUM(qty) AS qty FROM order_items "
                               + "LEFT JOIN order_list ON order_id = order_list.id "
                               + "WHERE status = 1 AND type = 3 GROUP BY product_id,warehouse_id "
                               + "UNION "
                               # substract all item quantities from MOVE orders
                               + "SELECT product_id, from_id AS warehouse_id, -(SUM(qty)) AS qty FROM order_items "
                               + "LEFT JOIN order_list ON order_id = order_list.id "
                               + "WHERE status = 1 AND type = 3 GROUP BY product_id,warehouse_id) AS Z "
                               + "LEFT JOIN products AS p ON p.id = Z.product_id "
                               + "LEFT JOIN warehouses AS w on warehouse_id = w.id GROUP BY warehouse_id, Z.product_id")

    # User reached route via GET by clicking the link
    return render_template("current_stock_report.html", current_stock=current_stock)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 400)

        # Ensure password match confirmation
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password and confirmation do not match", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username not exists
        if len(rows) > 0:
            return apology("username already exists", 400)

        # Generate password hash
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Insert username and hash to the database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                   username=request.form.get("username"), hash=hash)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
