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
import logging

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

        # Ensure expiration date is in local timezone
        expiration_date_local = indian_timezone.localize(expiration_date)
    except ValueError:
        return jsonify({"error": "Invalid expiration date format"}), 400

    doc_id = str(uuid.uuid4())

    # Save to Firestore
    doc_ref = db.collection('qr_codes').document(doc_id)
    doc_ref.set({
        'url': url,
        'expires': expiration_date_local,
        'created_at': firestore.SERVER_TIMESTAMP
    })

    # Generate QR code with the unique document ID
    qr_code = pyqrcode.create(url)
    qr_code_path = os.path.join(generated_codes_dir, f'qrcode_{doc_id}.png')
    qr_code.png(qr_code_path, scale=8)

    return jsonify({"qr_code_url": f"/generated_codes/qrcode_{doc_id}.png"})


# #############################
# @app.route('/validate', methods=["GET"])
# def validate_qr():
#     doc_id = request.args.get("doc_id")
#
#     if not doc_id:
#         return jsonify({"error": "Missing document ID"}), 400
#
#     # Retrieve the document from Firestore
#     doc_ref = db.collection('qr_codes').document(doc_id)
#     doc = doc_ref.get()
#
#     if doc.exists:
#         data = doc.to_dict()
#         stored_expires = data.get('expires')
#         url = data.get('url')
#
#         # Check expiration date and convert expiration date and current date to Indian Timezone
#         expiration_date = datetime.datetime.fromtimestamp(stored_expires).astimezone(indian_timezone)
#         current_date = datetime.datetime.now(indian_timezone)
#
#         if current_date < expiration_date:
#             return redirect(url)
#         else:
#             return jsonify({"error": "QR Code has expired"}), 403
#     else:
#         return jsonify({"error": "Invalid QR Code"}), 404
# #######################


# Configure logging to output to the console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


@app.route('/validate', methods=["GET"])
def validate_qr():
    doc_id = request.args.get("doc_id")

    if not doc_id:
        return jsonify({"error": "Missing document ID"}), 400

    # Create a query to retrieve only the documents that have not expired
    query = db.collection('qr_codes').where('expires', '>', SERVER_TIMESTAMP)

    # Retrieve the document from Firestore using the query
    doc_ref = query.stream()
    doc = None
    for doc in doc_ref:
        if doc.id == doc_id:
            break
    # Log the retrieved document
    logging.info(f"Retrieved document: {doc.to_dict()}")

    if doc:
        data = doc.to_dict()
        url = data.get('url')

        return redirect(url)
    else:
        return jsonify({"error": "QR Code has expired or is invalid"}), 403


@app.route('/generated_codes/<path:filename>')
def serve_generated_code(filename):
    return send_from_directory(generated_codes_dir, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
