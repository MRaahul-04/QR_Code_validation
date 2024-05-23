from flask import Flask, request, redirect, jsonify
from datetime import datetime
import pytz
import json

app = Flask(__name__)

# Load the QR code data from the JSON file
with open("qr_codes.json", "r") as f:
    qr_codes = json.load(f)

@app.route("/")
def home():
    return "QR Code Validation Service"

@app.route("/validate", methods=["GET"])
def validate_qr():
    # Get the URL and expiration date from the query parameters
    url = request.args.get("url")
    expires = request.args.get("expires")

    if not url or not expires:
        return jsonify({"error": "Missing URL or expiration date"}), 400

    # Check if the QR code URL exists and is valid
    if url in qr_codes and qr_codes[url]["expires"] == expires:
        # Check expiration date
        expiration_date = datetime.fromisoformat(expires)
        current_date = datetime.now(pytz.utc)

        if current_date < expiration_date:
            return redirect(url)
        else:
            return jsonify({"error": "QR Code has expired"}), 403
    else:
        return jsonify({"error": "Invalid QR Code"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)

