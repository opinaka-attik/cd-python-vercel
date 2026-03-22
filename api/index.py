from flask import Flask, jsonify
import os

app = Flask(__name__)

# Variable d'environnement injectée par Vercel
ENVIRONMENT = os.getenv("APP_ENV", "local")

@app.route("/")
def home():
    return jsonify({
        "message": "Hello depuis l'API Python !",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "environment": ENVIRONMENT
    })

@app.route("/sum/<int:a>/<int:b>")
def sum_route(a, b):
    return jsonify({
        "operation": f"{a} + {b}",
        "result": a + b
    })