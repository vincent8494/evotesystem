import uuid
from datetime import timedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .tokens import account_activation_token, email_verification_token



class CustomUserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """Custom user model that uses email as the unique identifier."""
    USER_TYPE_CHOICES = (
        ('voter', 'Voter'),
        ('candidate', 'Candidate'),
        ('election_officer', 'Election Officer'),
        ('admin', 'System Administrator'),
    )
    
    # Remove username field and use email as the username
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # User type and status fields
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='voter')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Email verification fields
    email_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    email_verified_at = models.DateTimeField(_('email verified at'), null=True, blank=True)
    email_verification_sent_at = models.DateTimeField(_('verification email sent at'), null=True, blank=True)
    
    # Account status fields
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    
    # Security fields
    security_token = models.UUIDField(default=uuid.uuid4, editable=False)
    token_created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('-created_at',)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]
    
    def get_uid(self):
        """Get the user's base64 encoded ID for use in verification links."""
        return urlsafe_base64_encode(force_bytes(self.pk))
    
    def is_verification_token_valid(self, token, token_generator):
        """Check if the verification token is valid for this user."""
        return token_generator.check_token(self, token)
    
    def send_verification_email(self, request=None):
        """Send an email verification link to the user."""
        current_site = get_current_site(request) if request else None
        site_name = current_site.name if current_site else settings.SITE_NAME
        domain = current_site.domain if current_site else settings.SITE_DOMAIN
        
        context = {
            'user': self,
            'domain': domain,
            'site_name': site_name,
            'uid': self.get_uid(),
            'token': email_verification_token.make_token(self),
            'protocol': 'https' if request and request.is_secure() else 'http',
        }
        
        subject = _('Verify your email address')
        message = render_to_string('accounts/emails/email_verification.html', context)
        
        try:
            self.email_user(subject, message, html_message=message)
            self.email_verification_sent_at = timezone.now()
            self.save(update_fields=['email_verification_sent_at'])
            return True
        except Exception as e:
            # Log the error but don't expose it to the user
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send verification email to {self.email}: {e}")
            return False
    
    def send_activation_email(self, request=None):
        """Send an account activation email to the user."""
        current_site = get_current_site(request) if request else None
        site_name = current_site.name if current_site else settings.SITE_NAME
        domain = current_site.domain if current_site else settings.SITE_DOMAIN
        
        context = {
            'user': self,
            'domain': domain,
            'site_name': site_name,
            'uid': self.get_uid(),
            'token': account_activation_token.make_token(self),
            'protocol': 'https' if request and request.is_secure() else 'http',
            'expiration_days': getattr(settings, 'EMAIL_VERIFICATION_EXPIRE_DAYS', 7),
        }
        
        subject = _('Activate your account')
        message = render_to_string('accounts/emails/account_activation.html', context)
        
        try:
            self.email_user(subject, message, html_message=message)
            return True
        except Exception as e:
            # Log the error but don't expose it to the user
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send activation email to {self.email}: {e}")
            return False
    
    def verify_email(self):
        """Mark the user's email as verified."""
        if not self.email_verified:
            self.email_verified = True
            self.email_verified_at = timezone.now()
            self.save(update_fields=['email_verified', 'email_verified_at', 'updated_at'])
            return True
        return False
    
    def activate(self):
        """Activate the user's account."""
        if not self.is_active:
            self.is_active = True
            # Also verify email if not already verified
            if not self.email_verified:
                self.verify_email()
            self.save(update_fields=['is_active', 'email_verified', 'email_verified_at', 'updated_at'])
            return True
        return False
    
    def get_email_verification_url(self, request=None):
        """Get the email verification URL for the user."""
        current_site = get_current_site(request) if request else None
        domain = current_site.domain if current_site else settings.SITE_DOMAIN
        protocol = 'https' if request and request.is_secure() else 'http'
        
        return f"{protocol}://{domain}/accounts/verify-email/{self.get_uid()}/{email_verification_token.make_token(self)}/"
    
    def get_activation_url(self, request=None):
        """Get the account activation URL for the user."""
        current_site = get_current_site(request) if request else None
        domain = current_site.domain if current_site else settings.SITE_DOMAIN
        protocol = 'https' if request and request.is_secure() else 'http'
        
        return f"{protocol}://{domain}/accounts/activate/{self.get_uid()}/{account_activation_token.make_token(self)}/"


class UserProfile(models.Model):
    """Extended user profile information."""
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    id_number = models.CharField(max_length=20, blank=True, null=True, help_text='National ID/Passport Number')
    
    # Additional fields for voters
    voter_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    has_voted = models.BooleanField(default=False)
    
    # Additional fields for candidates
    is_candidate = models.BooleanField(default=False)
    bio = models.TextField(blank=True, null=True)
    party_affiliation = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Profile"
