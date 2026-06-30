
# Smart Expense Tracker Web Application

A full-stack expense management web application built using Flask and SQLite that enables users to track daily spending, manage upcoming expenses, monitor budgets, visualize spending trends, and interact with expense data through REST APIs.

## Features
- User Login and Signup (Multi-user support)
- Add, Edit, Delete Expenses (CRUD)
- Add and Delete Upcoming Expenses
- Search expenses by category/description
- Filter expenses by category
- Export expenses to CSV
- Monthly expense chart using Chart.js
- Clean and responsive UI using HTML/CSS

## Tech Stack
- Python
- Flask
- SQLite
- HTML, CSS
- Chart.js



# Expense Tracker Web App (Flask + SQLite)

A web-based expense tracker built using Python Flask and SQLite.  
Users can record daily expenses, manage upcoming expenses, and view spending summaries through a dashboard.

## Features

- User Signup/Login with secure password hashing
- Multi-user session-based authentication
- Add, Edit, Delete Expenses (CRUD)
- Manage Upcoming Expenses
- Search and filter expenses by category or description
- Export expense records to CSV
- Monthly expense analytics dashboard using Chart.js
- Budget tracking with threshold-based alerts
- REST API support for expense retrieval, creation, and deletion
- Responsive UI using HTML, CSS, and Flask templates


## REST API Endpoints

### Get all expenses
GET /api/expenses

Returns all expense records in JSON format.

### Add expense
POST /api/expenses

Example JSON body:
{
  "date": "30-06-2026",
  "category": "Food",
  "amount": 250,
  "description": "Burger"
}

### Delete expense
DELETE /api/expenses/<expense_id>

Deletes an expense using its ID.

## Tech Stack

- Python
- Flask
- SQLite
- HTML / CSS
- Chart.js
- REST APIs
- Git / GitHub

## Project Highlights

- Implemented secure authentication using password hashing and Flask sessions
- Designed normalized relational database schema using SQLite
- Built RESTful API endpoints for expense management
- Added analytics, reporting, and budget alert features