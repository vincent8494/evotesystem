import six
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int, int_to_base36

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Strategy object used to generate and check tokens for account activation.
    """
    def _make_hash_value(self, user, timestamp):
        """
        Hash the user's primary key and some user state that's sure to change
        after account activation to produce a token that invalidated when it's used.
        
        The token is invalidated when the user activates their account.
        """
        # Ensure results are consistent across different Python versions
        login_timestamp = '' if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return (
            six.text_type(user.pk) + 
            six.text_type(timestamp) + 
            six.text_type(user.is_active) +
            six.text_type(login_timestamp)
        )
    
    def check_token(self, user, token):
        """
        Check that the account activation token is correct for a given user.
        """
        if not (user and token):
            return False
            
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False
            
        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False
            
        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return False
            
        # Check the timestamp is within limit
        if (self._num_days(self._today()) - ts) > settings.EMAIL_VERIFICATION_EXPIRE_DAYS:
            return False
            
        return True


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Strategy object used to generate and check tokens for email verification.
    """
    def _make_hash_value(self, user, timestamp):
        """
        Hash the user's primary key and email verification status to produce
        a token that's invalidated when the email is verified.
        """
        # Ensure results are consistent across different Python versions
        email_verified_at = '' if user.email_verified_at is None else user.email_verified_at.replace(microsecond=0, tzinfo=None)
        return (
            six.text_type(user.pk) + 
            six.text_type(timestamp) + 
            six.text_type(user.email_verified) +
            six.text_type(email_verified_at) +
            six.text_type(user.email)
        )
    
    def check_token(self, user, token):
        """
        Check that the email verification token is correct for a given user.
        """
        if not (user and token):
            return False
            
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False
            
        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False
            
        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return False
            
        # Check the timestamp is within limit
        if (self._num_days(self._today()) - ts) > settings.EMAIL_VERIFICATION_EXPIRE_DAYS:
            return False
            
        return True

# Create instances of token generators
account_activation_token = AccountActivationTokenGenerator()
email_verification_token = EmailVerificationTokenGenerator()
