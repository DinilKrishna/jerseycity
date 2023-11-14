from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from . models import UserProfile
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404

# Create your views here.


def log_in(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            users = User.objects.get(username=email)
            # user = UserProfile.objects.get(user = users)
        except User.DoesNotExist:
            messages.warning(request, "User Not found!")
            return redirect('login_page')
        try:
            # users = User.objects.get(username=email)
            user = UserProfile.objects.get(user = users)
        except UserProfile.DoesNotExist:
            messages.warning(request, "User Not Verified !")
            return redirect('login_page')
        
        
        if user.is_blocked:
            messages.warning(request, 'Your account has been blocked.')
            return redirect('login_page')

        authenticated_user = authenticate(username=email, password=password)
        
        if authenticated_user is not None and not authenticated_user.is_staff:
            login(request, authenticated_user)
            return redirect('home_page')
        
        messages.warning(request, 'Invalid credentials')
        return redirect('login_page')

    return render(request, 'accounts/login.html')

        

def sign_up(request):
    if request.method == "POST":
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        email = request.POST.get('email')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('confirm_password')

        if not (fname[0].isupper() and lname[0].isupper()):
            messages.error(request, 'First letters of First Name and Last Name should be capitalized.')
        elif User.objects.filter(username = email).exists():
            messages.error(request, 'Email already exists!')
        elif pass1 != pass2:
            messages.error(request, "Passwords doesn't match!")
        elif len(pass1) < 8:
            messages.error(request, 'Password should contain minimum 8 characters!')
        else:
           
            user = User.objects.create_user(username=email, password=pass1, email=email, first_name=fname, last_name=lname)
            user.userprofile.save()
            # request.session['email']=email
            return redirect(f'/userauth/verify_otp/{user.userprofile.uid}')
                
            # return redirect('otp')
    return render(request, 'pages/signup.html')


def verify_otp(request, uid):
    user = UserProfile.objects.get(uid = uid)
    otp_token = user.otp
    if request.method=="POST":
        otp = request.POST['otp']
        if otp_token == otp:
            user.is_verified = True
            user.save()
            messages.success(request, "signup successful!")
            return redirect('login_page')
        else:
            messages.success(request, "Invalid otp")
            redirect(f'/otp/{user.uid}')
    return render(request,'pages/otpverification.html')




def log_out(request):
    if request.user.is_authenticated:
        logout(request)
        request.session.flush()
    return redirect('landing_page')


def user_profile(request):
    if request.user.is_authenticated:    
        return render(request, 'userside/user_profile.html')
    return redirect('login_page')


