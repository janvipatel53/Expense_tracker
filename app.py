# Import Flask components needed for web app routing, templates, forms and sessions
from flask import Flask, render_template, request, redirect, url_for, session, send_file

# Import sqlite3 to store data permanently in a local database file
import sqlite3

# Import csv to export expense data into a CSV file
import csv

# Import hashing functions for secure password storage and checking
from werkzeug.security import generate_password_hash, check_password_hash

# Import wraps to preserve function metadata when using decorators
from functools import wraps

# Create Flask app object
app = Flask(__name__)

# Secret key is used to secure session data (login system uses sessions)
# Change this to any random string when you upload project on GitHub
app.secret_key = "your_secret_key_change_this"

# Database file name
DB_NAME = "expenses.db"


# Function to connect to the database file
def get_db_connection():
    # Connect to SQLite database
    conn = sqlite3.connect(DB_NAME)

    # This allows us to access columns using names like row["amount"] instead of row[2]
    conn.row_factory = sqlite3.Row

    # Return database connection object
    return conn


# Function to create tables in database if they don’t exist
def create_tables():
    # Get a database connection
    conn = get_db_connection()

    # Cursor is used to execute SQL queries
    cursor = conn.cursor()

    # Create users table for login/signup system
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Create expenses table to store daily expenses (linked to user_id)
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

    # Create upcoming table to store planned/future expenses (also linked to user_id)
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

    # Save changes to database
    conn.commit()

    # Close database connection
    conn.close()


# Decorator function to protect routes (only logged-in users can access them)
def login_required(func):
    # wraps keeps original function name and details
    @wraps(func)
    def wrapper(*args, **kwargs):
        # If user_id is not stored in session, user is not logged in
        if "user_id" not in session:
            # Redirect user to login page
            return redirect(url_for("login"))

        # If logged in, allow the original function to run
        return func(*args, **kwargs)

    # Return wrapper function
    return wrapper


# Signup route for creating a new user account
@app.route("/signup", methods=["GET", "POST"])
def signup():
    # If user submits signup form
    if request.method == "POST":
        # Get user details from form inputs
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Simple validation: check if any input is empty
        if not full_name or not email or not password:
            return render_template("signup.html", error="All fields are required.")

        # Convert password into a secure hashed form
        password_hash = generate_password_hash(password)

        # Try inserting user into database
        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name, email, password_hash)
            )
            conn.commit()
            conn.close()

        # If email already exists, database throws an error
        except sqlite3.IntegrityError:
            return render_template("signup.html", error="Email already exists. Try login.")

        # If signup is successful, redirect user to login page
        return redirect(url_for("login"))

    # If request method is GET, show signup page
    return render_template("signup.html")


# Login route for user authentication
@app.route("/login", methods=["GET", "POST"])
def login():
    # If login form is submitted
    if request.method == "POST":
        # Get login form data
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        # Get user record from database by email
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        # If no user found
        if user is None:
            return render_template("login.html", error="User not found. Please signup.")

        # Check if password matches hashed password
        if not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Incorrect password.")

        # If login is successful, store user details in session
        session["user_id"] = user["id"]
        session["full_name"] = user["full_name"]

        # Redirect user to dashboard
        return redirect(url_for("index"))

    # If GET request, just show login page
    return render_template("login.html")


# Logout route - clears session data
@app.route("/logout")
def logout():
    # Remove everything saved in session
    session.clear()

    # Redirect user to login page
    return redirect(url_for("login"))


# Dashboard route (shows summary + expenses table)
@app.route("/")
@login_required
def index():
    # Get logged-in user id from session
    user_id = session["user_id"]

    # Get search text from URL query (default empty string)
    search = request.args.get("search", "").strip()

    # Get category filter from URL query (default empty string)
    category_filter = request.args.get("category", "").strip()

    # Connect to database
    conn = get_db_connection()

    # Fetch all categories for dropdown filter
    categories = conn.execute(
        "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category ASC",
        (user_id,)
    ).fetchall()

    # Start building SQL query for expenses list
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    # If user typed something in search box, apply search
    if search:
        query += " AND (category LIKE ? OR description LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")

    # If user selected category filter, apply filter
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    # Show latest expenses first
    query += " ORDER BY id DESC"

    # Fetch filtered expenses
    expenses = conn.execute(query, params).fetchall()

    # Calculate total spending (all expenses sum)
    total_spent = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    # Calculate total upcoming spending
    total_upcoming = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM upcoming WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    # Create monthly chart data using date format (DD-MM-YYYY)
    monthly_data = conn.execute("""
        SELECT substr(date, 7, 4) || '-' || substr(date, 4, 2) AS month,
               SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month ASC
    """, (user_id,)).fetchall()

    # Close DB connection
    conn.close()

    # Convert chart data into Python lists to send to HTML
    chart_labels = [row["month"] for row in monthly_data]
    chart_values = [row["total"] for row in monthly_data]

    # Render dashboard page with all required data
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


