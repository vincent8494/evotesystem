"""
Simple script to run Django development server with SSL.
"""
import os
import sys
from django.core.management import execute_from_command_line
from django.conf import settings

def run():
    cert_path = os.path.join(settings.BASE_DIR, 'ssl', 'localhost.crt')
    key_path = os.path.join(settings.BASE_DIR, 'ssl', 'localhost.key')
    
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        print("Error: SSL certificate or key not found.")
        print(f"Certificate path: {cert_path}")
        print(f"Key path: {key_path}")
        sys.exit(1)
    
    # Set the environment variable for the SSL certificate
    os.environ['SSL_CERT_FILE'] = cert_path
    
    # Run the development server with SSL
    execute_from_command_line([
        'manage.py', 'runserver_plus',
        '--cert-file', cert_path,
        '--key-file', key_path,
        '127.0.0.1:8443'
    ])

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    run()
