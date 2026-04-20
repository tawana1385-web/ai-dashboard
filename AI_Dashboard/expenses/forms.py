# expenses/forms.py

from django import forms
from .models import Expense, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'category', 'amount', 'date', 'description', 'receipt_image', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: خرید تجهیزات'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'مبلغ به افغانی'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات اختیاری'}),
            'receipt_image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 0:
            raise forms.ValidationError("مبلغ هزینه نمی‌تواند منفی باشد.")
        if amount and amount > 999999999:
            raise forms.ValidationError("مبلغ وارد شده بسیار زیاد است.")
        return amount


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'description', 'parent_category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: دفتری، حمل و نقل، ...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'parent_category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }