# chama/forms.py
from django import forms
from .models import Chama
from .models import Investment

class ChamaForm(forms.ModelForm):
    class Meta:
        model = Chama
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Chama Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['name', 'amount', 'date_invested', 'expected_return_date', 
                  'expected_return_amount', 'status', 'description']
        widgets = {
            'date_invested': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_return_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'expected_return_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
