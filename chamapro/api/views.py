from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from payments.models import MpesaTransaction

@login_required
def dashboard_charts(request):
    """
    Returns JSON data for dashboard charts:
    1. Monthly contributions trend (Last 6 months)
    2. Transaction status distribution (Success vs Failed vs Pending)
    """
    # Calculate date 6 months ago to filter recent data
    six_months_ago = timezone.now() - timedelta(days=180)
    
    # --- Chart 1: Monthly Contributions Trend ---
    # Filter for successful contributions by the logged-in user
    contributions = MpesaTransaction.objects.filter(
        user=request.user,
        transaction_type='CONTRIBUTION',
        status='SUCCESS',
        transaction_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('transaction_date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    trend_labels = []
    trend_data = []
    
    for entry in contributions:
        if entry['month']:
            trend_labels.append(entry['month'].strftime('%b %Y'))
            trend_data.append(float(entry['total'] or 0))
            
    # --- Chart 2: Transaction Status Distribution ---
    status_counts = MpesaTransaction.objects.filter(
        user=request.user
    ).values('status').annotate(
        count=Count('id')
    )
    
    status_labels = [entry['status'] for entry in status_counts]
    status_data = [entry['count'] for entry in status_counts]
        
    return JsonResponse({
        'trend': {
            'labels': trend_labels,
            'data': trend_data
        },
        'distribution': {
            'labels': status_labels,
            'data': status_data
        }
    })
