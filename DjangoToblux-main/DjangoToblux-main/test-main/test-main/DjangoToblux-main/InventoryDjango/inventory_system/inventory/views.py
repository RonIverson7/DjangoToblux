from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib import messages

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import ProductForm, UserRegistrationForm, ProfileForm
from .models import Product, Profile
from .serializers import ProductSerializer
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated


def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number'),
                address=form.cleaned_data.get('address')
            )
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'inventory/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'inventory/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
         
            token, created = Token.objects.get_or_create(user=user)

            request.session['auth_token'] = token.key
 
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'inventory/login.html')



def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'inventory/profile.html', {
        'form': form,
        'profile': profile
    })



def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')



def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    query = request.GET.get('q', '')
    products = Product.objects.filter(user=request.user)
    
    if query:
        products = products.filter(
            models.Q(name__icontains=query) |
            models.Q(category__icontains=query) |
            models.Q(description__icontains=query)
        )
    
   
    for product in products:
        product.total = product.price * product.quantity
    
   
    total_sum = sum(product.total for product in products)
  
    low_stock_products = products.filter(quantity__lt=10)
    
    return render(request, 'inventory/home.html', {
        'products': products,
        'query': query,
        'total_sum': total_sum,
        'low_stock_products': low_stock_products
    })



def manage_products(request):
    products = Product.objects.filter(user=request.user)

    if request.method == 'POST':
        if 'add_product' in request.POST:
            form = ProductForm(request.POST)
            if form.is_valid():
                product = form.save(commit=False)
                product.user = request.user
                price = form.cleaned_data['price']
                if price < 0:
                    messages.error(request, "Price cannot be negative.")
                    return redirect('manage_products')
                product.save()
                messages.success(request, "Product added successfully!")
                return redirect('manage_products')
        
        elif 'edit_product' in request.POST:
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id, user=request.user)
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                price = form.cleaned_data['price']
                if price < 0:
                    messages.error(request, "Price cannot be negative.")
                    return redirect('manage_products')
                form.save()
                messages.success(request, "Product updated successfully!")
                return redirect('manage_products')
        
        elif 'delete_product' in request.POST:
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id, user=request.user)
            product.delete()
            messages.success(request, "Product deleted successfully!")
            return redirect('manage_products')

    else:
        add_form = ProductForm()  
        edit_form = None  
        return render(request, 'inventory/manage_products.html', {
            'products': products,
            'add_form': add_form,
            'edit_form': edit_form,
        })



def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id, user=request.user)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('home')



def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id, user=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('home')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {'form': form})



def results_view(request):
    products = Product.objects.filter(user=request.user)
    product_details = []

    total_sum = 0 
    
    for product in products:
        total_price = product.price * product.quantity  
        product_details.append({
            'name': product.name,
            'quantity': product.quantity,
            'price': product.price,
            'total_price': total_price,
        })
        total_sum += total_price  

    context = {
        'product_details': product_details,
        'total_sum': total_sum  
    }

    return render(request, 'inventory/results.html', context)


class ProductListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated] 
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductRetrieveUpdateDestroyAPIView(APIView):
 
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if product is None:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if product is None:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if product is None:
            return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
