import os
import sys
from wsgiref.simple_server import make_server
from django.core.wsgi import get_wsgi_application

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Get the WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    # Run the development server
    port = 9000
    with make_server('0.0.0.0', port, application) as httpd:
        print(f"Starting development server at http://127.0.0.1:{port}/")
        print("Quit the server with CONTROL-C.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)
