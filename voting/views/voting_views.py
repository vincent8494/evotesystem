"""
Views for handling voting functionality with role-based access control.
"""
from django.views.generic import FormView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.urls import reverse_lazy

from ..models import Vote, VoterRegistration
from ..forms import VoteForm
from ..view_mixins import (
    VoterRequiredMixin,
    ElectionVoterRequiredMixin,
    ActiveElectionMixin,
    PublicElectionMixin
)


class CastVoteView(ElectionVoterRequiredMixin, ActiveElectionMixin, FormView):
    """View for casting a vote in an election."""
    template_name = 'voting/cast_vote.html'
    form_class = VoteForm
    
    def get_election(self):
        """Get the election object from the URL parameter."""
        if not hasattr(self, '_election'):
            from ..models import Election
            self._election = Election.objects.get(pk=self.kwargs['pk'])
        return self._election
    
    def get_form_kwargs(self):
        """Add the election to the form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['election'] = self.get_election()
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Add the election to the template context."""
        context = super().get_context_data(**kwargs)
        context['election'] = self.get_election()
        return context
    
    def form_valid(self, form):
        """Process the vote form and save the vote."""
        election = self.get_election()
        
        with transaction.atomic():
            # Record the vote for each position
            for position, candidate in form.cleaned_data.items():
                if candidate:  # Skip positions with no selection
                    Vote.objects.create(
                        election=election,
                        position=position,
                        candidate=candidate,
                        voter=self.request.user
                    )
            
            # Mark the voter as having voted
            VoterRegistration.objects.filter(
                voter=self.request.user,
                election=election
            ).update(has_voted=True)
        
        messages.success(
            self.request,
            _('Your vote has been recorded successfully. Thank you for voting!')
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect to the election detail page after voting."""
        return reverse_lazy('voting:election_detail', kwargs={'pk': self.kwargs['pk']})
