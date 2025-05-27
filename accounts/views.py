import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, UpdateView, DetailView, View, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from .tokens import account_activation_token, email_verification_token
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm,
    UserProfileForm, VoterRegistrationForm, ResendActivationForm, ResendVerificationForm
)

# Set up logging
logger = logging.getLogger(__name__)
UserModel = get_user_model()

from .models import CustomUser, UserProfile
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm,
    UserProfileForm, VoterRegistrationForm
)


class SignUpView(CreateView):
    """View for user registration with email verification."""
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:activation_sent')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create an Account')
        context['email_verification_required'] = getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', True)
        return context
    
    def form_valid(self, form):
        try:
            # Create user but don't save to DB yet
            self.object = form.save(commit=False)
            
            # Set user as inactive if email verification is required
            email_verification_required = getattr(settings, 'EMAIL_VERIFICATION_REQUIRED', True)
            self.object.is_active = not email_verification_required
            
            # Save the user to DB
            self.object.save()
            logger.info(f"New user created: {self.object.email}")
            
            # If email verification is required, send activation email
            if email_verification_required:
                try:
                    self.send_activation_email(self.object, self.request)
                    messages.info(
                        self.request,
                        _('Please check your email to activate your account.')
                    )
                    return redirect(self.get_success_url())
                except Exception as e:
                    logger.error(f"Error sending activation email to {self.object.email}: {e}", 
                                exc_info=True)
                    # Continue with auto-login if email fails but user was created
                    self.object.is_active = True
                    self.object.save()
                    messages.warning(
                        self.request,
                        _('Account created, but we couldn\'t send a verification email. You can log in directly.')
                    )
            
            # Auto-login if no email verification required or if email sending failed
            login(self.request, self.object)
            messages.success(
                self.request,
                _('Your account has been created and you are now logged in!')
            )
            return redirect('home')
            
        except Exception as e:
            logger.error(f"Error during user registration: {e}", exc_info=True)
            messages.error(
                self.request,
                _('An error occurred during registration. Please try again.')
            )
            return self.form_invalid(form)
    
    def send_activation_email(self, user, request):
        """Send account activation email to the user."""
        try:
            current_site = get_current_site(request)
            subject = _('Activate your account')
            
            # Generate tokens
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)
            
            context = {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http',
                'site_name': getattr(settings, 'SITE_NAME', 'E-Vote'),
            }
            
            # Render email content
            message = render_to_string('accounts/emails/account_activation.html', context)
            
            # Send email
            user.email_user(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                html_message=message
            )
            
            # Update verification timestamp
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=['email_verification_sent_at'])
            
            logger.info(f"Activation email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send activation email to {user.email}: {e}", exc_info=True)
            raise  # Re-raise to be handled by the caller
    
    def get_success_url(self):
        """Redirect to activation sent page after successful signup."""
        return reverse('accounts:activation_sent')


class EmailVerificationView(View):
    """View for verifying a user's email address."""
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None
        
        if user is not None and email_verification_token.check_token(user, token):
            if not user.email_verified:
                user.email_verified = True
                user.email_verified_at = timezone.now()
                user.save()
                messages.success(
                    request, 
                    _('Your email has been verified successfully!')
                )
                return redirect('accounts:verify-email-success')
            else:
                messages.info(
                    request,
                    _('Your email has already been verified.')
                )
                return redirect('accounts:verify-email-success')
        else:
            messages.error(
                request,
                _('The verification link is invalid or has expired.')
            )
            return redirect('accounts:verification_error')


class ResendVerificationView(FormView):
    """View for resending email verification."""
    form_class = ResendVerificationForm
    template_name = 'accounts/resend_verification.html'
    success_url = reverse_lazy('accounts:verification_success')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = UserModel.objects.get(email=email, is_active=True)
            if not user.email_verified:
                self.send_verification_email(user)
            else:
                messages.info(
                    self.request,
                    _('This email has already been verified.')
                )
                return redirect('accounts:login')
        except UserModel.DoesNotExist:
            # Don't reveal if the email exists for security reasons
            pass
            
        return super().form_valid(form)
    
    def send_verification_email(self, user):
        """Send email verification email."""
        current_site = get_current_site(self.request)
        subject = _('Verify your email address')
        
        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': user.get_uid,  # Removed parentheses to pass the method, not call it
            'token': email_verification_token.make_token(user),
            'protocol': 'https' if self.request.is_secure() else 'http',
            'site_name': getattr(settings, 'SITE_NAME', 'E-Vote'),
        }
        
        message = render_to_string('accounts/emails/email_verification.html', context)
        
        try:
            user.email_user(subject, message, html_message=message)
            logger.info(f"Verification email resent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to resend verification email to {user.email}: {e}")
            messages.error(
                self.request,
                _('Failed to send verification email. Please try again later.')
            )
            return False
        return True


class AccountActivationView(View):
    """View for activating a user's account."""
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = UserModel.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            user = None
        
        if user is not None and account_activation_token.check_token(user, token):
            if not user.is_active:
                user.is_active = True
                user.save()
                # Also verify email if not already verified
                if not user.email_verified:
                    user.email_verified = True
                    user.email_verified_at = timezone.now()
                    user.save()
                messages.success(
                    request,
                    _('Your account has been activated successfully! You can now log in.')
                )
                return redirect('accounts:activation_success')
            else:
                messages.info(
                    request,
                    _('Your account has already been activated.')
                )
                return redirect('accounts:activation_success')
        else:
            messages.error(
                request,
                _('The activation link is invalid or has expired.')
            )
            return redirect('accounts:activation_error')


