import ssl
import socket
import os
from pathlib import Path
import http.server
import socketserver
import time
import threading

# Use absolute paths for SSL files
SSL_CERTIFICATE = '/home/fetty/electionsproject/config/ssl/localhost.crt'
SSL_PRIVATE_KEY = '/home/fetty/electionsproject/config/ssl/localhost.key'

print(f"Testing SSL certificate at {SSL_CERTIFICATE}")
print(f"Testing SSL key at {SSL_PRIVATE_KEY}")

# Create SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=SSL_CERTIFICATE, keyfile=SSL_PRIVATE_KEY)

# Simple HTTP request handler
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Hello, SSL!")

def run_ssl_server():
    # Create server
    server_address = ('0.0.0.0', 8003)
    httpd = http.server.HTTPServer(server_address, SimpleHandler)
    
    # Wrap socket with SSL
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"Starting SSL server on port {8003}")
    httpd.serve_forever()

# Run server in a separate thread
server_thread = threading.Thread(target=run_ssl_server)
server_thread.daemon = True
server_thread.start()

# Wait a moment for the server to start
print("Waiting for server to start...")
time.sleep(2)

# Try to connect to the server
try:
    with socket.create_connection(('localhost', 8003)) as sock:
        with context.wrap_socket(sock, server_hostname='localhost') as ssock:
            print("Successfully connected to SSL server!")
            print("Server certificate:", ssock.getpeercert())
except Exception as e:
    print(f"Failed to connect to SSL server: {e}")

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
