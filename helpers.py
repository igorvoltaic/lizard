import requests
import os

from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def create_db_tables():
    """ Create database tables """

    # Configure CS50 Library to use SQLite database
    db = SQL(os.environ['DATABASE_URL'])

    # Create users table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS users ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "username TEXT NOT NULL, hash TEXT NOT NULL)")

    # Create products table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS products ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "name TEXT NOT NULL, "
                + "price FLOAT NOT NULL, "
                + "description TEXT, "
                + "unit TEXT NOT NULL, "
                + "barcode INTEGE RNOT NULL, "
                + "status INTEGER NOT NULL)")

    # Create customers table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS customers ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "name TEXT NOT NULL, "
                + "address TEXT, "
                + "tax INTEGER NOT NULL, "
                + "status INTEGER NOT NULL)")

    # Create suppliers table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS suppliers ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "name TEXT NOT NULL, "
                + "address TEXT, "
                + "tax INTEGER NOT NULL, "
                + "status INTEGER NOT NULL)")

    # Create warehouses table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS warehouses ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "name TEXT NOT NULL, "
                + "address TEXT, "
                + "status INTEGER NOT NULL)")

    # Create order_list table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS order_list ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "uuid TEXT NOT NULL UNIQUE, "
                + "number TEXT NOT NULL, "
                + "date DATE NOT NULL, "
                + "type INTEGER NOT NULL, "
                + "from_id INTEGER NOT NULL, "
                + "to_id INTEGER NOT NULL, "
                + "status INTEGER NOT NULL)")

    # Create order_items table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS order_items ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "order_id INTEGER NOT NULL, "
                + "qty FLOAT NOT NULL, "
                + "price FLOAT NOT NULL, "
                + "product_id INTEGER NOT NULL)")

    # Create inventory_list table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS inventory_list ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "uuid TEXT NOT NULL UNIQUE, "
                + "date DATE NOT NULL, "
                + "warehouse_id INTEGER NOT NULL, "
                + "status INTEGER NOT NULL)")

    # Create warehouse_items table if not exists
    db.execute("CREATE TABLE IF NOT EXISTS inventory_items ("
                + "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                + "inventory_id INTEGER NOT NULL, "
                + "qty FLOAT, "
                + "product_id INTEGER NOT NULL)")

