from django.db import models
from django.conf import settings

class MpesaTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    chama = models.ForeignKey('chama.Chama', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    transaction_type = models.CharField(max_length=50, default='CONTRIBUTION')
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, default='PENDING')
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    receipt_number = models.CharField(max_length=50, null=True, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} - {self.status}"
