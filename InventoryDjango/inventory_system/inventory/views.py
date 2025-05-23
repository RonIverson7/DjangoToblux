from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import ProductForm
from .models import Product
from .serializers import ProductSerializer


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                return HttpResponse("Username already taken. Please choose another.")
            else:
                User.objects.create_user(username=username, password=password)
                return redirect('login')
        else:
            return HttpResponse("Passwords do not match.")
    
    return render(request, 'inventory/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Invalid username or password.")
    
    return render(request, 'inventory/login.html')


def home(request):
    products = Product.objects.all()

    context = {
        'total_products': products.count(),
        'products_in_stock': products.filter(quantity__gt=0).count(),  
        'low_stock_products': products.filter(quantity__lte=5), 
        'products': products,  
    }
    return render(request, 'inventory/home.html', context)


def manage_products(request):
    products = Product.objects.all()  

    if request.method == 'POST':
        if 'add_product' in request.POST:
            form = ProductForm(request.POST)
            if form.is_valid():
                price = form.cleaned_data['price']
                if price < 0:
                    return HttpResponse("Price cannot be negative.")
                form.save()
                return redirect('manage_products')
        
        elif 'edit_product' in request.POST:
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id)
            form = ProductForm(request.POST, instance=product)
            if form.is_valid():
                price = form.cleaned_data['price']
                if price < 0:
                    return HttpResponse("Price cannot be negative.")
                form.save()
                return redirect('manage_products')
        
        elif 'delete_product' in request.POST:
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id)
            product.delete()
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
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    return redirect('home')  


def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login') 


def results_view(request):
    products = Product.objects.all() 
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
