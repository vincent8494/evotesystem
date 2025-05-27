from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserProfile


class CustomUserAdmin(UserAdmin):
    """Custom User Admin configuration."""
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type', 'phone_number')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )


class UserProfileAdmin(admin.ModelAdmin):
    """User Profile Admin configuration."""
    list_display = ('user', 'gender', 'voter_id', 'is_candidate', 'has_voted')
    list_filter = ('gender', 'is_candidate', 'has_voted')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'voter_id')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'gender', 'date_of_birth', 'profile_picture')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'address', 'id_number')
        }),
        ('Voter Information', {
            'fields': ('voter_id', 'has_voted')
        }),
        ('Candidate Information', {
            'classes': ('collapse',),
            'fields': ('is_candidate', 'bio', 'party_affiliation')
        }),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
