from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('add_product/', views.manage_products, name='add_product'),
    path('manage_products/', views.manage_products, name='manage_products'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('results/', views.results_view, name='results'),
 
    path('api/products/', views.ProductListCreateAPIView.as_view(), name='api_product_list_create'),
    path('api/products/<int:pk>/', views.ProductRetrieveUpdateDestroyAPIView.as_view(), name='api_product_detail'),
]
