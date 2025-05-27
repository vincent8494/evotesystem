# config/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

def home(request):
    context = {
        'has_dashboard': hasattr(request, 'user') and request.user.is_authenticated
    }
    return render(request, 'home.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        email_message = f"""
        Name: {name}
        Email: {email}
        Subject: {subject}
        
        Message:
        {message}
        """
        
        try:
            send_mail(
                subject=f"Contact Form: {subject}",
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, _('Thank you for your message. We will get back to you soon!'))
            return redirect('contact')
        except Exception as e:
            messages.error(request, _('There was an error sending your message. Please try again later.'))
    
    return render(request, 'contact.html')

def privacy_policy(request):
    return render(request, 'static_pages/privacy.html')

def terms_of_service(request):
    return render(request, 'static_pages/terms.html')

def faq(request):
    return render(request, 'static_pages/faq.html')

def about(request):
    return render(request, 'about.html')

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')