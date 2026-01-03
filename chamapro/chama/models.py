import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from datetime import date

User = get_user_model()

class Chama(models.Model):
    """SEO-Optimized Chama Model"""
    
    PLAN_CHOICES = [
        ('BASIC', 'Starter (Free)'),
        ('STANDARD', 'Growth (KES 500/mo)'),
        ('PREMIUM', 'Enterprise (KES 1,200/mo)'),
    ]

    FREQUENCY_CHOICES = [
        ('MONTHLY', 'Monthly'),
        ('WEEKLY', 'Weekly'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # SEO: Title and slug for URLs
    name = models.CharField(
        _('chama name'),
        max_length=200,
        db_index=True,
        help_text=_('Unique name for your chama group')
    )
    
    slug = models.SlugField(
        _('slug'),
        max_length=250,
        unique=True,
        blank=True,
        help_text=_('Auto-generated URL-friendly version of the name')
    )
    
    # SEO: Rich description
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed description of your chama (appears in search results)')
    )
    
    # SEO: Short excerpt for meta descriptions
    excerpt = models.CharField(
        _('excerpt'),
        max_length=160,
        blank=True,
        help_text=_('Short summary (max 160 chars for meta description)')
    )
    
    # Financial settings
    contribution_frequency = models.CharField(
        _('contribution frequency'),
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default='MONTHLY'
    )

    monthly_contribution = models.DecimalField(
        _('contribution amount'),
        max_digits=10,
        decimal_places=2
    )
    
    contribution_day = models.IntegerField(
        _('contribution day (monthly)'),
        default=1,
        help_text=_('Day of month when contributions are due (1-28)'),
        blank=True, null=True
    )

    contribution_weekday = models.IntegerField(
        _('contribution day (weekly)'),
        choices=WEEKDAY_CHOICES,
        null=True, blank=True,
        help_text=_('Day of the week when contributions are due')
    )

    penalty_amount = models.DecimalField(
        _('penalty amount'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Penalty amount for late contributions')
    )
    
    penalty_grace_period = models.IntegerField(
        _('penalty grace period'),
        default=7,
        help_text=_('Days after contribution day before penalty applies')
    )
    
    # SEO: Location data (important for local SEO)
    county = models.CharField(
        _('county'),
        max_length=100,
        db_index=True,
        help_text=_('County where the chama is based')
    )
    
    constituency = models.CharField(
        _('constituency'),
        max_length=100,
        blank=True,
        db_index=True
    )
    
    # Contact information
    phone = models.CharField(_('phone'), max_length=15)
    email = models.EmailField(_('email'), blank=True)
    
    # SEO: Image for social sharing
    logo = models.ImageField(
        _('logo'),
        upload_to='chama_logos/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_('Recommended size: 1200x630px for social sharing')
    )
    
    # Status and visibility
    is_active = models.BooleanField(_('active'), default=True, db_index=True)
    is_public = models.BooleanField(
        _('public'),
        default=False,
        help_text=_('If checked, this chama appears in public listings')
    )
    
    # Subscription & Plans
    subscription_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='BASIC')
    subscription_status = models.CharField(max_length=20, default='ACTIVE') # ACTIVE, EXPIRED
    subscription_expiry = models.DateTimeField(_('subscription expiry'), null=True, blank=True)
    
    # SEO: Meta fields
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True)
    meta_description = models.TextField(_('meta description'), max_length=160, blank=True)
    meta_keywords = models.CharField(_('meta keywords'), max_length=255, blank=True)
    
    # Financial tracking
    total_balance = models.DecimalField(
        _('total balance'),
        max_digits=12,
        decimal_places=2,
        default=0,
        db_index=True
    )
    
    # Timestamps for freshness
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chamas'
    )
    members = models.ManyToManyField(User, related_name='chamas', blank=True)
    
    class Meta:
        verbose_name = _('chama')
        verbose_name_plural = _('chamas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['county', 'is_public']),
            models.Index(fields=['created_at', 'total_balance']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """SEO: Auto-generate slug and meta data"""
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Auto-generate meta data if not provided
        if not self.meta_title:
            self.meta_title = f"{self.name} - ChamaPro Investment Group"
        
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt
        elif not self.meta_description:
            self.meta_description = f"Join {self.name} chama in {self.county}. Monthly contribution: KSh {self.monthly_contribution}"
        
        if not self.meta_keywords:
            self.meta_keywords = f"chama, investment group, {self.county}, savings, Kenya"
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """SEO: Canonical URL"""
        return reverse('chama:chama_detail', kwargs={'slug': self.slug, 'pk': self.id})
    
    def get_meta_image_url(self):
        """SEO: Open Graph image URL"""
        if self.logo:
            return self.logo.url
        return '/static/img/chama-default-og.jpg'  # Default OG image
    
    @property
    def active_members_count(self):
        return self.members.filter(is_active=True).count()
    
    @property
    def next_contribution_date(self):
        today = date.today()
        return date(today.year, today.month, self.contribution_day)
    
    def get_schema_org_data(self):
        """SEO: Structured data for Google"""
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.name,
            "description": self.excerpt or self.description[:150],
            "url": self.get_absolute_url(),
            "location": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": self.county,
                    "addressRegion": "Kenya"
                }
            }
        }

class Loan(models.Model):
    """Loan Model for Chama Members"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('DISBURSED', 'Disbursed'),
        ('PAID', 'Fully Paid'),
    ]
    
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='loans')
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(_('interest rate (%)'), max_digits=5, decimal_places=2, default=10.0)
    duration_months = models.IntegerField(_('duration (months)'), default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    
    request_date = models.DateTimeField(auto_now_add=True)
    action_date = models.DateTimeField(null=True, blank=True)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_loans')
    
    repayment_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-request_date']
        
    def __str__(self):
        return f"{self.borrower} - {self.amount} ({self.status})"
        
    @property
    def total_repayment(self):
        return self.amount * (1 + (self.interest_rate / 100))
    
class Investment(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('matured', 'Matured'),
        ('liquidated', 'Liquidated'),
        ('loss', 'Loss'),
    )

    chama = models.ForeignKey('Chama', on_delete=models.CASCADE, related_name='investments')
    name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_invested = models.DateField()
    expected_return_date = models.DateField(null=True, blank=True)
    expected_return_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_return_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.chama.name}"

class Penalty(models.Model):
    """Model to track penalties for late contributions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='penalties')
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='penalties')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_assessed = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=200) # e.g., "Late payment for Jan 2024"
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.reason})"
