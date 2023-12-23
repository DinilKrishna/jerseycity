
from django.urls import path, include
from . import views

urlpatterns = [
    path('log_in/',views.log_in, name='log_in'),
    path('sign_up/',views.sign_up, name='sign_up'),
    path('log_out/',views.log_out, name='log_out'),

    path('verify_otp/<uid>/', views.verify_otp, name='verify_otp'),
    path('otp_login/',views.otp_login, name = 'otp_login'),
    path('google_signup/',views.google_signup, name = 'google_signup'),
    path('otp_login_verify/',views.otp_login_verify, name = 'otp_login_verify'),
    path('resend_otp/',views.resend_otp, name = 'resend_otp'),

    path('cart/',views.cart, name = 'cart'),
    

    path('userprofile/<uid>/', views.user_profile, name='user_profile'),
    path('add_address/',views.add_address, name = 'add_address'),
    path('edit_address/<uid>/',views.edit_address, name = 'edit_address'),
    path('delete_address/<uid>/',views.delete_address, name = 'delete_address'),
    path('edit_profile/<uid>/',views.edit_profile, name = 'edit_profile'),
    path('change_password/<uid>/',views.change_password, name = 'change_password'),
    path('change_profile_image/<uid>/',views.change_profile_image, name = 'change_profile_image'),
    path('order_details/<uid>/',views.order_details, name = 'order_details'),    
    path('invoice/<uid>/',views.invoice, name = 'invoice'),    
    path('cancel_order/<uid>/',views.cancel_order, name = 'cancel_order'),
    path('wishlist/',views.wishlist, name = 'wishlist'),
]
