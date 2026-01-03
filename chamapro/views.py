import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .utils import MpesaGateWay
from .models import MpesaTransaction

@login_required
def initiate_payment(request):
    if request.method == "POST":
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        
        if not phone or not amount:
            return JsonResponse({'error': 'Phone and Amount are required'}, status=400)

        gateway = MpesaGateWay()
        response = gateway.stk_push(phone, amount, account_reference="Contribution")
        
        if response.get('ResponseCode') == '0':
            MpesaTransaction.objects.create(
                user=request.user,
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

@csrf_exempt
@require_POST
def mpesa_callback(request):
    data = json.loads(request.body)
    stk_callback = data.get('Body', {}).get('stkCallback', {})
    
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    
    try:
        transaction = MpesaTransaction.objects.get(checkout_request_id=checkout_request_id)
        if result_code == 0:
            transaction.status = 'SUCCESS'
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            for item in items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    transaction.receipt_number = item.get('Value')
        else:
            transaction.status = 'FAILED'
        transaction.save()
    except MpesaTransaction.DoesNotExist:
        pass
    
    return JsonResponse({'status': 'ok'})

# def test_callback(request):
#     """Test endpoint that accepts both GET and POST"""
#     if request.method == 'GET':
#         return JsonResponse({"message": "GET request received"})
#     return JsonResponse({"message": "Use POST for real callback"})