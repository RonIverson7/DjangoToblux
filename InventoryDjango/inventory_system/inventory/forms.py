from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'quantity', 'price']

def clean_name(self):
        name = self.cleaned_data.get('name')
        # Check if a product with the same name already exists
        if Product.objects.filter(name=name).exists():
            raise forms.ValidationError("A product with this name already exists.")
        return name
