from flask import Flask, request, jsonify, render_template, redirect, send_from_directory
import os
import pyqrcode
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from dotenv import load_dotenv
import pytz
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Get environment variables
service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
domain_url = os.getenv("DOMAIN_URL")

# Initialize Firebase
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)

db = firestore.client()

# Create a directory for generated QR codes if it doesn't exist
generated_codes_dir = 'generated_codes'
os.makedirs(generated_codes_dir, exist_ok=True)

# Set Indian Timezone
indian_timezone = pytz.timezone('Asia/Kolkata')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_qr():
    data = request.json
    url = data.get('url')
    expires = data.get('expires')

    if not url or not expires:
        return jsonify({"error": "Missing URL or expiration date"}), 400

    try:
        # Convert expiration date string to datetime object
        expiration_date = datetime.datetime.strptime(expires, '%Y-%m-%dT%H:%M')

        # Get current date in local timezone and convert to desired timezone
        current_date_synced = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))

        # Convert expiration date to the desired timezone
        expiration_date_synced = expiration_date.astimezone(pytz.timezone('Asia/Kolkata'))

        print("Current Date (Synced):", current_date_synced)
        print("Expiration Date (Synced):", expiration_date_synced)

        # Check if expiration date is in the past
        if expiration_date_synced < current_date_synced:
            return jsonify({"error": "Expiration date cannot be in the past"}), 400

    except ValueError:
        return jsonify({"error": "Invalid expiration date format"}), 400

    doc_id = str(uuid.uuid4())

    # Save to Firestore
    doc_ref = db.collection('qr_codes').document(doc_id)
    doc_ref.set({
        'url': url,
        'expires': expiration_date_synced,
        'created_at': SERVER_TIMESTAMP
    })

    # Generate QR code with the unique document ID
    qr_code = pyqrcode.create(url)
    qr_code_path = os.path.join(generated_codes_dir, f'qrcode_{doc_id}.png')
    qr_code.png(qr_code_path, scale=8)

    return jsonify({"qr_code_url": f"/generated_codes/qrcode_{doc_id}.png"})


@app.route('/validate', methods=["GET"])
def validate_qr():
    doc_id = request.args.get("doc_id")

    if not doc_id:
        return jsonify({"error": "Missing document ID"}), 400

    # Retrieve the document from Firestore
    doc_ref = db.collection('qr_codes').document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        data = doc.to_dict()
        stored_expires = data.get('expires')
        url = data.get('url')

        # Convert stored expiration date to datetime object
        expiration_date = datetime.datetime.fromisoformat(stored_expires)

        # Get current date in local timezone
        current_date = datetime.datetime.now()

        if current_date < expiration_date:
            return redirect(url)
        else:
            return jsonify({"error": "QR Code has expired"}), 403
    else:
        return jsonify({"error": "Invalid QR Code"}), 404


@app.route('/generated_codes/<path:filename>')
def serve_generated_code(filename):
    return send_from_directory(generated_codes_dir, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
