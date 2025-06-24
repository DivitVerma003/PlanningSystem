from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
import cx_Oracle
import json
import os
from sqlalchemy import Sequence, text
from datetime import datetime, timezone

# Oracle DB connection setup
host = "localhost"
port = 1521
service_name = "xepdb1"
dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
username = "PDBADMIN"
password = "DivitVerma231"

# Create DSN
dsn = cx_Oracle.makedsn("localhost", 1521, service_name="xepdb1")
conn = cx_Oracle.connect("sys", "DivitVerma231", dsn, mode=cx_Oracle.SYSDBA)
print("Connected:", conn.version)
conn.close()

# Flask app setup
app = Flask(__name__)
app.secret_key = 'your_super_secret_key'

app.config["SQLALCHEMY_DATABASE_URI"] = f"oracle+cx_oracle://{username}:{password}@{dsn}"

# Suppress FSADeprecationWarning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy only ONCE
db = SQLAlchemy(app)

# Direct cx_Oracle test (optional)
try:
    dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
    conn = cx_Oracle.connect(username, password, dsn)
    print("✅ Oracle DB connected:", conn.version)
    conn.close()
except Exception as e:
    print("❌ cx_Oracle failed:", e)

# Define a model (example)
class Employee(db.Model):
    __tablename__ = 'employees'
    emp_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))

class Ticket(db.Model):
    __tablename__ = 'tickets'
    ticket_id = db.Column(db.Integer, Sequence('ticket_id_seq'), primary_key=True)
    emp_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Create tables
with app.app_context():
    db.create_all()
    try:
        db.session.execute(text("""
            BEGIN
              EXECUTE IMMEDIATE 'CREATE SEQUENCE ticket_id_seq START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE';
            EXCEPTION
              WHEN OTHERS THEN
                IF SQLCODE != -955 THEN -- -955 = sequence already exists
                  RAISE;
                END IF;
            END;
        """))
        db.session.commit()
        print("✅ Sequence ticket_id_seq ready.")
    except Exception as e:
        print("❌ Failed to create sequence:", e)

# Home route
@app.route('/')
def home():
    return render_template('login.html', error=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_id = request.form['emp_id']
        entered_name = request.form['name'].strip().lower()

        with open('c:\\Users\\TUF GAMING\\Downloads\\PlanningSystem\\PlanningSystem\\datasets\\data.json') as f:
            employees = json.load(f)

        # Match employee ID and name
        matched_employee = next(
            (emp for emp in employees if str(emp['emp_id']) == entered_id and emp['name'].strip().lower() == entered_name),
            None
        )

        if matched_employee:
            session['user'] = matched_employee['emp_id']
            session['user_name'] = matched_employee['name']
            return redirect(url_for('admin'))
        else:
            flash("Invalid employee ID or name")
            return render_template('login.html', error="Invalid ID or Name")

    return render_template('login.html')

@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    data = request.get_json()
    new_ticket = Ticket(
        emp_id=session['user'],
        category=data['category'],
        description=data['description']
    )
    db.session.add(new_ticket)
    db.session.commit()
    return jsonify({"success": True, "message": "Ticket submitted!"})

@app.route('/get_tickets')
def get_tickets():
    if 'user' not in session:
        return jsonify([])

    tickets = Ticket.query.filter_by(emp_id=session['user']).order_by(Ticket.ticket_id.desc()).all()
    return jsonify([
        {
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M"),
            "id": t.ticket_id,
            "category": t.category,
            "description": t.description,
            "status": t.status
        } for t in tickets
    ])

@app.route('/admin')
def admin():
    if 'user' in session:
        return render_template('admin.html')
    else:
        return redirect(url_for('login'))
    
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session['user']
    
    # Load user data from data.json
    with open('c:\\Users\\TUF GAMING\\Downloads\\PlanningSystem\\PlanningSystem\\datasets\\data.json') as f:
        employees = json.load(f)
    
    # Find the logged-in user
    user_info = next((emp for emp in employees if str(emp['emp_id']) == str(user_id)), None)
    
    if not user_info:
        flash("User profile not found.")
        return redirect(url_for('admin'))

    # Get user's tickets from DB
    tickets = Ticket.query.filter_by(emp_id=user_id).order_by(Ticket.ticket_id.desc()).all()

    return render_template('profile.html', user_info=user_info, tickets=tickets)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 2rem; background: #f0f0f0; }
    a { display: block; margin: 1rem 0; color: #1565c0; font-size: 1.2rem; }
  </style>
</head>
<body>
  <h1>Welcome, {{ user }}</h1>
  <a href="{{ url_for('get_users') }}">View Employees (JSON)</a>
  <a href="{{ url_for('logout') }}">Logout</a>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
