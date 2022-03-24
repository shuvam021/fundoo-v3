from django import forms

from api.models import User


class AuthForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'password')
        widgets = {
            'email': forms.EmailInput(attrs={"placeholder": "Email", "class": "form-control"}),
            'password': forms.PasswordInput(attrs={"placeholder": "Password", "class": "form-control"})
        }
        labels = {'email': '', 'password': ''}
