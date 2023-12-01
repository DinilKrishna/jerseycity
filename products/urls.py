
from django.urls import path, include
from . import views

urlpatterns = [
    path('add_to_cart/' , views.add_to_cart, name = "add_to_cart"),
    path('add_quantity/<uid>/',views.add_quantity, name = 'add_quantity'),
    path('decrease_quantity/<uid>/',views.decrease_quantity, name = 'decrease_quantity'),
    path('cart_remove/<uid>/',views.remove_from_cart, name = 'remove_from_cart'),
    path('add_to_wishlist/<uuid:uid>/' , views.add_to_wishlist, name = "add_to_wishlist"),
]
