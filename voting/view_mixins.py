"""
View mixins for role-based access control in the voting app.
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from .models import Election
from .permissions import is_election_manager, is_voter


class ElectionContextMixin:
    """Mixin to add common context data for election views."""
    model = Election
    context_object_name = 'election'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_manager'] = self.object.can_user_manage(self.request.user)
        context['can_vote'] = self.object.can_user_vote(self.request.user)
        return context


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin, View):
    """Mixin to ensure only election managers can access the view."""
    permission_denied_message = _("You don't have permission to access this page.")
    permission_denied_url = reverse_lazy('voting:election_list')
    
    def test_func(self):
        return is_election_manager(self.request.user)
    
    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            messages.error(self.request, self.permission_denied_message)
            return redirect(self.permission_denied_url)
        return super().handle_no_permission()


class VoterRequiredMixin(LoginRequiredMixin, UserPassesTestMixin, View):
    """Mixin to ensure only voters (non-managers) can access the view."""
    permission_denied_message = _("This action is not available to administrators and election managers.")
    permission_denied_url = reverse_lazy('voting:election_list')
    
    def test_func(self):
        return is_voter(self.request.user)
    
    def handle_no_permission(self):
        if self.raise_exception or self.request.user.is_authenticated:
            messages.error(self.request, self.permission_denied_message)
            return redirect(self.permission_denied_url)
        return super().handle_no_permission()


class ElectionManagerRequiredMixin(ManagerRequiredMixin):
    """Mixin to ensure the user is a manager of the specific election."""
    def test_func(self):
        if not super().test_func():
            return False
            
        # Get the election object
        election = self.get_object()
        return election.can_user_manage(self.request.user)


class ElectionVoterRequiredMixin(VoterRequiredMixin):
    """Mixin to ensure the user is a voter for the specific election."""
    def test_func(self):
        if not super().test_func():
            return False
            
        # Get the election object
        election = self.get_object()
        return election.can_user_vote(self.request.user)


class ActiveElectionMixin:
    """Mixin to check if the election is active and handle inactive states."""
    inactive_template_name = 'voting/election_inactive.html'
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # If election is not active, show inactive template
        if not self.object.is_active:
            context = self.get_context_data(object=self.object)
            return self.render_to_response(
                context,
                template_name=self.inactive_template_name,
                status=403
            )
            
        return super().get(request, *args, **kwargs)


class PublicElectionMixin:
    """Mixin to handle public/private election access."""
    login_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # If election is not public and user is not authenticated, redirect to login
        if not self.object.is_public and not request.user.is_authenticated:
            messages.info(
                request,
                _("Please log in to access this election.")
            )
            return redirect(f"{self.login_url}?next={request.path}")
            
        return super().dispatch(request, *args, **kwargs)
