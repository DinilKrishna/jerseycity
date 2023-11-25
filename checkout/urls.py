from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.checkout, name="checkout"),
    path('add_new_address/', views.add_new_address, name="add_new_address"),
    path('success_page/<uid>/', views.success_page, name="success_page"),    
]
