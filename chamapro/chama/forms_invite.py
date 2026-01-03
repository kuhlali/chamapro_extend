from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class InviteMemberForm(forms.Form):
    email = forms.EmailField(
        label="Member's Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("User with this email does not exist on ChamaPro.")
        return email