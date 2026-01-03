import json
from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import F, Sum
from django.contrib.auth import get_user_model
from .utils import MpesaGateWay
from .models import MpesaTransaction
from chama.models import Chama, Penalty

@login_required
def initiate_payment(request):
    if request.method == "POST":
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        
        if not phone or not amount:
            return JsonResponse({'error': 'Phone and Amount are required'}, status=400)

        # Identify user by phone number
        User = get_user_model()
        transaction_user = request.user
        
        # Normalize phone for lookup (e.g., 0712... to 254712...)
        clean_phone = phone.strip()
        if clean_phone.startswith('0'):
            clean_phone = '254' + clean_phone[1:]
        
        user_by_phone = User.objects.filter(phone_number=clean_phone).first()
        if user_by_phone:
            transaction_user = user_by_phone

        gateway = MpesaGateWay()
        response = gateway.stk_push(phone, amount, account_reference="Contribution")
        
        if response.get('ResponseCode') == '0':
            MpesaTransaction.objects.create(
                user=transaction_user,
                transaction_type='CONTRIBUTION',
                merchant_request_id=response.get('MerchantRequestID'),
                checkout_request_id=response.get('CheckoutRequestID'),
                amount=amount,
                phone_number=phone,
                status='PENDING'
            )
            return JsonResponse(response)
        else:
            return JsonResponse(response, status=400)
            
    return render(request, 'payments/initiate.html')

