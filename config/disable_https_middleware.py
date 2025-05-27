class DisableHttpsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Override the scheme to always be http
        request.scheme = 'http'
        request.is_secure = lambda: False
        
        # Remove any HTTPS headers that might trigger redirects
        if 'HTTP_X_FORWARDED_PROTO' in request.META:
            del request.META['HTTP_X_FORWARDED_PROTO']
            
        response = self.get_response(request)
        
        # Ensure no HTTPS redirects in the response
        if hasattr(response, 'url') and response.url and response.url.startswith('https://'):
            response.url = response.url.replace('https://', 'http://', 1)
            
        return response
