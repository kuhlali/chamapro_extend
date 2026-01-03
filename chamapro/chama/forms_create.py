from django import forms
from .models import Chama

class CreateChamaForm(forms.ModelForm):
    """Form for creating a new Chama with enhanced UX and penalty settings"""
    
    monthly_contribution = forms.DecimalField(
        label='Contribution Amount (KSh)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1000', 'step': '100', 'min': '1'})
    )
    
    penalty_amount = forms.DecimalField(
        label='Late Payment Penalty (KSh)',
        initial=0,
        required=False,
        help_text='Amount charged if contribution is late',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 100', 'min': '0'})
    )
    
    penalty_grace_period = forms.IntegerField(
        label='Grace Period (Days)',
        initial=7,
        required=False,
        help_text='Number of days allowed after due date before penalty applies',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7', 'min': '0'})
    )

    class Meta:
        model = Chama
        fields = [
            'name', 
            'description', 
            'contribution_frequency',
            'monthly_contribution', 
            'contribution_day',
            'contribution_weekday',
            'penalty_amount', 
            'penalty_grace_period'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vision 2030 Investment'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your group goals...'}),
            'contribution_frequency': forms.Select(attrs={'class': 'form-select'}),
            'contribution_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Day of Month (1-28)', 'min': '1', 'max': '28'}),
            'contribution_weekday': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('contribution_frequency')
        day_monthly = cleaned_data.get('contribution_day')
        day_weekly = cleaned_data.get('contribution_weekday')
        
        if frequency == 'MONTHLY':
            if not day_monthly:
                self.add_error('contribution_day', 'Please specify the day of the month.')
            elif day_monthly < 1 or day_monthly > 28:
                self.add_error('contribution_day', 'Day must be between 1 and 28.')
            cleaned_data['contribution_weekday'] = None
            
        elif frequency == 'WEEKLY':
            if day_weekly is None:
                self.add_error('contribution_weekday', 'Please specify the day of the week.')
            cleaned_data['contribution_day'] = None
            
        return cleaned_data

    class Media:
        js = ('js/chama_form.js',)