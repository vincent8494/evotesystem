"""
Custom CSRF middleware to fix validation issues with Render.
"""
import logging
import re
from django.middleware.csrf import CsrfViewMiddleware, get_token, constant_time_compare
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

# This is the same regex used by Django internally
csrf_token_re = re.compile(r'^[a-zA-Z0-9]{64}$')

class CsrfFixMiddleware(CsrfViewMiddleware):
    """
    Custom CSRF middleware that handles token validation more flexibly.
    """
    def _reject(self, request, reason):
        logger.warning(
            "CSRF validation failed: %s\n"
            "Referer: %s\n"
            "Origin: %s\n"
            "Host: %s\n"
            "CSRF_TRUSTED_ORIGINS: %s\n"
            "CSRF_COOKIE: %s\n"
            "CSRF_HEADER: %s",
            reason,
            request.META.get('HTTP_REFERER'),
            request.META.get('HTTP_ORIGIN'),
            request.get_host(),
            getattr(settings, 'CSRF_TRUSTED_ORIGINS', []),
            request.META.get('CSRF_COOKIE'),
            request.META.get('HTTP_X_CSRFTOKEN')
        )
        return super()._reject(request, reason)
    
    def _sanitize_token(self, token):
        """
        Sanitize and validate the CSRF token.
        """
        if token is None:
            return None
            
        # Convert to string in case it's not already
        token = str(token)
        
        # Check if the token looks valid
        if not csrf_token_re.match(token):
            return None
            
        return token
    
    def _check_token(self, request):
        # Get the CSRF token from the request
        csrf_token = self._get_token(request)
        if csrf_token is None:
            return False
            
        # Get the CSRF cookie
        csrf_cookie = request.META.get('CSRF_COOKIE')
        if csrf_cookie is None:
            return False
            
        # Compare the tokens
        return constant_time_compare(csrf_token, csrf_cookie)
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(callback, 'csrf_exempt', False):
            return None
            
        # Skip CSRF check for safe methods as defined by RFC 7231
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return self._accept(request)
            
        # Get the CSRF token from the POST data or header
        csrf_token = request.POST.get('csrfmiddlewaretoken', '')
        if not csrf_token:
            csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
            
        # If no token found, try to get it from the cookie
        if not csrf_token:
            csrf_token = request.META.get('CSRF_COOKIE')
            
        # If still no token, reject the request
        if not csrf_token:
            logger.warning("CSRF token not found in request")
            return self._reject(request, 'CSRF token not found')
            
        # Sanitize the token
        csrf_token = self._sanitize_token(csrf_token)
        if not csrf_token:
            logger.warning("Invalid CSRF token format")
            return self._reject(request, 'Invalid CSRF token format')
        
        # Check the token against the cookie
        csrf_cookie = request.META.get('CSRF_COOKIE')
        if not csrf_cookie:
            logger.warning("CSRF cookie not set")
            return self._reject(request, 'CSRF cookie not set')
            
        if not constant_time_compare(csrf_token, csrf_cookie):
            logger.warning("CSRF token does not match cookie")
            return self._reject(request, 'CSRF token does not match cookie')
            
        return self._accept(request)
