

from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.landing_page, name='landing_page'),
    path('login/',views.login_page, name='login_page'),
    path('signup/',views.signup_page, name='signup_page'),
    path('home/',views.home_page, name='home_page'),
    path('shop/',views.shop_page, name='shop_page'),
    path('about/',views.about_page, name='about_page'),
    path('contact/',views.contact_page, name='contact_page'),
    path('product_details/<uid>',views.product_details, name='product_details'),
    path('get_stock/<product_id>/<size_id>/', views.get_stock, name='get_stock'),
    path('404error/', views.error, name="404"),
]
