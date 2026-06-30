# Smart Expense Tracker Web Application

A full-stack expense management web application built using Flask and SQLite that enables users to track daily spending, manage upcoming expenses, monitor budgets, visualize spending trends, and interact with expense data through REST APIs.

## Live Demo
Deployed Application: https://smart-expense-tracker-ys20.onrender.com

## Features

- Secure user signup and login with password hashing
- Multi-user session-based authentication
- Add, edit, and delete expenses (CRUD operations)
- Manage upcoming expenses
- Search and filter expenses by category or description
- Export expense records to CSV
- Monthly expense analytics dashboard using Chart.js
- Budget tracking with threshold-based warning alerts
- REST API support for expense retrieval, creation, and deletion
- Responsive web interface using Flask templates, HTML, and CSS

## Tech Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- Chart.js
- REST APIs
- Git / GitHub
- Render (Deployment)

## Project Highlights

- Implemented secure authentication using password hashing and Flask sessions
- Designed relational database schema using SQLite for multi-user expense management
- Built RESTful API endpoints for expense retrieval, insertion, and deletion
- Added analytics dashboard with interactive visualizations and budget alert logic
- Deployed the application on Render for public access

## REST API Endpoints

### Get All Expenses
```http
GET /api/expenses
```

Returns all expense records in JSON format.

### Add Expense
```http
POST /api/expenses
```

Example Request Body:

```json
{
  "date": "30-06-2026",
  "category": "Food",
  "amount": 250,
  "description": "Burger"
}
```

### Delete Expense
```http
DELETE /api/expenses/<expense_id>
```

Deletes an expense using its ID.

## Installation and Setup

### Clone Repository
```bash
git clone https://github.com/janvipatel53/Expense_tracker.git
cd Expense_tracker
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```

Application runs locally at:

```text
http://127.0.0.1:5000
```

## Future Improvements

- Email-based expense reminders
- Cloud database integration (PostgreSQL)
- JWT-based API authentication
- Expense prediction using machine learning

## License
This project is licensed under the MIT License.