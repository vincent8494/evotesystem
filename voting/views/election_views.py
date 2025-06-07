"""
Views for managing elections with role-based access control.
"""
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin

from ..models import Election
from ..forms import ElectionForm
from ..view_mixins import (
    ElectionContextMixin,
    ManagerRequiredMixin,
    ElectionManagerRequiredMixin,
    ActiveElectionMixin,
    PublicElectionMixin
)


class ElectionListView(ListView):
    """View for listing all elections."""
    model = Election
    template_name = 'voting/election_list.html'
    context_object_name = 'elections'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status and status in dict(Election.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        
        # For non-staff users, only show public elections or those they manage
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                is_public=True
            ) | queryset.filter(
                managers=self.request.user
            )
        
        return queryset.distinct().order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = dict(Election.STATUS_CHOICES)
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class ElectionDetailView(PublicElectionMixin, DetailView):
    """View for displaying a single election."""
    model = Election
    template_name = 'voting/election_detail.html'
    context_object_name = 'election'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_manager'] = self.object.can_user_manage(self.request.user)
        context['can_vote'] = self.object.can_user_vote(self.request.user)
        return context


class ElectionCreateView(ManagerRequiredMixin, CreateView):
    """View for creating a new election (managers only)."""
    model = Election
    form_class = ElectionForm
    template_name = 'voting/election_form.html'
    success_url = reverse_lazy('voting:election_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            _('Election "%s" was created successfully.') % form.instance.name
        )
        return super().form_valid(form)


class ElectionUpdateView(ElectionManagerRequiredMixin, UpdateView):
    """View for updating an election (managers only)."""
    model = Election
    form_class = ElectionForm
    template_name = 'voting/election_form.html'
    
    def get_success_url(self):
        return reverse_lazy('voting:election_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(
            self.request,
            _('Election "%s" was updated successfully.') % form.instance.name
        )
        return super().form_valid(form)


class ElectionDeleteView(ElectionManagerRequiredMixin, DeleteView):
    """View for deleting an election (managers only)."""
    model = Election
    template_name = 'voting/election_confirm_delete.html'
    success_url = reverse_lazy('voting:election_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(
            request,
            _('Election was deleted successfully.')
        )
        return response


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@require_http_methods(["POST"])
@csrf_exempt
def toggle_election_status(request, pk, status):
    """
    View for toggling election status (publish, activate, complete, cancel).
    Only accessible by election managers.
    """
    # Skip CSRF check for HTMX requests
    if request.headers.get('HX-Request') == 'true':
        setattr(request, '_dont_enforce_csrf_checks', True)
    try:
        election = Election.objects.get(pk=pk)
        
        # Check if user can manage this election
        if not election.can_user_manage(request.user):
            return JsonResponse(
                {'success': False, 'error': 'Permission denied'},
                status=403
            )
        
        # Update status based on the action
        if status in dict(Election.STATUS_CHOICES):
            election.status = status
            election.save()
            
            messages.success(
                request,
                _('Election "%s" has been %s.') % 
                (election.name, election.get_status_display().lower())
            )
            
            return JsonResponse({
                'success': True,
                'status': election.status,
                'status_display': election.get_status_display(),
                'message': f'Election has been {election.get_status_display().lower()}.'
            })
        
        return JsonResponse(
            {'success': False, 'error': 'Invalid status'},
            status=400
        )
        
    except Election.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Election not found'},
            status=404
        )
