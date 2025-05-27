from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, Permission
from .models import Election, Position, Candidate, Vote, VoterRegistration, ElectionResult
from .permissions import is_election_manager

User = get_user_model()


class PositionInline(admin.TabularInline):
    """Inline admin for positions in an election."""
    model = Position
    extra = 1
    fields = ('title', 'description', 'max_votes', 'priority')
    show_change_link = True


class CandidateInline(admin.TabularInline):
    """Inline admin for candidates in a position."""
    model = Candidate
    extra = 1
    fields = ('user', 'is_approved', 'photo', 'vote_count')
    readonly_fields = ('vote_count',)
    raw_id_fields = ('user',)
    show_change_link = True


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    """Admin configuration for the Election model with role-based access control."""
    list_display = ('name', 'status_display', 'start_date', 'end_date', 'is_public', 'manager_count', 'created_by')
    list_filter = ('status', 'is_public', 'start_date', 'end_date')
    search_fields = ('name', 'description', 'created_by__username')
    date_hierarchy = 'start_date'
    readonly_fields = ('status_display', 'created_at', 'updated_at', 'created_by')
    filter_horizontal = ('managers',)
    inlines = [PositionInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'status', 'is_public')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Management', {
            'fields': ('created_by', 'managers')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Limit elections to those the user can manage."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(managers=request.user)
    
    def save_model(self, request, obj, form, change):
        """Set the created_by field to the current user if this is a new election."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """Only allow users to change elections they manage."""
        if obj is None:
            return super().has_change_permission(request, obj)
        return obj.can_user_manage(request.user)
    
    def has_delete_permission(self, request, obj=None):
        """Only allow users to delete elections they manage."""
        if obj is None:
            return super().has_delete_permission(request, obj)
        return obj.can_user_manage(request.user)
    
    def status_display(self, obj):
        """Display status with color coding."""
        status_map = {
            'draft': 'gray',
            'published': 'blue',
            'active': 'green',
            'completed': 'purple',
            'cancelled': 'red',
        }
        color = status_map.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display().upper()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def manager_count(self, obj):
        return obj.managers.count()
    manager_count.short_description = 'Managers'


class CandidateInline(admin.TabularInline):
    """Inline admin for candidates in a position."""
    model = Candidate
    extra = 1
    readonly_fields = ('vote_count',)
    fields = ('user', 'is_approved', 'photo', 'vote_count')
    raw_id_fields = ('user',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for the Position model."""
    list_display = ('title', 'election', 'candidate_count', 'max_votes', 'priority')
    list_filter = ('election',)
    search_fields = ('title', 'description')
    inlines = [CandidateInline]
    
    def candidate_count(self, obj):
        return obj.candidates.count()
    candidate_count.short_description = 'Candidates'


class VoteInline(admin.TabularInline):
    """Inline admin for votes in a candidate."""
    model = Vote
    extra = 0
    readonly_fields = ('voter', 'created_at')
    raw_id_fields = ('voter',)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin configuration for the Candidate model."""
    list_display = ('__str__', 'position', 'is_approved', 'vote_count')
    list_filter = ('is_approved', 'position__election', 'position')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    list_editable = ('is_approved',)
    readonly_fields = ('vote_count', 'created_at', 'updated_at')
    raw_id_fields = ('user',)
    inlines = [VoteInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'position', 'is_approved', 'photo')
        }),
        ('Campaign Information', {
            'fields': ('bio', 'manifesto')
        }),
        ('Statistics', {
            'fields': ('vote_count',)
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def vote_count(self, obj):
        return obj.votes.count()
    vote_count.short_description = 'Votes Received'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin configuration for the Vote model."""
    list_display = ('voter', 'candidate', 'position', 'election', 'created_at')
    list_filter = ('election', 'position')
    search_fields = (
        'voter__email', 'voter__first_name', 'voter__last_name',
        'candidate__user__first_name', 'candidate__user__last_name'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('voter', 'candidate', 'election', 'position')
        }),
        ('Technical Information', {
            'classes': ('collapse',),
            'fields': ('ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(VoterRegistration)
class VoterRegistrationAdmin(admin.ModelAdmin):
    """Admin configuration for the VoterRegistration model."""
    list_display = ('voter', 'election', 'is_verified', 'has_voted', 'created_at')
    list_filter = ('is_verified', 'has_voted', 'election')
    search_fields = (
        'voter__email', 'voter__first_name', 'voter__last_name',
        'verification_code'
    )
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('voter',)
    
    fieldsets = (
        (None, {
            'fields': ('voter', 'election')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_code', 'has_voted')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ElectionResult)
class ElectionResultAdmin(admin.ModelAdmin):
    """Admin configuration for the ElectionResult model."""
    list_display = ('candidate', 'position', 'election', 'total_votes', 'percentage', 'is_winner')
    list_filter = ('election', 'position', 'is_winner')
    search_fields = (
        'candidate__user__first_name', 'candidate__user__last_name',
        'position__title', 'election__name'
    )
    readonly_fields = ('percentage', 'created_at', 'updated_at')
    list_editable = ('is_winner',)
    
    fieldsets = (
        (None, {
            'fields': ('election', 'position', 'candidate')
        }),
        ('Results', {
            'fields': ('total_votes', 'percentage', 'is_winner')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'election', 'position', 'candidate', 'candidate__user'
        )
