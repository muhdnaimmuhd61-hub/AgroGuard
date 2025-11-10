from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, requests, hashlib, time

app = Flask(__name__)
CORS(app)

DB_NAME = "farming.db"

# =============== DATABASE SETUP ==================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            crop_type TEXT,
            lat REAL,
            lon REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS flood_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            description TEXT,
            severity TEXT,
            lat REAL,
            lon REAL,
            event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =============== HELPERS ==================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# =============== AUTH ROUTES ==================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"error": "Missing fields"}), 400
    try:
        query_db("INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
                 (name, email, hash_password(password)))
        return jsonify({"message": "User registered successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already registered"}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")
    user = query_db("SELECT * FROM users WHERE email=? AND password_hash=?",
                    (email, hash_password(password)), one=True)
    if user:
        return jsonify({"message": "Login successful", "user_id": user["id"], "name": user["name"]})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# =============== FARM ROUTES ==================
@app.route("/add_farm", methods=["POST"])
def add_farm():
    data = request.get_json()
    user_id = data.get("user_id")
    name = data.get("name")
    crop_type = data.get("crop_type")
    lat = data.get("lat")
    lon = data.get("lon")

    if not all([user_id, name, lat, lon]):
        return jsonify({"error": "Missing fields"}), 400

    query_db("INSERT INTO farms (user_id,name,crop_type,lat,lon) VALUES (?,?,?,?,?)",
             (user_id, name, crop_type, lat, lon))
    return jsonify({"message": "Farm added successfully!"})

@app.route("/get_farms/<int:user_id>")
def get_farms(user_id):
    farms = query_db("SELECT * FROM farms WHERE user_id=?", (user_id,))
    return jsonify([dict(f) for f in farms])

# =============== WEATHER & FLOOD ROUTES ==================
OPENWEATHER_KEY = "YOUR_OPENWEATHER_API_KEY"  # register free at openweathermap.org
OPEN_METEO_URL = "https://api.open-meteo.com/v1/flood"

@app.route("/weather")
def get_weather():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric"
    res = requests.get(url)
    return jsonify(res.json())

@app.route("/flood_indicator")
def flood_indicator():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400

    try:
        response = requests.get(f"{OPEN_METEO_URL}?latitude={lat}&longitude={lon}")
        data = response.json()
        discharge = data.get("discharge")
        risk = "low"
        if discharge:
            avg_discharge = sum(discharge) / len(discharge)
            if avg_discharge > 5000:
                risk = "high"
            elif avg_discharge > 2000:
                risk = "moderate"
        return jsonify({"risk": risk, "avg_discharge": discharge})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_floods")
def get_floods():
    floods = query_db("SELECT * FROM flood_events ORDER BY event_time DESC LIMIT 10")
    return jsonify([dict(f) for f in floods])

# =============== HOME ==================
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Smart Farming Flood & Weather Guide API",
        "routes": ["/register", "/login", "/add_farm", "/get_farms/<user_id>", "/weather?lat=&lon=", "/flood_indicator?lat=&lon="]
    })

# =============== RUN APP ==================
if __name__ == "__main__":
    print("🚜 Running server on http://127.0.0.1:5000")
    app.run(debug=True)
