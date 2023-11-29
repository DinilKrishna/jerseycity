from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.checkout, name="checkout"),
    path('add_new_address/', views.add_new_address, name="add_new_address"),
    path('success_page/', views.success_page, name="success_page"),    
    path('validate_coupon/', views.validate_coupon, name='validate_coupon'),
    path('create_order/', views.create_order, name="create_order"),    
]
