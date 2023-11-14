
from django.urls import path, include
from . import views

urlpatterns = [
    path('log_in/',views.log_in, name='log_in'),
    path('sign_up/',views.sign_up, name='sign_up'),
    path('log_out/',views.log_out, name='log_out'),
    path('userprofile/', views.user_profile, name='user_profile'),
    path('verify_otp/<uid>/', views.verify_otp, name='verify_otp'),
]
