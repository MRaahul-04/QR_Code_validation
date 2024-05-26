from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import pyqrcode
import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from dotenv import load_dotenv

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
        expiration_date = datetime.datetime.fromisoformat(expires)
    except ValueError:
        return jsonify({"error": "Invalid expiration date format"}), 400

    doc_id = str(uuid.uuid4())

    # Save to Firestore
    doc_ref = db.collection('qr_codes').document(doc_id)
    doc_ref.set({
        'url': url,
        'expires': expiration_date.isoformat()
    })

    # Generate QR code with the unique document ID
    qr_code = pyqrcode.create(f"{domain_url}/validate?doc_id={doc_id}")
    qr_code_path = os.path.join(generated_codes_dir, f'qrcode_{doc_id}.png')
    qr_code.png(qr_code_path, scale=8)

    return jsonify({"qr_code_url": f"/generated_codes/qrcode_{doc_id}.png"})


@app.route('/generated_codes/<path:filename>')
def serve_generated_code(filename):
    return send_from_directory(generated_codes_dir, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
