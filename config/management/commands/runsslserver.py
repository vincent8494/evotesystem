"""
Custom management command to run the Django development server with SSL.
"""
import os
import ssl
from django.core.management.commands.runserver import Command as RunserverCommand
from django.conf import settings

class Command(RunserverCommand):
    help = 'Run the development server with SSL support'

    def handle(self, *args, **options):
        if not (hasattr(settings, 'SSL_ENABLED') and settings.SSL_ENABLED):
            self.stderr.write(
                'SSL is not properly configured. Falling back to non-SSL server.\n'
                'Make sure you have run the SSL certificate generation command.\n'
            )
            super().handle(*args, **options)
            return

        # Set default address and port for SSL
        addrport = options.get('addrport')
        self._raw_ipv6 = False
        if not addrport:
            addr = '0.0.0.0'
            port = str(getattr(settings, 'SSL_PORT', 8003))  # Use SSL_PORT from settings if available
            addrport = f"{addr}:{port}"
        elif ':' in addrport and not addrport.startswith('['):
            # Handle IPv6 addresses
            addr = addrport.split(':')
            port = addr[-1]
            addr = ':'.join(addr[:-1])
            addrport = f"[{addr}]:{port}"
            self._raw_ipv6 = True

        # Set up SSL context
        cert_file = getattr(settings, 'SSL_CERTIFICATE', None)
        key_file = getattr(settings, 'SSL_PRIVATE_KEY', None)

        if not (cert_file and key_file):
            self.stderr.write(
                'SSL certificate or key file not found. Falling back to non-SSL server.\n'
                'Run the SSL certificate generation command first.\n'
            )
            super().handle(*args, **options)
            return

        # Patch the server to use SSL
        from django.core.servers.basehttp import WSGIServer
        import http.server
        import socketserver

        class SecureHTTPServer(socketserver.ThreadingMixIn, WSGIServer):
            def server_bind(self):
                # Bind the socket
                super().server_bind()
                # Wrap the socket with SSL
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(certfile=cert_file, keyfile=key_file)
                self.socket = context.wrap_socket(
                    self.socket,
                    server_side=True,
                )

        # Replace the server class
        http.server.HTTPServer.allow_reuse_address = True
        self.server_cls = SecureHTTPServer

        # Run the server with the modified settings
        self.stdout.write(
            f'Starting development server with SSL at https://{addrport}/\n'
            f'Using SSL certificate: {cert_file}\n'
            f'Using SSL key: {key_file}\n'
            'Quit the server with CONTROL-C.\n'
        )
        super().handle(*args, **options)
