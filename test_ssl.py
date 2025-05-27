import ssl
import os
from pathlib import Path

# Get paths from settings
BASE_DIR = Path(__file__).resolve().parent.parent
SSL_CERTIFICATE = os.path.join(BASE_DIR, 'config', 'ssl', 'localhost.crt')
SSL_PRIVATE_KEY = os.path.join(BASE_DIR, 'config', 'ssl', 'localhost.key')

print(f"Testing SSL certificate at {SSL_CERTIFICATE}")
print(f"Testing SSL key at {SSL_PRIVATE_KEY}")

# Test SSL context creation
try:
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=SSL_CERTIFICATE, keyfile=SSL_PRIVATE_KEY)
    print("SSL context created successfully")
except Exception as e:
    print(f"Error creating SSL context: {e}")
