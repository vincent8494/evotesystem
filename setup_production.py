import os
import random
import string
from pathlib import Path
from django.core.management.utils import get_random_secret_key

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'

# Generate secure random values
SECRET_KEY = get_random_secret_key()

# Default configuration
config = f"""# Django Production Settings
DEBUG=False
SECRET_KEY={SECRET_KEY}
ALLOWED_HOSTS=.localhost,127.0.0.1

# Database Configuration (Update with your database details)
DATABASE_URL=sqlite:///{BASE_DIR}/db.sqlite3

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=webmaster@example.com

# Security Settings
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
"""

def setup():
    # Create .env file if it doesn't exist
    if not ENV_PATH.exists():
        with open(ENV_PATH, 'w') as f:
            f.write(config)
        print(f"✅ Created {ENV_PATH}")
        print("Please update the .env file with your production settings.")
    else:
        print(f"ℹ️ {ENV_PATH} already exists. Skipping creation.")

if __name__ == "__main__":
    setup()
