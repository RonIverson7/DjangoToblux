from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product, Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone_number', 'address']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address']
        
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone_number


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'quantity', 'price']
        exclude = ['user']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if hasattr(self, 'instance') and self.instance.pk:
            if Product.objects.filter(user=self.instance.user, name=name).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("A product with this name already exists in your inventory.")
        else:
            if Product.objects.filter(user=self.instance.user, name=name).exists():
                raise forms.ValidationError("A product with this name already exists in your inventory.")
        return name
