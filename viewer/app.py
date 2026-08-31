import os
import requests
from flask import Flask, render_template

app = Flask(__name__)
API_URL = os.getenv("API_URL", "http://api:5002").rstrip("/")
ENTRY_URL = os.getenv("ENTRY_URL", "http://localhost:5000")


def render_records():
    students = []
    source = "unknown"
    error = None
    try:
        response = requests.get(f"{API_URL}/students", timeout=10)
        payload = response.json()
        if response.ok:
            students = payload.get("students", [])
            source = payload.get("source", "unknown")
        else:
            error = payload.get("error", "Could not load students")
    except Exception as exc:
        error = f"API connection error: {exc}"

    return render_template(
        "index.html",
        students=students,
        source=source,
        error=error,
        entry_url=ENTRY_URL,
    )


@app.get("/")
def index():
    return render_records()


@app.get("/records")
@app.get("/records/")
def records():
    return render_records()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=False)
