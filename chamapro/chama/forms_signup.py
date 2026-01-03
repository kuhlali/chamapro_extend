from django import forms
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name', widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, label='Last Name', widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'form-control'}))
    phone_number = forms.CharField(max_length=15, label='Phone Number', widget=forms.TextInput(attrs={'placeholder': 'Phone Number (e.g., 0712345678)', 'class': 'form-control'}))

    def clean_phone_number(self):
        """Ensure phone number is in 254 format for M-Pesa"""
        phone = self.cleaned_data['phone_number']
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        elif phone.startswith('254') and len(phone) == 12:
            pass
        else:
            raise forms.ValidationError("Please enter a valid Safaricom number (e.g., 0712... or 2547...).")

        # Block known non-Safaricom prefixes (Airtel: 073/078, Telkom: 077)
        if phone.startswith(('25473', '25478', '25477')):
            raise forms.ValidationError("Airtel and Telkom numbers are not supported for M-Pesa. Please use a Safaricom number.")
            
        return phone

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Save phone number if the User model has the field (Custom User Model)
        if hasattr(user, 'phone_number'):
            user.phone_number = self.cleaned_data['phone_number']
        user.save()
        return user