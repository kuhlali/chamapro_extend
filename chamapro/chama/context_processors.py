# chama/context_processors.py
from django.conf import settings

def seo_metadata(request):
    """SEO: Add meta data to all templates"""
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'ChamaPro'),
        'site_description': getattr(settings, 'SITE_DESCRIPTION', 'Professional Chama Management Platform'),
        'site_keywords': getattr(settings, 'SITE_KEYWORDS', 'chama, investment group, M-Pesa'),
        'site_author': getattr(settings, 'SITE_AUTHOR', 'ChamaPro Team'),
        'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'canonical_url': request.build_absolute_uri(request.path),
        'og_type': 'website',
        'twitter_card': 'summary_large_image',
        'DEBUG': settings.DEBUG,
    }

def site_settings(request):
    """SEO: Site-wide settings"""
    return {
        'DEBUG': settings.DEBUG,
    }