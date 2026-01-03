# chamapro/urls.py
from django.contrib import admin
from django.urls import path, include
from chama import views as chama_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Allauth URLs
    path('users/', include('allauth.urls')),
    
    # Create an alias for 'login' that points to allauth's login
    path('login/', RedirectView.as_view(pattern_name='account_login'), name='login'),
    path('logout/', RedirectView.as_view(pattern_name='account_logout'), name='logout'),
    path('register/', RedirectView.as_view(pattern_name='account_signup'), name='register'),
    path('dashboard/', chama_views.dashboard_view, name='dashboard'),
    path('create/', chama_views.create_chama, name='create'),

    # Redirect global members link to dashboard (Fix for NoReverseMatch)
    path('members/', chama_views.dashboard_view, name='members'),
    path('reports/', chama_views.reports_view, name='reports'),
    path('features/', chama_views.features_view, name='features'),
    path('profile/', chama_views.profile_view, name='profile'),
    path('account/profile/', RedirectView.as_view(pattern_name='profile')), # Safety redirect
    path('settings/', RedirectView.as_view(pattern_name='profile')), # Redirect /settings to /profile
    
    # Home page
    path('', chama_views.home_view, name='home'),
    
    # Static pages
    path('about/', chama_views.about_view, name='about'),
    path('contact/', chama_views.contact_view, name='contact'),
    path('privacy/', chama_views.privacy_view, name='privacy'),
    path('terms/', chama_views.terms_view, name='terms'),
    path('cookies/', chama_views.cookies_view, name='cookies'),
    
    # App URLs (comment these out if they're causing errors)
    path('chama/', include('chama.urls', namespace='chama')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('users/', include('users.urls', namespace='users')),
    path('api/', include('api.urls', namespace='api')),
]