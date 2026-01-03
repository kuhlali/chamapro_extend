from django import forms
from .models import Loan

class LoanRequestForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['amount', 'duration_months']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Amount (KSh)'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration (Months)'}),
        }
        labels = {
            'duration_months': 'Repayment Period (Months)'
        }
