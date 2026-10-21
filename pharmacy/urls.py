from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    path('', views.index_redirect, name='index'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    
    path('pharmacist/', views.pharmacist_catalog, name='pharmacist_catalog'),
    path('pharmacist/sell/', views.pharmacist_sell, name='pharmacist_sell'),
    
    path('warehouse/', views.warehouse_dashboard, name='warehouse_dashboard'),
    path('warehouse/add/', views.warehouse_add_product, name='warehouse_add_product'),
    path('warehouse/edit/', views.warehouse_edit_product, name='warehouse_edit_product'),
    path('warehouse/sell/', views.warehouse_sell_product, name='warehouse_sell_product'),
    path('warehouse/return/', views.warehouse_return_product, name='warehouse_return_product'),
    path('warehouse/delete-expired/', views.warehouse_delete_expired, name='warehouse_delete_expired'),
    path('warehouse/delete/<int:pk>/', views.warehouse_delete_product, name='warehouse_delete_product'),
]
