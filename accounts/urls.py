from django.urls import path
from django.contrib.auth import views as auth_views
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from . import views
from .views import DashboardView

app_name = 'accounts'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Authentication URLs
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Email Verification URLs
    path('verify-email/<uidb64>/<token>/', 
         views.EmailVerificationView.as_view(), 
         name='verify_email'),
    path('verify-email/success/', 
         TemplateView.as_view(template_name='accounts/verification_success.html'), 
         name='verification_success'),
    path('verify-email/error/', 
         TemplateView.as_view(template_name='accounts/verification_error.html'), 
         name='verification_error'),
    path('resend-verification/', 
         views.ResendVerificationView.as_view(), 
         name='resend_verification'),
    
    # Account Activation URLs
    path('activate/<uidb64>/<token>/', 
         views.AccountActivationView.as_view(), 
         name='activate'),
    path('activate/success/', 
         TemplateView.as_view(template_name='accounts/activation_success.html'), 
         name='activation_success'),
    path('activate/error/', 
         TemplateView.as_view(template_name='accounts/activation_error.html'), 
         name='activation_error'),
    path('resend-activation/', 
         views.ResendActivationView.as_view(), 
         name='resend_activation'),
    
    # Dashboard URL
    path('dashboard/', 
         DashboardView.as_view(), 
         name='dashboard'),
    
    # Password reset URLs
    path('password/change/', 
         views.CustomPasswordChangeView.as_view(), 
         name='password_change'),
    path('password/reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/emails/password_reset_email.html',
             subject_template_name='accounts/emails/password_reset_subject.txt',
             success_url='done/'
         ), 
         name='password_reset'),
    path('password/reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/password/reset/complete/'
         ), 
         name='password_reset_confirm'),
    path('password/reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Profile URLs
    path('profile/<int:user_id>/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # Voter registration
    path('election/<int:election_id>/register/', 
         views.register_voter, 
         name='register_voter'),
    
    # Legal
    path('terms/', views.terms_and_conditions, name='terms'),
]
