from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend requests

# ✅ MySQL Configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"  # Change if you have a different MySQL username
app.config["MYSQL_PASSWORD"] = ""  # Set your MySQL password here
app.config["MYSQL_DB"] = "mental_health_db"

mysql = MySQL(app)

# ✅ Register API
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")  # Ideally, hash the password

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        mysql.connection.commit()
        return jsonify({"success": True, "message": "User registered successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        cursor.close()

# ✅ Login API
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    cursor.close()

    if user:
        return jsonify({"success": True, "message": "Login successful!"})
    else:
        return jsonify({"success": False, "message": "Invalid credentials!"})

if __name__ == "__main__":
    app.run(debug=True)
