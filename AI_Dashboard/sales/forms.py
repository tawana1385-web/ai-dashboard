# sales/forms.py

from django import forms
from .models import MonthlySales, SalesTransaction

class MonthlySalesForm(forms.ModelForm):
    class Meta:
        model = MonthlySales
        fields = ['month', 'revenue', 'transaction_count']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'month', 'class': 'form-control'}),
            'revenue': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transaction_count': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean_revenue(self):
        revenue = self.cleaned_data.get('revenue')
        if revenue and revenue < 0:
            raise forms.ValidationError("مبلغ فروش نمی‌تواند منفی باشد.")
        return revenue
    
    def clean_transaction_count(self):
        count = self.cleaned_data.get('transaction_count')
        if count and count < 0:
            raise forms.ValidationError("تعداد تراکنش نمی‌تواند منفی باشد.")
        return count


class SalesTransactionForm(forms.ModelForm):
    class Meta:
        model = SalesTransaction
        fields = ['transaction_id', 'amount', 'payment_method', 'customer_name', 'customer_phone', 'description']
        widgets = {
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }