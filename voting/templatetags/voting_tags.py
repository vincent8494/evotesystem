"""
Custom template tags for the voting app.
"""
from django import template
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

register = template.Library()
User = get_user_model()


@register.filter(name='can_manage_election')
def can_manage_election(user, election):
    """Check if a user can manage a specific election.
    
    Usage in template:
    {% if request.user|can_manage_election:election %}
        Show admin controls
    {% endif %}
    """
    if not user.is_authenticated:
        return False
    return election.can_user_manage(user)


@register.filter(name='can_vote_in_election')
def can_vote_in_election(user, election):
    """Check if a user can vote in a specific election.
    
    Usage in template:
    {% if request.user|can_vote_in_election:election %}
        Show vote button
    {% endif %}
    """
    if not user.is_authenticated:
        return False
    return election.can_user_vote(user)


@register.simple_tag(takes_context=True)
def if_can_manage(context, election, *args, **kwargs):
    """Conditionally render content based on election management permissions.
    
    Usage in template:
    {% if_can_manage election %}
        Show admin controls
    {% endif_can_manage %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return ''
    
    if election.can_user_manage(request.user):
        template = Template(''.join(args))
        return template.render(context.flatten())
    return ''


@register.simple_tag(takes_context=True)
def if_can_vote(context, election, *args, **kwargs):
    """Conditionally render content based on voting permissions.
    
    Usage in template:
    {% if_can_vote election %}
        Show vote button
    {% endif_can_vote %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return ''
    
    if election.can_user_vote(request.user):
        template = Template(''.join(args))
        return template.render(context.flatten())
    return ''


@register.inclusion_tag('voting/includes/role_based_ui.html')
def render_role_based_ui(user, election):
    """Render different UI elements based on user role and permissions.
    
    Usage in template:
    {% render_role_based_ui request.user election %}
    """
    can_manage = election.can_user_manage(user) if user.is_authenticated else False
    can_vote = election.can_user_vote(user) if user.is_authenticated else False
    
    return {
        'can_manage': can_manage,
        'can_vote': can_vote,
        'election': election,
        'user': user,
    }
