"""
Custom CSRF middleware to fix validation issues with Render.
"""
import logging
import re
from django.middleware.csrf import CsrfViewMiddleware, get_token, constant_time_compare
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.middleware.csrf import _get_new_csrf_token

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
        token = str(token).strip()
        
        # Check if the token looks valid
        if not csrf_token_re.match(token):
            return None
            
        return token
    
    def _get_token(self, request):
        """
        Get the CSRF token from the request.
        """
        # Try to get the token from POST data first
        csrf_token = request.POST.get('csrfmiddlewaretoken', '')
        if not csrf_token:
            # Then try to get it from the header
            csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')
        
        # If still no token, try to get it from the cookie
        if not csrf_token:
            csrf_token = request.COOKIES.get(settings.CSRF_COOKIE_NAME, '')
        
        return self._sanitize_token(csrf_token)
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        # Skip CSRF check for views marked as exempt
        if getattr(callback, 'csrf_exempt', False):
            return None

        # Skip CSRF check for safe methods as defined by RFC 7231
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return self._accept(request)
        
        # Get the CSRF token from the request
        csrf_token = self._get_token(request)
        
        # If no token found, reject the request
        if not csrf_token:
            logger.warning("CSRF token not found in request")
            return self._reject(request, 'CSRF token not found')
        
        # Get the CSRF cookie
        csrf_cookie = request.META.get('CSRF_COOKIE')
        if not csrf_cookie:
            logger.warning("CSRF cookie not set")
            return self._reject(request, 'CSRF cookie not set')
        
        # Sanitize the cookie token
        csrf_cookie = self._sanitize_token(csrf_cookie)
        if not csrf_cookie:
            logger.warning("Invalid CSRF cookie format")
            return self._reject(request, 'Invalid CSRF cookie format')
        
        # Compare the tokens
        if not constant_time_compare(csrf_token, csrf_cookie):
            logger.warning(
                "CSRF token does not match cookie. "
                "Token: %s, Cookie: %s",
                csrf_token,
                csrf_cookie
            )
            return self._reject(request, 'CSRF token does not match cookie')
        
        return self._accept(request)
    
    def process_response(self, request, response):
        # Call the parent's process_response to handle CSRF cookie setting
        response = super().process_response(request, response)
        
        # Ensure the CSRF cookie is set for all responses that need it
        if not request.META.get('CSRF_COOKIE_USED', False):
            # Only set the cookie if it's not already set
            if settings.CSRF_USE_SESSIONS:
                if request.session.get(settings.CSRF_SESSION_KEY):
                    return response
            elif not request.COOKIES.get(settings.CSRF_COOKIE_NAME):
                # Set a new CSRF token
                token = _get_new_csrf_token()
                response.set_cookie(
                    settings.CSRF_COOKIE_NAME,
                    token,
                    max_age=settings.CSRF_COOKIE_AGE,
                    domain=settings.CSRF_COOKIE_DOMAIN,
                    path=settings.CSRF_COOKIE_PATH,
                    secure=settings.CSRF_COOKIE_SECURE,
                    httponly=settings.CSRF_COOKIE_HTTPONLY,
                    samesite=settings.CSRF_COOKIE_SAMESITE,
                )
        
        return response
