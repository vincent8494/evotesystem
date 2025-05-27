"""
Custom management command to run the development server with SSL using django-extensions and werkzeug.
"""
import os
import ssl
from django.core.management.commands.runserver_plus import Command as RunserverPlusCommand
from django.conf import settings

class Command(RunserverPlusCommand):
    help = 'Run the development server with SSL support using django-extensions and werkzeug'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--cert', dest='cert_path',
            default=os.path.join(settings.BASE_DIR, 'ssl', 'localhost.crt'),
            help='SSL certificate file',
        )
        parser.add_argument(
            '--key', dest='key_path',
            default=os.path.join(settings.BASE_DIR, 'ssl', 'localhost.key'),
            help='SSL key file',
        )

    def handle(self, *args, **options):
        cert_path = options.get('cert_path')
        key_path = options.get('key_path')

        if not os.path.exists(cert_path):
            self.stderr.write(
                f'SSL certificate not found at {cert_path}.\n'
                'Please generate a self-signed certificate first.\n'
            )
            return

        if not os.path.exists(key_path):
            self.stderr.write(
                f'SSL key not found at {key_path}.\n'
                'Please generate a self-signed certificate first.\n'
            )
            return

        # Set up SSL context
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_path, key_path)

        # Set the SSL context for the server
        from werkzeug.serving import make_ssl_devcert
        self.ssl_context = ssl_context

        # Run the server with SSL
        self.stdout.write(
            f'Starting development server with SSL at https://{options["addrport"]}/\n'
            f'Using SSL certificate: {cert_path}\n'
            f'Using SSL key: {key_path}\n'
            'Quit the server with CONTROL-C.\n'
        )
        super().handle(*args, **options)
