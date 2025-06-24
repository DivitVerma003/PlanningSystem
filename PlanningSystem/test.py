from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import cx_Oracle

app = Flask(__name__)

# Replace with your Oracle details
host = "localhost"
port = 1521
service_name = "XEPDB1"

dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
username = "Admin"
password = "1234567890"

# SQLAlchemy URI
app.config["SQLALCHEMY_DATABASE_URI"] = f"oracle+cx_oracle://{username}:{password}@{dsn}"

db = SQLAlchemy(app)

try:
    connection = cx_Oracle.connect(username, password, dsn)
    print("✅ Successfully connected to Oracle DB:", connection.version)
    connection.close()
except cx_Oracle.DatabaseError as e:
    print("❌ Connection failed:", e)