class ResendActivationView(FormView):
    """View for resending account activation email."""
    form_class = ResendActivationForm
    template_name = 'accounts/resend_activation.html'
    success_url = reverse_lazy('accounts:activation_sent')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = UserModel.objects.get(email=email, is_active=False)
            self.send_activation_email(user)
        except UserModel.DoesNotExist:
            # Don't reveal if the email exists for security reasons
            pass
            
        return super().form_valid(form)
    
    def send_activation_email(self, user):
        """Send account activation email."""
        current_site = get_current_site(self.request)
        subject = _('Activate your account')
        
        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': user.get_uid(),
            'token': account_activation_token.make_token(user),
            'protocol': 'https' if self.request.is_secure() else 'http',
            'site_name': getattr(settings, 'SITE_NAME', 'E-Vote'),
            'expiration_days': settings.EMAIL_VERIFICATION_EXPIRE_DAYS,
        }
        
        message = render_to_string('accounts/emails/account_activation.html', context)
        
        try:
            user.email_user(subject, message, html_message=message)
            logger.info(f"Activation email resent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to resend activation email to {user.email}: {e}")
            messages.error(
                self.request,
                _('Failed to send activation email. Please try again later.')
            )
            return False
        return True


class ActivationSentView(TemplateView):
    """View shown after sending activation email."""
    template_name = 'accounts/activation_sent.html'


class VerificationSentView(TemplateView):
    """View shown after sending verification email."""
    template_name = 'accounts/verification_sent.html'


def login_view(request):
    """Custom login view with account activation check."""
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to home instead of election_list
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if not user.is_active:
                    # Activate the user if credentials are correct
                    user.is_active = True
                    user.email_verified = True
                    user.email_verified_at = timezone.now()
                    user.save()
                    
                # Log the user in regardless of email verification status
                login(request, user)
                messages.success(request, _('You are now logged in.'))
                next_url = request.POST.get('next', '')
                if next_url:
                    return redirect(next_url)
                return redirect('home')  # Always redirect to home by default
            else:
                messages.error(request, _('Invalid email or password.'))
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        form = CustomAuthenticationForm()
    
    context = {
        'form': form,
        'title': _('Log In'),
        'next': request.GET.get('next', '')
    }
    return render(request, 'accounts/login.html', context)


@login_required
def logout_view(request):
    """Log out the current user."""
    logout(request)
    messages.info(request, _('You have been logged out.'))
    return redirect('home')


class ProfileView(LoginRequiredMixin, DetailView):
    """View for viewing a user's profile."""
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'id'
    slug_url_kwarg = 'user_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['title'] = _('Profile: %(username)s') % {'username': user.get_full_name() or user.email}
        context['is_own_profile'] = (self.request.user == user)
        return context


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating a user's profile."""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    
    def get_object(self, queryset=None):
        return self.request.user.profile
    
    def test_func(self):
        return self.request.user == self.get_object().user
    
    def get_success_url(self):
        messages.success(self.request, _('Your profile has been updated!'))
        return reverse_lazy('profile', kwargs={'user_id': self.request.user.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Profile')
        return context


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """View for changing a user's password."""
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Change Password')
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, _('Your password has been changed!'))
        return response


@login_required
def register_voter(request, election_id=None):
    """View for voters to register for an election."""
    from voting.models import Election, VoterRegistration
    
    # Check if the election exists and is active
    try:
        election = Election.objects.get(id=election_id, is_active=True)
    except Election.DoesNotExist:
        raise PermissionDenied(_('This election is not available for registration.'))
    
    # Check if user is already registered for this election
    if VoterRegistration.objects.filter(voter=request.user, election=election).exists():
        messages.info(request, _('You are already registered for this election.'))
        return redirect('election_detail', pk=election_id)
    
    if request.method == 'POST':
        form = VoterRegistrationForm(
            request.POST,
            request.FILES,
            election=election,
            instance=request.user.profile
        )
        
        if form.is_valid():
            profile = form.save()
            
            # Create voter registration
            VoterRegistration.objects.create(
                voter=request.user,
                election=election,
                is_verified=False  # Will be verified by admin
            )
            
            messages.success(
                request,
                _('Your voter registration has been submitted for verification. '\
                  'You will be notified once your registration is approved.')
            )
            return redirect('election_detail', pk=election_id)
    else:
        form = VoterRegistrationForm(instance=request.user.profile, election=election)
    
    context = {
        'form': form,
        'election': election,
        'title': _('Register for Election: %(election)s') % {'election': election.name}
    }
    return render(request, 'accounts/register_voter.html', context)


def terms_and_conditions(request):
    """View for displaying terms and conditions."""
    return render(request, 'accounts/terms_and_conditions.html', {'title': _('Terms and Conditions')})


class DashboardView(LoginRequiredMixin, TemplateView):
    """View for the user dashboard."""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Dashboard')
        # Add any additional context data needed for the dashboard
        return context
