import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)
API_URL = os.getenv("API_URL", "http://api:5002").rstrip("/")
VIEWER_URL = os.getenv("VIEWER_URL", "/records")


@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    error = None
    form = {}

    if request.method == "POST":
        form = request.form.to_dict()
        try:
            response = requests.post(f"{API_URL}/students", json=form, timeout=10)
            payload = response.json()
            if response.ok:
                message = payload.get("message", "Student saved successfully")
                form = {}
            else:
                error = payload.get("error", "Could not save student")
        except Exception as exc:
            error = f"API connection error: {exc}"

    return render_template(
        "index.html",
        message=message,
        error=error,
        form=form,
        viewer_url=VIEWER_URL,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
