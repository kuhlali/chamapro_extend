import requests
import base64
from datetime import datetime
from django.conf import settings

class MpesaGateWay:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.base_url = "https://sandbox.safaricom.co.ke" if settings.DEBUG else "https://api.safaricom.co.ke"

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            # Log error here
            return None

    def stk_push(self, phone_number, amount, account_reference="ChamaPro", transaction_desc="Payment"):
        access_token = self.get_access_token()
        if not access_token:
            return {"ResponseCode": "1", "ResponseDescription": "Failed to get access token"}

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(float(amount)),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": f"{settings.MPESA_CALLBACK_URL}/payments/callback/",
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            return {"ResponseCode": "1", "ResponseDescription": str(e)}

    def disburse_funds(self, phone_number, amount, remarks="Loan Disbursement"):
        """
        B2C API to send money from Chama to Member (e.g., Loans, Dividends)
        Requires MPESA_INITIATOR_NAME and MPESA_SECURITY_CREDENTIAL in settings
        """
        access_token = self.get_access_token()
        if not access_token:
            return {"ResponseCode": "1", "ResponseDescription": "Failed to get access token"}

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "InitiatorName": getattr(settings, 'MPESA_INITIATOR_NAME', 'testapi'),
            "SecurityCredential": getattr(settings, 'MPESA_SECURITY_CREDENTIAL', 'your_encrypted_credential'),
            "CommandID": "BusinessPayment", # or SalaryPayment
            "Amount": int(float(amount)),
            "PartyA": self.shortcode,
            "PartyB": phone_number,
            "Remarks": remarks,
            "QueueTimeOutURL": f"{settings.MPESA_CALLBACK_URL}/payments/b2c/timeout/",
            "ResultURL": f"{settings.MPESA_CALLBACK_URL}/payments/b2c/result/",
            "Occasion": "Loan"
        }
        
        url = f"{self.base_url}/mpesa/b2c/v1/paymentrequest"
        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.json()
        except Exception as e:
            return {"ResponseCode": "1", "ResponseDescription": str(e)}