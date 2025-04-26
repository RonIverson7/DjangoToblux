from django.contrib import admin
from .models import Product

# Register the Product model to make it available in the admin interface
admin.site.register(Product)
