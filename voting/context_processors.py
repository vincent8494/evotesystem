"""
Template context processors for the voting app.
"""
from .permissions import is_election_manager, is_voter


def user_roles(request):
    """
    Add user role information to the template context.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}
    
    return {
        'is_election_manager': is_election_manager(request.user),
        'is_voter': is_voter(request.user),
    }
