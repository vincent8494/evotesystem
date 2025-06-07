"""
Custom CSRF middleware for debugging CSRF issues.
"""
import logging
from django.middleware.csrf import CsrfViewMiddleware, RejectRequest
from django.conf import settings

logger = logging.getLogger(__name__)

class CsrfDebugMiddleware(CsrfViewMiddleware):
    """
    CSRF middleware that logs detailed information about CSRF validation.
    """
    def _reject(self, request, reason):
        logger.warning(
            "CSRF validation failed: %s\n"
            "Referer: %s\n"
            "Origin: %s\n"
            "Host: %s\n"
            "CSRF_TRUSTED_ORIGINS: %s",
            reason,
            request.META.get('HTTP_REFERER'),
            request.META.get('HTTP_ORIGIN'),
            request.get_host(),
            getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        )
        return super()._reject(request, reason)
    
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(callback, 'csrf_exempt', False):
            return None
            
        logger.debug(
            "Processing CSRF for %s %s\n"
            "Method: %s\n"
            "Referer: %s\n"
            "Origin: %s\n"
            "CSRF Token: %s",
            request.method,
            request.path,
            request.method,
            request.META.get('HTTP_REFERER'),
            request.META.get('HTTP_ORIGIN'),
            request.META.get('CSRF_COOKIE')
        )
        
        return super().process_view(request, callback, callback_args, callback_kwargs)
