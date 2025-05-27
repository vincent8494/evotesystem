"""
Custom permissions and mixins for role-based access control in the voting app.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def is_election_manager(user):
    """Check if user is a superuser, staff, or has election management permissions."""
    return (
        user.is_authenticated and 
        (user.is_superuser or 
         user.is_staff or 
         user.has_perm('voting.can_manage_elections') or
         user.groups.filter(name='Election Managers').exists())
    )


def is_voter(user):
    """Check if user is a regular voter (not an admin/manager)."""
    return user.is_authenticated and not is_election_manager(user)


class ElectionManagerRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to election managers only."""
    permission_denied_message = "You don't have permission to manage elections."
    
    def test_func(self):
        return is_election_manager(self.request.user)
    
    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()


class VoterRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to regular voters only (not admins/managers)."""
    permission_denied_message = "Admins and managers cannot perform this action."
    
    def test_func(self):
        return is_voter(self.request.user)
    
    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()
