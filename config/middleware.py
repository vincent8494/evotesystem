from django.http import HttpRequest
from functools import wraps

class ForceHttpMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Create a wrapper for the request to override the scheme and is_secure
        class WsgiRequestWithHttp(HttpRequest):
            @property
            def scheme(self):
                return 'http'
            
            def is_secure(self):
                return False
        
        # Create a new request with our custom class
        request.__class__ = type('PatchedWSGIRequest', 
                               (WsgiRequestWithHttp, request.__class__), 
                               {})
        
        # Prevent any upgrade to HTTPS
        if 'upgrade-insecure-requests' in request.META.get('HTTP_UPGRADE_INSECURE_REQUESTS', ''):
            request.META['HTTP_UPGRADE_INSECURE_REQUESTS'] = '0'
        
        # Handle the request
        response = self.get_response(request)
        
        # Ensure no HTTPS redirects in the response
        if hasattr(response, 'url') and response.url and response.url.startswith('https://'):
            response.url = response.url.replace('https://', 'http://', 1)
            
        return response
