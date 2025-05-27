from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from . import views

app_name = 'voting'  # This sets the application namespace

urlpatterns = [
    # Election URLs
    path('elections/', 
         views.ElectionListView.as_view(), 
         name='election_list'),
    path('elections/create/', 
         views.ElectionCreateView.as_view(),
         name='election_create'),
    path('elections/<int:pk>/', 
         views.ElectionDetailView.as_view(),
         name='election_detail'),
    path('elections/<int:pk>/results/', 
         views.ElectionResultsView.as_view(),
         name='election_results'),
    path('elections/<int:pk>/update/', 
         views.ElectionUpdateView.as_view(),
         name='election_update'),
    path('elections/<int:pk>/delete/', 
         views.ElectionDeleteView.as_view(),
         name='election_delete'),
    
    # Election status management
    path('elections/<int:pk>/publish/', 
         require_http_methods(['POST'])(views.toggle_election_status),
         {'status': 'published'},
         name='election_publish'),
    path('elections/<int:pk>/activate/', 
         require_http_methods(['POST'])(views.toggle_election_status),
         {'status': 'active'},
         name='election_activate'),
    path('elections/<int:pk>/complete/', 
         require_http_methods(['POST'])(views.toggle_election_status),
         {'status': 'completed'},
         name='election_complete'),
    path('elections/<int:pk>/cancel/', 
         require_http_methods(['POST'])(views.toggle_election_status),
         {'status': 'cancelled'},
         name='election_cancel'),
    
    # Voting
    path('elections/<int:pk>/vote/', 
         views.CastVoteView.as_view(),
         name='election_vote'),
    
    # Results
    path('elections/<int:pk>/results/', 
         views.ElectionResultsView.as_view(),
         name='election_results'),
    path('elections/<int:pk>/export/', 
         views.export_election_results,
         name='election_export_results'),
]
