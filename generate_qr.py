import qrcode
from datetime import datetime, timedelta
import pytz
import json

# Data and expiration
base_url = "https://www.google.com"
expiration = (datetime.now(pytz.utc) + timedelta(days=1)).isoformat()

# Include the expiration date in the QR code data
data = f"{base_url}?expires={expiration}"

# Generate the QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(data)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

# Save the QR code image
img.save("qrcode_with_expiration.png")

# Save the QR code data to a JSON file (simulating a database)
qr_codes = {
    base_url: {
        "expires": expiration
    }
}

with open("qr_codes.json", "w") as f:
    json.dump(qr_codes, f)

print(f"QR Code generated with expiration date: {expiration}")

