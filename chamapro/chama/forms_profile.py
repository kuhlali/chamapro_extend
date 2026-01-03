from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class EditProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=15, 
        label='Phone Number', 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Phone Number (e.g., 0712345678)', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate phone number if it exists on the user instance
        if self.instance and hasattr(self.instance, 'phone_number'):
            self.fields['phone_number'].initial = self.instance.phone_number
        
        # Make email read-only as changing it affects login
        if 'email' in self.fields:
            self.fields['email'].disabled = True
            self.fields['email'].help_text = "Email cannot be changed."

    def clean_phone_number(self):
        """Ensure phone number is in 254 format for M-Pesa"""
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            return ""
            
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        if phone.startswith('07') or phone.startswith('01'):
            phone = '254' + phone[1:]
        elif phone.startswith('254') and len(phone) == 12:
            pass
        else:
            raise forms.ValidationError("Please enter a valid Safaricom number (e.g., 0712... or 2547...).")

        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        if hasattr(user, 'phone_number'):
            user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user