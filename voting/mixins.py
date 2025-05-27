"""
View mixins for role-based access control in the voting app.
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .permissions import is_election_manager, is_voter


class ElectionManagerRequiredMixin:
    """Mixin to ensure only election managers can access the view."""
    permission_denied_message = _("You don't have permission to access this page.")
    permission_denied_url = reverse_lazy('voting:election_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not is_election_manager(request.user):
            messages.error(request, self.permission_denied_message)
            return redirect(self.permission_denied_url)
        return super().dispatch(request, *args, **kwargs)


class VoterRequiredMixin:
    """Mixin to ensure only voters (non-managers) can access the view."""
    permission_denied_message = _("This action is not available to administrators and election managers.")
    permission_denied_url = reverse_lazy('voting:election_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not is_voter(request.user):
            messages.error(request, self.permission_denied_message)
            return redirect(self.permission_denied_url)
        return super().dispatch(request, *args, **kwargs)


class ElectionObjectMixin:
    """Mixin to handle election object retrieval and permission checks."""
    model = None
    context_object_name = 'election'
    
    def get_object(self, queryset=None):
        """Get the election object and verify user permissions."""
        obj = super().get_object(queryset)
        if not obj.can_user_manage(self.request.user):
            messages.error(
                self.request,
                _("You don't have permission to access this election.")
            )
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return obj


class ElectionVoteMixin:
    """Mixin to handle voting permissions and restrictions."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_vote'] = self.object.can_user_vote(self.request.user)
        return context
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if voting is allowed
        if not self.object.can_vote:
            messages.error(
                request,
                _("Voting is not currently allowed for this election.")
            )
            return redirect(self.object)
            
        # Check if user can vote
        if not self.object.can_user_vote(request.user):
            if request.user.is_authenticated and not is_voter(request.user):
                messages.error(
                    request,
                    _("Administrators and election managers cannot vote in elections.")
                )
            else:
                messages.error(
                    request,
                    _("You have already voted in this election or are not eligible to vote.")
                )
            return redirect(self.object)
            
        return super().dispatch(request, *args, **kwargs)
