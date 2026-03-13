"""Minimal Flask application — fixture for bootstrap self-tests."""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return jsonify({"service": "minimal-python-service", "version": "0.1.0"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
