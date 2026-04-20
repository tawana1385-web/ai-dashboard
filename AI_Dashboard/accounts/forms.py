from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400',
            'placeholder': 'Username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-400',
            'placeholder': 'Password',
        })
    )
