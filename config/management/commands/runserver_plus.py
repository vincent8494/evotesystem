from django.core.management.commands.runserver import Command as RunserverCommand
from django.conf import settings
import ssl
import os

class Command(RunserverCommand):
    help = 'Run the development server with SSL support'

    def handle(self, *args, **options):
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

        # Run the server with SSL
        self.stdout.write(
            f'Starting development server with SSL at https://{options["addrport"]}/\n'
            f'Using SSL certificate: {cert_file}\n'
            f'Using SSL key: {key_file}\n'
            'Quit the server with CONTROL-C.\n'
        )
        
        # Override the server class to use SSL
        from django.core.servers.basehttp import WSGIServer
        import http.server
        import socketserver

        class SecureHTTPServer(socketserver.ThreadingMixIn, WSGIServer):
            def server_bind(self):
                super().server_bind()
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(certfile=cert_file, keyfile=key_file)
                self.socket = context.wrap_socket(
                    self.socket,
                    server_side=True,
                )

        http.server.HTTPServer.allow_reuse_address = True
        self.server_cls = SecureHTTPServer

        # Run the server with the modified settings
        super().handle(*args, **options)
