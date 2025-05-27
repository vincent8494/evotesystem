"""
Views for displaying and exporting election results.
"""
import csv
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse_lazy

from ..models import Election, Vote, Position, Candidate, VoterRegistration
from ..view_mixins import PublicElectionMixin, ManagerRequiredMixin


class ElectionResultsView(PublicElectionMixin, TemplateView):
    """View for displaying election results."""
    template_name = 'voting/election_results.html'
    
    def get_context_data(self, **kwargs):
        """Add election results to the template context."""
        context = super().get_context_data(**kwargs)
        election = self.get_object()
        
        # Get all positions and their vote counts
        positions = []
        for position in election.positions.all():
            # Get vote counts for each candidate in this position
            candidates = []
            for candidate in position.candidates.all():
                vote_count = Vote.objects.filter(
                    election=election,
                    position=position,
                    candidate=candidate
                ).count()
                
                candidates.append({
                    'candidate': candidate,
                    'vote_count': vote_count,
                    'percentage': (vote_count / position.votes.count() * 100) 
                                if position.votes.exists() else 0
                })
            
            # Sort candidates by vote count (descending)
            candidates.sort(key=lambda x: x['vote_count'], reverse=True)
            
            positions.append({
                'position': position,
                'candidates': candidates,
                'total_votes': position.votes.count(),
                'voter_count': election.voters.count(),
                'voter_turnout': (position.votes.count() / election.voters.count() * 100) 
                               if election.voters.exists() else 0
            })
        
        context.update({
            'election': election,
            'positions': positions,
            'is_manager': election.can_user_manage(self.request.user),
            'can_export': election.status in ['completed', 'cancelled'] or \
                         election.can_user_manage(self.request.user)
        })
        
        return context
    
    def get_object(self):
        """Get the election object from the URL parameter."""
        if not hasattr(self, '_election'):
            self._election = Election.objects.get(pk=self.kwargs['pk'])
        return self._election


def export_election_results(request, pk):
    """Export election results as a CSV file."""
    try:
        election = Election.objects.get(pk=pk)
        
        # Check permissions
        if not election.can_user_manage(request.user):
            messages.error(request, _("You don't have permission to export these results."))
            return redirect('voting:election_detail', pk=election.pk)
        
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="election_{election.id}_results.csv"'
        
        # Create the CSV writer
        writer = csv.writer(response)
        
        # Write the header row
        writer.writerow([
            'Position',
            'Candidate',
            'Vote Count',
            'Percentage',
            'Winner'
        ])
        
        # Write data rows
        for position in election.positions.all():
            total_votes = position.votes.count()
            
            # Get all candidates for this position with their vote counts
            candidates_data = []
            for candidate in position.candidates.all():
                vote_count = Vote.objects.filter(
                    election=election,
                    position=position,
                    candidate=candidate
                ).count()
                
                percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
                candidates_data.append((candidate, vote_count, percentage))
            
            # Sort by vote count (descending)
            candidates_data.sort(key=lambda x: x[1], reverse=True)
            
            # Determine the winner (candidates with the highest vote count)
            max_votes = candidates_data[0][1] if candidates_data else 0
            
            # Write each candidate's data
            for candidate, vote_count, percentage in candidates_data:
                is_winner = vote_count == max_votes and max_votes > 0
                writer.writerow([
                    position.name,
                    str(candidate),
                    vote_count,
                    f"{percentage:.2f}%",
                    "Winner" if is_winner else ""
                ])
            
            # Add an empty row between positions for better readability
            writer.writerow([])
        
        # Add summary information
        writer.writerow(['Election Summary'])
        writer.writerow(['Total Voters', election.voters.count()])
        writer.writerow(['Total Votes Cast', election.votes.count()])
        
        return response
        
    except Election.DoesNotExist:
        messages.error(request, _("Election not found."))
        return redirect('voting:election_list')
