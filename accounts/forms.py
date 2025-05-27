import logging
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm, UserChangeForm, AuthenticationForm, 
    PasswordResetForm, SetPasswordForm
)
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, UserProfile

# Get the User model
UserModel = get_user_model()
logger = logging.getLogger(__name__)


class CustomUserCreationForm(UserCreationForm):
    """A form for creating new users with email as the unique identifier."""
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'required': 'required',
        })
    )
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a password'),
            'autocomplete': 'new-password',
        }),
        help_text=_("Your password must contain at least 8 characters."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password'),
            'autocomplete': 'new-password',
        }),
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'user_type')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('First name'),
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Last name'),
            }),
            'user_type': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove autofocus from username field (which is hidden)
        self.fields['email'].widget.attrs.pop('autofocus', None)


class CustomUserChangeForm(UserChangeForm):
    """A form for updating users with email as the unique identifier."""
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'is_superuser')


class CustomAuthenticationForm(AuthenticationForm):
    """Authentication form which uses email as the unique identifier."""
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autofocus': True,
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your password'),
            'autocomplete': 'current-password',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _('Email')


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    class Meta:
        model = UserProfile
        fields = [
            'gender', 'date_of_birth', 'profile_picture',
            'phone_number', 'address', 'id_number', 'bio',
            'party_affiliation'
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date',
                },
                format='%Y-%m-%d'
            ),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., +254700000000'),
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Your physical address'),
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('National ID/Passport Number'),
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Tell us about yourself...'),
            }),
            'party_affiliation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Political party or affiliation (if any)'),
            }),
        }
        help_texts = {
            'date_of_birth': _('Format: YYYY-MM-DD'),
            'profile_picture': _('Recommended size: 200x200 pixels'),
        }


class VoterRegistrationForm(forms.ModelForm):
    """Form for voters to register for an election."""
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('I agree to the terms and conditions of this election'),
        error_messages={
            'required': _('You must accept the terms and conditions to register.')
        }
    )

    class Meta:
        model = UserProfile
        fields = ['voter_id', 'id_number']
        widgets = {
            'voter_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your voter ID number'),
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('National ID/Passport Number'),
            }),
        }
        help_texts = {
            'voter_id': _('Your unique voter identification number'),
        }

    def __init__(self, *args, **kwargs):
        self.election = kwargs.pop('election', None)
        super().__init__(*args, **kwargs)

    def clean_voter_id(self):
        voter_id = self.cleaned_data.get('voter_id')
        # Add any voter ID validation logic here
        return voter_id

    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        # Add any ID number validation logic here
        return id_number

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.is_voter = True
        if commit:
            profile.save()
        return profile


class ResendVerificationForm(forms.Form):
    """Form for resending email verification."""
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'required': 'required',
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = UserModel._default_manager.get(email=email, is_active=True)
            if user.email_verified:
                raise forms.ValidationError(
                    _('This email has already been verified.')
                )
        except UserModel.DoesNotExist:
            # Don't reveal if the email exists for security reasons
            pass
            
        return email


class ResendActivationForm(forms.Form):
    """Form for resending account activation email."""
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'required': 'required',
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = UserModel._default_manager.get(email=email, is_active=False)
        except UserModel.DoesNotExist:
            # Don't reveal if the email exists for security reasons
            pass
            
        return email


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with improved email handling."""
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
        })
    )
    
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = send_mail(
            subject, body, from_email, [to_email],
            html_message=body,  # Use the HTML template as the email body
            fail_silently=False,
        )
        
        return email_message


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with improved styling."""
    new_password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter new password'),
            'autocomplete': 'new-password',
        }),
        strip=False,
        help_text=_('Your password must contain at least 8 characters.'),
    )
    new_password2 = forms.CharField(
        label=_('New password confirmation'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm new password'),
            'autocomplete': 'new-password',
        }),
    )