@login_required
def initiate_contribution(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    
    # --- PENALTY CHECK LOGIC ---
    today = timezone.now().date()
    
    # 1. Check if user is late for MONTHLY contribution
    if chama.contribution_frequency == 'MONTHLY' and chama.contribution_day:
        # Construct due date for this month
        try:
            due_date = today.replace(day=chama.contribution_day)
        except ValueError:
            due_date = today.replace(day=28) # Fallback for short months
            
        cutoff_date = due_date + timedelta(days=chama.penalty_grace_period)
        
        # If today is past the cutoff (Grace period over)
        if today > cutoff_date:
            # Check if they have paid for this month
            has_paid = MpesaTransaction.objects.filter(
                user=request.user,
                chama=chama,
                transaction_type='CONTRIBUTION',
                status='SUCCESS',
                transaction_date__month=today.month,
                transaction_date__year=today.year
            ).exists()
            
            if not has_paid:
                # Create penalty if it doesn't exist yet
                reason = f"Late Contribution: {today.strftime('%B %Y')}"
                Penalty.objects.get_or_create(
                    user=request.user,
                    chama=chama,
                    reason=reason,
                    defaults={'amount': chama.penalty_amount}
                )

    # 2. Calculate Total Due (Contribution + Unpaid Penalties)
    unpaid_penalties = Penalty.objects.filter(user=request.user, chama=chama, is_paid=False)
    penalty_total = sum(p.amount for p in unpaid_penalties)
    
    suggested_amount = chama.monthly_contribution + penalty_total
    
    # Allow pre-filling amount from query params (e.g. ?amount=500)
    initial_amount = request.GET.get('amount', suggested_amount)
    
    if request.method == "POST":
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        
        if not phone or not amount:
            return render(request, 'payments/contribution_form.html', {'chama': chama, 'error': 'Phone and Amount are required', 'initial_amount': initial_amount, 'penalties': unpaid_penalties, 'penalty_total': penalty_total})

        # Identify user by phone number
        User = get_user_model()
        transaction_user = request.user
        
        # Normalize phone for lookup
        clean_phone = phone.strip()
        if clean_phone.startswith('0'):
            clean_phone = '254' + clean_phone[1:]
            
        user_by_phone = User.objects.filter(phone_number=clean_phone).first()
        if user_by_phone:
            transaction_user = user_by_phone

        gateway = MpesaGateWay()
        # Use Chama Name as reference (truncated to 12 chars for API limits)
        account_ref = chama.name[:12].replace(" ", "")
        response = gateway.stk_push(phone, amount, account_reference=account_ref)
        
        if response.get('ResponseCode') == '0':
            MpesaTransaction.objects.create(
                user=transaction_user,
                chama=chama,
                transaction_type='CONTRIBUTION',
                merchant_request_id=response.get('MerchantRequestID'),
                checkout_request_id=response.get('CheckoutRequestID'),
                amount=amount,
                phone_number=phone,
                status='PENDING'
            )
            return redirect('chama:chama_detail', slug=chama.slug, pk=chama.id)
        else:
            return render(request, 'payments/contribution_form.html', {'chama': chama, 'error': response.get('ResponseDescription', 'Payment Failed'), 'initial_amount': amount, 'penalties': unpaid_penalties, 'penalty_total': penalty_total})
            
    return render(request, 'payments/contribution_form.html', {'chama': chama, 'initial_amount': initial_amount, 'penalties': unpaid_penalties, 'penalty_total': penalty_total})

@login_required
def pay_subscription(request, chama_id):
    """View to handle monthly subscription payments"""
    chama = get_object_or_404(Chama, id=chama_id)
    
    # Determine amount based on plan
    amount = 0
    if chama.subscription_plan == 'STANDARD':
        amount = 500
    elif chama.subscription_plan == 'PREMIUM':
        amount = 1200
    else:
        # Basic plan doesn't need payment
        return redirect('chama:dashboard')

    if request.method == "POST":
        phone = request.POST.get('phone')
        
        if not phone:
            return render(request, 'payments/pay_subscription.html', {'chama': chama, 'amount': amount, 'error': 'Phone number is required'})

        # Normalize phone
        clean_phone = phone.strip()
        if clean_phone.startswith('0'):
            clean_phone = '254' + clean_phone[1:]

        gateway = MpesaGateWay()
        account_ref = f"SUB-{chama.name[:8]}".replace(" ", "")
        
        # Initiate STK Push
        response = gateway.stk_push(clean_phone, amount, account_reference=account_ref, transaction_desc=f"Subscription for {chama.name}")
        
        if response.get('ResponseCode') == '0':
            MpesaTransaction.objects.create(
                user=request.user,
                chama=chama,
                transaction_type='SUBSCRIPTION',
                merchant_request_id=response.get('MerchantRequestID'),
                checkout_request_id=response.get('CheckoutRequestID'),
                amount=amount,
                phone_number=clean_phone,
                status='PENDING',
                description=f"Monthly {chama.subscription_plan} Subscription"
            )
            # Show success message or redirect to a waiting page
            return render(request, 'payments/pay_subscription.html', {
                'chama': chama, 
                'amount': amount, 
                'success': True, 
                'message': 'Payment request sent to your phone. Please enter your PIN.'
            })
        else:
            return render(request, 'payments/pay_subscription.html', {'chama': chama, 'amount': amount, 'error': response.get('ResponseDescription', 'Payment Failed')})

    return render(request, 'payments/pay_subscription.html', {'chama': chama, 'amount': amount})

@csrf_exempt
@require_POST
def mpesa_callback(request):
    print("--- M-PESA CALLBACK RECEIVED ---")
    try:
        data = json.loads(request.body)
        # print(f"Payload: {data}") # Uncomment to see full data
    except json.JSONDecodeError:
        print("Error: Invalid JSON received")
        return JsonResponse({'status': 'error'}, status=400)

    stk_callback = data.get('Body', {}).get('stkCallback', {})
    
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc')
    
    print(f"Processing ID: {checkout_request_id} | Code: {result_code} | Desc: {result_desc}")
    
    try:
        transaction = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        if result_code == 0:
            transaction.status = 'SUCCESS'
            transaction.description = "Payment Successful"
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            for item in items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    transaction.receipt_number = item.get('Value')
                elif item.get('Name') == 'PhoneNumber':
                    transaction.phone_number = str(item.get('Value'))
            
            # --- HANDLE SUBSCRIPTION RENEWAL ---
            if transaction.transaction_type == 'SUBSCRIPTION' and transaction.chama:
                chama = transaction.chama
                # Extend expiry by 30 days from now (or from current expiry if valid)
                if chama.subscription_expiry and chama.subscription_expiry > timezone.now():
                    chama.subscription_expiry += timedelta(days=30)
                else:
                    chama.subscription_expiry = timezone.now() + timedelta(days=30)
                chama.subscription_status = 'ACTIVE'
                chama.save()

            # --- AUTO-CLEAR PENALTIES ---
            # If payment is successful, check if we can clear penalties
            elif transaction.transaction_type == 'CONTRIBUTION' and transaction.chama and transaction.user:
                # Update Chama Total Balance
                Chama.objects.filter(id=transaction.chama.id).update(
                    total_balance=F('total_balance') + transaction.amount
                )
                
                unpaid_penalties = Penalty.objects.filter(user=transaction.user, chama=transaction.chama, is_paid=False)
                for penalty in unpaid_penalties:
                    # Simple logic: If they paid enough, assume they cleared the penalty
                    penalty.is_paid = True
                    penalty.paid_at = timezone.now()
                    penalty.save()
        else:
            transaction.status = 'FAILED'
            transaction.description = result_desc # Save the failure reason (e.g., Cancelled by user)
        transaction.save()
        print(f"Transaction updated to: {transaction.status}")
    except MpesaTransaction.DoesNotExist:
        print("Error: Transaction not found for this CheckoutRequestID")
    
    return JsonResponse({'status': 'ok'})

def home_view(request):
    """Temporary home view for payments app"""
    return HttpResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payments - ChamaPro</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>Payments Module</h1>
                <p>This page will show payment features. Coming soon!</p>
                <a href="/" class="btn btn-primary">Back to Home</a>
            </div>
        </body>
        </html>
    """)

@login_required
def contributions_view(request):
    """Contributions page"""
    contributions = MpesaTransaction.objects.filter(
        user=request.user,
        transaction_type='CONTRIBUTION'
    ).order_by('-transaction_date')
    
    total_contribution = sum(t.amount for t in contributions if t.status == 'SUCCESS')

    context = {
        'contributions': contributions,
        'total_contribution': total_contribution,
        'title': 'My Contributions'
    }
    return render(request, 'payments/contributions.html', context)

@login_required
def chama_contributions_view(request, chama_id):
    """View to show total contributions for all members in a specific Chama"""
    chama = get_object_or_404(Chama, id=chama_id)
    
    # Group by user and sum their successful contributions
    member_contributions = MpesaTransaction.objects.filter(
        chama=chama,
        transaction_type='CONTRIBUTION',
        status='SUCCESS'
    ).values(
        'user__username', 'user__first_name', 'user__last_name', 'user__email'
    ).annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    return render(request, 'payments/chama_contributions.html', {
        'chama': chama,
        'member_contributions': member_contributions
    })

def loans_view(request):
    """Loans page"""
    return HttpResponse("Loans page - Coming soon")

def transactions_view(request):
    """Transactions page"""
    return HttpResponse("Transactions page - Coming soon")

# def test_callback(request):
#     """Test endpoint for debugging"""
#     if request.method == 'GET':
#         return JsonResponse({
#             "status": "success",
#             "message": "Test endpoint is working!",
#             "method": "GET"
#         })
#     elif request.method == 'POST':
#         return JsonResponse({
#             "status": "success", 
#             "message": "Test POST endpoint is working!",
#             "method": "POST"
#         })
#     else:
#         return JsonResponse({
#             "status": "error",
#             "message": "Method not allowed"
#         }, status=405)