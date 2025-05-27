from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Election
from .forms import ElectionForm

class ElectionListView(ListView):
    """View for listing all elections."""
    model = Election
    template_name = 'voting/election_list.html'
    context_object_name = 'elections'
    paginate_by = 10
    
    def get_queryset(self):
        """Return filtered elections based on status parameter, ordered by start date (newest first)."""
        queryset = Election.objects.all().order_by('-start_date')
        status = self.request.GET.get('status')
        now = timezone.now()
        
        if status == 'active':
            queryset = queryset.filter(status='active', start_date__lte=now, end_date__gte=now)
        elif status == 'upcoming':
            queryset = queryset.filter(start_date__gt=now)
        elif status == 'completed':
            queryset = queryset.filter(status='completed') | queryset.filter(end_date__lt=now)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Elections')
        context['now'] = timezone.now()
        context['status_choices'] = {
            'active': _('Active'),
            'upcoming': _('Upcoming'),
            'completed': _('Completed'),
        }
        return context

class ElectionDetailView(DetailView):
    """View for displaying election details with positions and candidates."""
    model = Election
    template_name = 'voting/election_detail.html'
    context_object_name = 'election'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        election = self.object
        
        # Get all positions for this election with their approved candidates
        positions_with_candidates = []
        has_approved_candidates = False
        
        for position in election.positions.all().prefetch_related('candidates__user'):
            candidates = position.candidates.filter(is_approved=True)
            if candidates.exists():
                has_approved_candidates = True
            positions_with_candidates.append({
                'position': position,
                'candidates': candidates
            })
        
        # Check if user has voted
        has_voted = False
        if self.request.user.is_authenticated:
            has_voted = election.votes.filter(voter=self.request.user).exists()
        
        context.update({
            'title': _('Election Details'),
            'now': timezone.now(),
            'positions_with_candidates': positions_with_candidates,
            'has_approved_candidates': has_approved_candidates,
            'has_voted': has_voted,
            'is_election_manager': election.can_user_manage(self.request.user) if self.request.user.is_authenticated else False,
        })
        return context


class ElectionResultsView(DetailView):
    """View for displaying election results."""
    model = Election
    template_name = 'voting/election_results.html'
    context_object_name = 'election'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        election = self.object
        
        # Get vote counts per candidate
        from django.db.models import Count
        results = []
        
        for position in election.positions.all():
            candidates = position.candidates.annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count')
            
            if candidates.exists():
                results.append({
                    'position': position,
                    'candidates': candidates,
                    'total_votes': sum(c.vote_count for c in candidates)
                })
        
        context.update({
            'title': _('Election Results'),
            'now': timezone.now(),
            'results': results,
            'has_results': any(r['candidates'] for r in results)
        })
        return context

class ElectionCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new election."""
    model = Election
    form_class = ElectionForm
    template_name = 'voting/election_form.html'
    success_url = reverse_lazy('voting:election_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _('Election created successfully!'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create Election')
        return context

class ElectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating an existing election."""
    model = Election
    form_class = ElectionForm
    template_name = 'voting/election_form.html'
    context_object_name = 'election'
    
    def test_func(self):
        election = self.get_object()
        return self.request.user == election.created_by or self.request.user.has_perm('voting.change_election')
    
    def get_success_url(self):
        messages.success(self.request, _('Election updated successfully!'))
        return reverse_lazy('voting:election_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update Election')
        return context

class ElectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting an election."""
    model = Election
    template_name = 'voting/election_confirm_delete.html'
    success_url = reverse_lazy('voting:election_list')
    context_object_name = 'election'
    
    def test_func(self):
        election = self.get_object()
        return self.request.user == election.created_by or self.request.user.has_perm('voting.delete_election')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('Election deleted successfully!'))
        return super().delete(request, *args, **kwargs)
