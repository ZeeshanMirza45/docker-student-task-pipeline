import json
import os
import time
from flask import Flask, jsonify, request
import mysql.connector
import redis

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST") or os.getenv("MYSQLHOST", "mysql"),
    "port": int(os.getenv("DB_PORT") or os.getenv("MYSQLPORT", "3306")),
    "database": os.getenv("DB_NAME") or os.getenv("MYSQLDATABASE", "studentdb"),
    "user": os.getenv("DB_USER") or os.getenv("MYSQLUSER", "studentuser"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("MYSQLPASSWORD", "studentpass"),
}

redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_PRIVATE_URL")
if redis_url:
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
else:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
    )

CACHE_KEY = "students:all"
CACHE_SECONDS = 60


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    for attempt in range(30):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    roll_no VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    semester INT NOT NULL,
                    cgpa DECIMAL(3,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized.")
            return
        except Exception as exc:
            print(f"DB init attempt {attempt + 1} failed: {exc}")
            time.sleep(2)
    raise RuntimeError("Could not initialize database")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/students")
def create_student():
    data = request.get_json(silent=True) or {}
    required = ["roll_no", "name", "email", "department", "semester", "cgpa"]
    missing = [field for field in required if str(data.get(field, "")).strip() == ""]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        semester = int(data["semester"])
        cgpa = float(data["cgpa"])
        if semester < 1 or semester > 12:
            return jsonify({"error": "Semester must be between 1 and 12"}), 400
        if cgpa < 0 or cgpa > 4.0:
            return jsonify({"error": "CGPA must be between 0.00 and 4.00"}), 400
    except ValueError:
        return jsonify({"error": "Semester and CGPA must be valid numbers"}), 400

    conn = None
    cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO students (roll_no, name, email, department, semester, cgpa)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                data["roll_no"].strip(),
                data["name"].strip(),
                data["email"].strip(),
                data["department"].strip(),
                semester,
                cgpa,
            ),
        )
        conn.commit()
        try:
            redis_client.delete(CACHE_KEY)
        except Exception as exc:
            print(f"Redis cache clear warning: {exc}")
        return jsonify({"message": "Student saved successfully", "id": cur.lastrowid}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Roll number already exists"}), 409
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.get("/students")
def list_students():
    try:
        cached = redis_client.get(CACHE_KEY)
    except Exception as exc:
        print(f"Redis cache read warning: {exc}")
        cached = None

    if cached:
        response = json.loads(cached)
        return jsonify({"source": "redis-cache", "students": response})

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT id, roll_no, name, email, department, semester,
               CAST(cgpa AS DOUBLE) AS cgpa, created_at
        FROM students
        ORDER BY id DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for row in rows:
        if row.get("created_at"):
            row["created_at"] = row["created_at"].isoformat(sep=" ", timespec="seconds")

    try:
        redis_client.setex(CACHE_KEY, CACHE_SECONDS, json.dumps(rows))
    except Exception as exc:
        print(f"Redis cache write warning: {exc}")

    return jsonify({"source": "mysql", "students": rows})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5002"))

    # Initialize database only if running locally
    if os.environ.get("VERCEL") != "1":
        init_db()

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
