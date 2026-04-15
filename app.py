# flask imports
from flask import Flask, render_template, request, redirect, url_for, session, send_file

# database and file handling
import sqlite3
import csv

# password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# for decorator
from functools import wraps


app = Flask(__name__)

# session key
app.secret_key = "a8sd7f8a7sdf8a7sd8f7a8sdf7a8sdf7"

# database file
DB_NAME = "expenses.db"


# db connect
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row   # access by column name
    return conn


# create tables
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # expenses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # upcoming
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS upcoming (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# login check
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


# signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not full_name or not email or not password:
            return render_template("signup.html", error="All fields required")

        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name, email, password_hash)
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Email exists")

        return redirect(url_for("login"))

    return render_template("signup.html")


# login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user is None:
            return render_template("login.html", error="User not found")

        if not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Wrong password")

        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]

        return redirect(url_for("index"))

    return render_template("login.html")


# logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# dashboard
@app.route("/")
@login_required
def index():
    user_id = session["user_id"]

    search = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    conn = get_db_connection()

    # categories list
    categories = conn.execute(
        "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category ASC",
        (user_id,)
    ).fetchall()

    # base query
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if search:
        query += " AND (category LIKE ? OR description LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY id DESC"

    expenses = conn.execute(query, params).fetchall()

    # totals
    total_spent = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    total_upcoming = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM upcoming WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    # monthly chart
    monthly_data = conn.execute("""
        SELECT substr(date, 7, 4) || '-' || substr(date, 4, 2) AS month,
               SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month ASC
    """, (user_id,)).fetchall()

    conn.close()

    chart_labels = [row["month"] for row in monthly_data]
    chart_values = [row["total"] for row in monthly_data]

    return render_template(
        "index.html",
        expenses=expenses,
        total_spent=total_spent,
        total_upcoming=total_upcoming,
        total_all=(total_spent + total_upcoming),
        categories=categories,
        selected_category=category_filter,
        search=search,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


# add expense
@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    user_id = session["user_id"]

    date = request.form["date"].strip()
    category = request.form["category"].strip()
    amount = request.form["amount"].strip()
    description = request.form["description"].strip()

    if not date or not category or not amount or not description:
        return redirect(url_for("index"))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO expenses (user_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, date, category, float(amount), description)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("index"))
