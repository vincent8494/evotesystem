from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import CustomUser


from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Election(models.Model):
    """Model representing an election event."""
    # Basic Information
    name = models.CharField(_('election name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True, null=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    
    # Timing
    start_date = models.DateTimeField(_('start date'))
    end_date = models.DateTimeField(_('end date'))
    
    # Status
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (DRAFT, _('Draft')),
        (PUBLISHED, _('Published')),
        (ACTIVE, _('Active')),
        (COMPLETED, _('Completed')),
        (CANCELLED, _('Cancelled')),
    ]
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
    )
    
    # Access Control
    is_public = models.BooleanField(
        _('public election'),
        default=True,
        help_text=_('If checked, any authenticated user can view this election')
    )
    
    # Relationships
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='elections_created',
        verbose_name=_('created by')
    )
    managers = models.ManyToManyField(
        User,
        related_name='elections_managed',
        verbose_name=_('election managers'),
        blank=True,
        help_text=_('Users who can manage this election')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        permissions = [
            ('can_manage_elections', 'Can manage elections'),
            ('can_verify_election', 'Can verify election results'),
            ('can_view_results', 'Can view election results'),
            ('can_export_results', 'Can export election results'),
        ]
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('voting:election_detail', kwargs={'pk': self.pk})
    
    @property
    def is_active(self):
        """Check if the election is currently active."""
        now = timezone.now()
        return self.status == self.ACTIVE and self.start_date <= now <= self.end_date
    
    @property
    def is_running(self):
        """Alias for is_active for backward compatibility."""
        return self.is_active
    
    @property
    def has_ended(self):
        """Check if the election has ended."""
        return timezone.now() > self.end_date or self.status in [self.COMPLETED, self.CANCELLED]
    
    @property
    def can_vote(self):
        """Check if voting is currently allowed."""
        now = timezone.now()
        return self.status == self.ACTIVE and self.start_date <= now <= self.end_date
    
    def can_user_vote(self, user):
        """Check if a specific user can vote in this election."""
        if not user.is_authenticated:
            return False
            
        # Admins and managers cannot vote
        if user.is_superuser or user.is_staff or self.managers.filter(pk=user.pk).exists():
            return False
            
        # Check if user has already voted
        return not self.votes.filter(voter=user).exists()
    
    def can_user_manage(self, user):
        """Check if a user can manage this election."""
        if not user.is_authenticated:
            return False
            
        return (
            user.is_superuser or 
            user.is_staff or 
            user.has_perm('voting.can_manage_elections') or
            self.managers.filter(pk=user.pk).exists()
        )
    
    def get_status_display_with_dates(self):
        """Get status display with date information."""
        now = timezone.now()
        status_display = self.get_status_display()
        
        if self.status == self.DRAFT:
            return f"{status_display} (Not published)"
        elif self.status == self.PUBLISHED:
            if now < self.start_date:
                return f"{status_display} (Starts {self.start_date.strftime('%b %d, %Y %H:%M')})"
            else:
                return f"{status_display} (Should be active)"
        elif self.status == self.ACTIVE:
            if self.start_date <= now <= self.end_date:
                return f"{status_display} (Ends {self.end_date.strftime('%b %d, %Y %H:%M')})"
            elif now > self.end_date:
                return f"{status_display} (Ended {self.end_date.strftime('%b %d, %Y %H:%M')})"
            else:
                return status_display
        else:
            return status_display
        """Check if the election is currently active."""
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_active


class Position(models.Model):
    """Model representing a position that candidates can run for."""
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='positions',
        help_text="The election this position belongs to"
    )
    title = models.CharField(max_length=200, help_text="Title of the position")
    description = models.TextField(blank=True, null=True)
    max_votes = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of candidates a voter can select for this position"
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Used to order positions on the ballot (lower numbers come first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['election', 'priority', 'title']
        unique_together = ['election', 'title']

    def __str__(self):
        return f"{self.title} ({self.election.name})"


class Candidate(models.Model):
    """Model representing a candidate running for a position."""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='candidacies',
        help_text="The user who is a candidate"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='candidates',
        help_text="The position this candidate is running for"
    )
    bio = models.TextField(blank=True, null=True, help_text="Candidate's biography")
    manifesto = models.TextField(blank=True, null=True, help_text="Candidate's campaign promises")
    is_approved = models.BooleanField(
        default=False,
        help_text="Has this candidate been approved by an admin?"
    )
    photo = models.ImageField(
        upload_to='candidate_photos/',
        blank=True,
        null=True,
        help_text="Candidate's profile photo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'user__last_name', 'user__first_name']
        unique_together = ['user', 'position']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position.title}"

    @property
    def vote_count(self):
        """Return the number of votes this candidate has received."""
        return self.votes.count()


class Vote(models.Model):
    """Model representing a single vote cast by a voter."""
    voter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='votes_cast',
        help_text="The user who cast this vote"
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The candidate who received this vote"
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The election this vote was cast in"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='votes',
        help_text="The position this vote was cast for"
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text="IP address of the voter")
    user_agent = models.TextField(blank=True, null=True, help_text="User agent of the voter's browser")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['voter', 'position']

    def __str__(self):
        return f"Vote by {self.voter.email} for {self.candidate.user.get_full_name()} as {self.position.title}"


class VoterRegistration(models.Model):
    """Model representing a voter's registration for an election."""
    voter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='voter_registrations',
        help_text="The user who is registered to vote"
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='voter_registrations',
        help_text="The election the voter is registered for"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Has the voter's registration been verified?"
    )
    verification_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Verification code sent to the voter"
    )
    has_voted = models.BooleanField(
        default=False,
        help_text="Has the voter cast their vote?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['voter', 'election']

    def __str__(self):
        return f"{self.voter.email} - {self.election.name}"


class ElectionResult(models.Model):
    """Model for storing election results."""
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='election_results',
        help_text="The election these results are for"
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='election_results',
        help_text="The position these results are for"
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='election_results',
        help_text="The candidate these results are for"
    )
    total_votes = models.PositiveIntegerField(
        default=0,
        help_text="Total number of votes received by this candidate for this position"
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Percentage of total votes received"
    )
    is_winner = models.BooleanField(
        default=False,
        help_text="Did this candidate win the position?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['election', 'position', '-total_votes']
        unique_together = ['election', 'position', 'candidate']

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.position.title} - {self.total_votes} votes"

    def save(self, *args, **kwargs):
        # Calculate percentage if total_votes is updated
        total_position_votes = ElectionResult.objects.filter(
            election=self.election,
            position=self.position
        ).aggregate(models.Sum('total_votes'))['total_votes__sum'] or 0
        
        if total_position_votes > 0:
            self.percentage = (self.total_votes / total_position_votes) * 100
        else:
            self.percentage = 0.00
            
        super().save(*args, **kwargs)