# Route to add a new expense
@app.route("/add_expense", methods=["POST"])
@login_required
def add_expense():
    # Get logged-in user id
    user_id = session["user_id"]

    # Read form values
    date = request.form["date"].strip()
    category = request.form["category"].strip()
    amount = request.form["amount"].strip()
    description = request.form["description"].strip()

    # Basic validation (if any field missing, redirect back)
    if not date or not category or not amount or not description:
        return redirect(url_for("index"))

    # Insert expense into database
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO expenses (user_id, date, category, amount, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, date, category, float(amount), description)
    )
    conn.commit()
    conn.close()

    # Redirect to dashboard after adding
    return redirect(url_for("index"))


# Route to delete an expense using its id
@app.route("/delete_expense/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    # Get logged-in user id
    user_id = session["user_id"]

    # Delete expense from DB only if it belongs to current user
    conn = get_db_connection()
    conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    conn.commit()
    conn.close()

    # Redirect back to dashboard
    return redirect(url_for("index"))


# Route to open edit form page
@app.route("/edit_expense/<int:expense_id>")
@login_required
def edit_expense(expense_id):
    # Get logged-in user id
    user_id = session["user_id"]

    # Fetch the expense record
    conn = get_db_connection()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id)
    ).fetchone()
    conn.close()

    # If expense not found, go back
    if expense is None:
        return redirect(url_for("index"))

    # Open edit page with current expense data
    return render_template("edit.html", expense=expense)


# Route to update expense data after edit
@app.route("/update_expense/<int:expense_id>", methods=["POST"])
@login_required
def update_expense(expense_id):
    # Get logged-in user id
    user_id = session["user_id"]

    # Read updated form values
    date = request.form["date"].strip()
    category = request.form["category"].strip()
    amount = request.form["amount"].strip()
    description = request.form["description"].strip()

    # Update database record
    conn = get_db_connection()
    conn.execute("""
        UPDATE expenses
        SET date = ?, category = ?, amount = ?, description = ?
        WHERE id = ? AND user_id = ?
    """, (date, category, float(amount), description, expense_id, user_id))
    conn.commit()
    conn.close()

    # Redirect to dashboard
    return redirect(url_for("index"))


# Upcoming expenses page route
@app.route("/upcoming")
@login_required
def upcoming_page():
    # Get logged-in user id
    user_id = session["user_id"]

    # Fetch all upcoming expenses of logged-in user
    conn = get_db_connection()
    upcoming = conn.execute(
        "SELECT * FROM upcoming WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()

    # Render upcoming page
    return render_template("upcoming.html", upcoming=upcoming)


# Route to add upcoming expense
@app.route("/add_upcoming", methods=["POST"])
@login_required
def add_upcoming():
    # Get logged-in user id
    user_id = session["user_id"]

    # Read upcoming expense form data
    due_date = request.form["due_date"].strip()
    title = request.form["title"].strip()
    amount = request.form["amount"].strip()
    note = request.form["note"].strip()

    # Validate inputs
    if not due_date or not title or not amount or not note:
        return redirect(url_for("upcoming_page"))

    # Insert upcoming expense in DB
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO upcoming (user_id, due_date, title, amount, note) VALUES (?, ?, ?, ?, ?)",
        (user_id, due_date, title, float(amount), note)
    )
    conn.commit()
    conn.close()

    # Redirect back
    return redirect(url_for("upcoming_page"))


# Route to delete upcoming expense
@app.route("/delete_upcoming/<int:upcoming_id>")
@login_required
def delete_upcoming(upcoming_id):
    # Get logged-in user id
    user_id = session["user_id"]

    # Delete upcoming expense only if it belongs to current user
    conn = get_db_connection()
    conn.execute("DELETE FROM upcoming WHERE id = ? AND user_id = ?", (upcoming_id, user_id))
    conn.commit()
    conn.close()

    # Redirect back
    return redirect(url_for("upcoming_page"))


# Route to export expenses in CSV format
@app.route("/export_csv")
@login_required
def export_csv():
    # Get logged in user id
    user_id = session["user_id"]

    # Fetch all expenses from database for current user
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT date, category, amount, description FROM expenses WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()

    # File name to save exported data
    export_file = "exported_expenses.csv"

    # Create CSV file and write data
    with open(export_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)  # Create CSV writer
        writer.writerow(["Date", "Category", "Amount", "Description"])  # Write headings

        # Write each expense row
        for r in rows:
            writer.writerow([r["date"], r["category"], r["amount"], r["description"]])

    # Send the file to user for download
    return send_file(export_file, as_attachment=True)


# Main entry point of the program
if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=5000)

