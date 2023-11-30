from decimal import Decimal
import re
import time
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from . models import UserProfile
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
import random
from django.core.mail import send_mail
from products.models import *
from checkout.models import Address, Order, OrderItems, Wallet
from userauth.decorator import login_required
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse

# Create your views here.


def log_in(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            users = User.objects.get(username=email)
        except User.DoesNotExist:
            messages.error(request, "User Not found!")
            return redirect('login_page')
        try:
            user = UserProfile.objects.get(user = users)
            if user.is_verified is False:
                raise user.DoesNotExist

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
        
        messages.error(request, 'Invalid credentials')
        return redirect('login_page')

    return render(request, 'accounts/login.html')


def is_valid_name(name):

    name = name.strip()

    if not name:
        return False

    if not any(char.isalpha() for char in name):
        return False

    if not re.match(r'^[A-Z][a-z]*( [A-Z][a-z]*)*$', name):
        return False

    return True


def is_valid_email(email):

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    match = re.match(email_pattern, email)

    return bool(match)        


def is_valid_password(password):

    if len(password) < 8:
        return False

    if not re.search(r'[A-Z]', password):
        return False

    if not re.search(r'[a-z]', password):
        return False

    if not re.search(r'\d', password):
        return False

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True


def sign_up(request):
    if request.method == "POST":
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        email = request.POST.get('email')
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('confirm_password')

        if not is_valid_name(fname):
            messages.error(request, f"{fname} is not a valid name format. Name is case sensitive")
            return redirect('signup_page')
        
        if not is_valid_name(lname):
            messages.error(request, f"{lname} is not a valid name format. Name is case sensitive")
            return redirect('signup_page')
        
        if not is_valid_email(email):
            messages.error(request, f"{email} is not a valid email address.")
            return redirect('signup_page')        
        

        if not (fname[0].isupper() and lname[0].isupper()):
            messages.error(request, 'First letters of First Name and Last Name should be capitalized.')
        elif User.objects.filter(username = email).exists():
            messages.error(request, 'Email already exists!')

        elif pass1 != pass2:
            messages.error(request, "Passwords doesn't match!")

        elif not is_valid_password(pass1):
            messages.error(request, "Password should contain atleast 8 characters including atleast one special character, one lowercase letter, one uppercase letter and a number")
            return redirect('signup_page')
        else:
           
            user = User.objects.create_user(username=email, password=pass1, email=email, first_name=fname, last_name=lname)
            request.session['email'] = email
            request.session['password'] = pass1
            otp = random.randint(1000, 9999)
            request.session['otp'] = otp
            print('The OTP is ========================================================', otp)

            subject = "JERSEY CITY OTP AUTHENTICATION"
            message = f"{otp} - OTP"
            from_email = "dinilkrishna594@gmail.com"
            recipient_list = [email]
            expiration_time = 30

            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                request.session['otp_expiration'] = time.time() + expiration_time
            except Exception as e:
                print(f"Error sending email: {e}")
            userprofile = UserProfile.objects.create(user=user)
            Wallet.objects.create(user = userprofile)
            Cart.objects.create(user = userprofile)
            return redirect(f'/userauth/verify_otp/{user.userprofile.uid}')

    return render(request, 'pages/signup.html')


def verify_otp(request, uid):
    if request.user.is_staff:
        logout(request)
    user = UserProfile.objects.get(uid = uid)
    otp_token = str(request.session.get('otp')).strip()
    email = request.session.get('email')

    expiration_time = request.session.get('otp_expiration')
    remaining_time = max(0, expiration_time - time.time())
    print('The OTP in session is ------------------------------------------', otp_token)

    if request.method=="POST":
        otp = request.POST['otp']

        if remaining_time <= 0:
            messages.error(request, 'OTP has expired. Please request a new OTP.')
            return redirect('otp_login')

        if otp_token == otp:
            user.is_verified = True
            user.save()
            messages.success(request, "signup successful!")
            return redirect('login_page')
        else:
            messages.error(request, "Invalid otp")
            redirect(f'/otp/{user.uid}')
    return render(request,'pages/otpverification.html', {'remaining_time': remaining_time})


def otp_login(request):
    if request.user.is_staff:
        logout(request)
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            users = User.objects.get(username=email)
        except User.DoesNotExist:
            messages.error(request, "User Not found!")
            return redirect('otp_login')
        try:
            user = UserProfile.objects.get(user = users)
            if user.is_verified is False:
                raise user.DoesNotExist
        except UserProfile.DoesNotExist:
            messages.warning(request, "User Not Verified !")
            return redirect('otp_login')        
        
        if user.is_blocked:
            messages.warning(request, 'Your account has been blocked.')
            return redirect('otp_login')

        otp = random.randint(1000, 9999)
        request.session['email'] = email
        request.session['otp'] = otp
        print('The OTP in session is  ========================================================', otp)
        subject = "JERSEY CITY OTP AUTHENTICATION"
        message = f"{otp} - OTP"
        from_email = "dinilkrishna594@gmail.com"
        recipient_list = [email]
        expiration_time = 30  
        try:
            
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            request.session['otp_expiration'] = time.time() + expiration_time   
        except Exception as e:
            print(f"Error sending email: {e}")
        return redirect('otp_login_verify')
        

    return render (request, 'pages/otplogin.html')

def otp_login_verify(request):
    if request.user.is_staff:
        logout(request)
    real_otp = str(request.session.get('otp')).strip()
    print('The OTP in session is  ========================================================', real_otp)
    email = request.session.get('email')
    otp_timestamp = request.session.get('otp_timestamp')
    expiration_time = request.session.get('otp_expiration')
    
    remaining_time = max(0, expiration_time - time.time())

    if request.method == 'POST':
        otp = request.POST.get('otp')

        if remaining_time <= 0:
            messages.error(request, 'OTP has expired. Please request a new OTP.')
            return redirect('otp_login')
        
        
        if otp == real_otp:
            user = User.objects.get(username=email)
            user_profile = UserProfile.objects.get(user = user)
            try:
                authenticated_user = authenticate(request, user = user_profile)
            except Exception as e:
                return HttpResponse(e)

            if user is not None:
                login(request, user)
                return redirect('home_page')  
            else:
                messages.error(request, 'Invalid Credentials')  
        else:
            messages.error(request, 'Invalid OTP')
            
    return render(request, 'pages/otploginverify.html', {'remaining_time': remaining_time})


def resend_otp(request):

    email = request.session.get('email')
    otp = random.randint(1000, 9999)
    request.session['email'] = email
    request.session['otp'] = otp
    print('The OTP is ========================================================', otp)
    subject = "JERSEY CITY OTP AUTHENTICATION"
    message = f"{otp} - OTP"
    from_email = "dinilkrishna594@gmail.com"
    recipient_list = [email]
    expiration_time = 30  
    try:
        
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        request.session['otp_expiration'] = time.time() + expiration_time   
    except Exception as e:
        print(f"Error sending email: {e}")

    return redirect(request.META.get("HTTP_REFERER"))



def log_out(request):
    if request.user.is_authenticated:
        logout(request)
        request.session.flush()
    return redirect('landing_page')


@login_required
def user_profile(request, uid):
    if request.user.is_authenticated: 
        context = {}  
        profile = UserProfile.objects.get(uid = uid)
        try:
            user_cart = Cart.objects.get(user_id = uid)
            cart_items = CartItems.objects.filter(cart = user_cart)
            number_in_cart = 0
            for item in cart_items:
                number_in_cart += 1
            context['number_in_cart'] = number_in_cart
        except:
            pass
        addresses = Address.objects.filter(user = profile.user)
        orders = Order.objects.filter(user = profile.user).order_by('-created_at')
        context['profile'] = profile 
        context['addresses'] = addresses
        context['orders'] = orders
        return render(request, 'userside/user_profile.html', context)
    
    return redirect('login_page')

@login_required
def change_profile_image(request, uid):
    context = {}  
    profile = UserProfile.objects.get(uid=uid)
    user_cart = Cart.objects.get(user_id = uid)
    cart_items = CartItems.objects.filter(cart = user_cart)
    number_in_cart = 0
    for item in cart_items:
        number_in_cart += 1
    
    try:
        if request.method == 'POST':
            profile_image = request.FILES.get('profile_image') if 'profile_image' in request.FILES else None

            # Ensure the image is not None before attempting to save
            if profile_image:
                # Add a timestamp to the image filename to make it unique
                filename = f'profile_image_{timezone.now().timestamp()}.jpg'
                profile.profile_image.save(filename, profile_image, save=True)
                
                return JsonResponse({
                    'status': 'success',
                    'uid': uid,
                })
    except Exception as e:
        return HttpResponse(e)

    context['profile'] = profile 
    context['number_in_cart']
    return render(request, 'userside/changeprofileimage.html', context)


def edit_profile(request, uid):

    if request.method == 'POST':
        user_profile = get_object_or_404(UserProfile, uid=uid)
        user_profile.user.first_name = request.POST['first_name']
        user_profile.user.last_name = request.POST['last_name']

        if not is_valid_name(user_profile.user.first_name):
            messages.error(request, f"{user_profile.user.first_name} is not a valid name format. Name should be a single word, with uppercase starting letter and the rest lowercase")
            return redirect(request.META.get("HTTP_REFERER"))
            # return redirect(reverse('user_profile', kwargs={'uid': uid}))
        if not is_valid_name(user_profile.user.last_name):
            messages.error(request, f"{user_profile.user.last_name} is not a valid name format. Name should be a single word, with uppercase starting letter and the rest lowercase")
            return redirect(request.META.get("HTTP_REFERER"))
        user_profile.user.save()

        return redirect(request.META.get("HTTP_REFERER"))
    return render (request, 'userauth/userprofile.html')


@login_required
def change_password(request, uid):
    id = uid
    context = {}
    user_profile = get_object_or_404(UserProfile, uid=uid)
    user_cart = Cart.objects.get(user_id = uid)
    cart_items = CartItems.objects.filter(cart = user_cart)
    number_in_cart = 0
    for item in cart_items:
        number_in_cart += 1
    context['number_in_cart'] = number_in_cart
    if request.method == 'POST':
        current_password = request.POST['current_password']
        pass1 = request.POST['password']
        pass2 = request.POST['cpassword']

        user = authenticate(request, username=user_profile.user.username, password=current_password)
        if user is None:
            messages.error(request, 'Current password is incorrect')
            return redirect(request.META.get("HTTP_REFERER"))

        if pass1 != pass2:
            messages.error(request, 'Both passwords does not match')
            return redirect(request.META.get("HTTP_REFERER"))
        
        elif not is_valid_password(pass1):
            messages.error(request, "Password should contain atleast 8 characters including atleast one special character, one lowercase letter, one uppercase letter and a number")
            return redirect(request.META.get("HTTP_REFERER"))
        
        user_profile.user.set_password(pass1)
        user_profile.user.save()
        return redirect(reverse('user_profile', kwargs={'uid': id}))

    return render(request, 'userside/changepassword.html', context)        


def is_valid_phone_number(phone_number):
    
    phone_number = re.sub(r'\D', '', phone_number)
    
    if not re.match(r'^\d{10}$', phone_number):
        return False
    
    return True

def is_valid_address(address):
   
    address = address.strip()

    if not address:
        return False
    
    if not re.match(r'^[^\n\r\t\v\f]*$', address):
        return False

    return True


def is_valid_city(city):

    city = city.strip()

    if not city:
        return False

    if not re.match(r'^[a-zA-Z\s]*$', city):
        return False

    return True


def is_valid_district(district):

    district = district.strip()

    if not district:
        return False

    if not re.match(r'^[a-zA-Z\s]*$', district):
        return False

    return True


def is_valid_state(state):

    state = state.strip()

    if not state:
        return False

    if not re.match(r'^[a-zA-Z\s]*$', state):
        return False

    return True

def is_valid_pincode(pincode):

    pincode = re.sub(r'\D', '', pincode)

    if not re.match(r'^\d{6}$', pincode):
        return False

    return True


def add_address(request):
    if request.method == "POST":
        user = request.user
        phone_number = request.POST.get('phone')
        if not is_valid_phone_number(phone_number):
            messages.error(request, "Not a valid phone number")
            return redirect(request.META.get("HTTP_REFERER"))
        address = request.POST.get('address')
        if not is_valid_address(address):
            messages.error(request, "Not a valid address")
            return redirect(request.META.get("HTTP_REFERER"))
        city = request.POST.get('city')
        if not is_valid_city(city):
            messages.error(request, "Not a valid city name")
            return redirect(request.META.get("HTTP_REFERER"))
        district = request.POST.get('district')
        if not is_valid_district(district):
            messages.error(request, "Not a valid district name")
            return redirect(request.META.get("HTTP_REFERER"))
        state = request.POST.get('state')
        if not is_valid_state(state):
            messages.error(request, "Not a valid state name")
            return redirect(request.META.get("HTTP_REFERER"))
        pincode = request.POST.get('pincode')
        if not is_valid_pincode(pincode):
            messages.error(request, "Not a valid pincode")
            return redirect(request.META.get("HTTP_REFERER"))

        address = Address(user = user, phone_number = phone_number, address = address, city = city, district = district, state = state, pincode = pincode)
        address.save()

        return redirect(request.META.get("HTTP_REFERER"))
    return render (request, 'userauth/userprofile.html')


@login_required
def edit_address(request, uid):
    context = {}
    address = Address.objects.get(uid = uid)
    id = request.user.userprofile.uid
    user_cart = Cart.objects.get(user_id = id)
    cart_items = CartItems.objects.filter(cart = user_cart)
    number_in_cart = 0
    for item in cart_items:
        number_in_cart += 1
    context['number_in_cart'] = number_in_cart
    if request.method == 'POST':
        address.phone_number = request.POST.get('phone')
        if not is_valid_phone_number(address.phone_number):
            messages.error(request, "Not a valid phone number")
            return redirect(request.META.get("HTTP_REFERER"))
        address.address = request.POST.get('address')
        if not is_valid_address(address.address):
            messages.error(request, "Not a valid address")
            return redirect(request.META.get("HTTP_REFERER"))
        address.city = request.POST.get('city')
        if not is_valid_city(address.city):
            messages.error(request, "Not a valid city name")
            return redirect(request.META.get("HTTP_REFERER"))
        address.district = request.POST.get('district')
        if not is_valid_district(address.district):
            messages.error(request, "Not a valid district name")
            return redirect(request.META.get("HTTP_REFERER"))
        address.state = request.POST.get('state')
        if not is_valid_state(address.state):
            messages.error(request, "Not a valid state name")
            return redirect(request.META.get("HTTP_REFERER"))
        address.pincode = request.POST.get('pincode')
        if not is_valid_pincode(address.pincode):
            messages.error(request, "Not a valid pincode")
            return redirect(request.META.get("HTTP_REFERER"))
        address.save()
        return redirect(reverse('user_profile', kwargs={'uid': id}))
    context['address'] = address
    context['number_in_cart'] = number_in_cart
    return render(request, 'userside/editaddress.html', context)


@login_required
def delete_address(request, uid):
    address = get_object_or_404(Address, uid=uid)

    if request.user == address.user:
        address.delete()

    else:
        pass

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def cart(request):
    uid = request.user.userprofile.uid
    print(uid)
    context = {}
    
    try:
        profile = UserProfile.objects.get(uid = uid)
        cart, created = Cart.objects.get_or_create(user=profile)
        cart_items = CartItems.objects.filter(cart=cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
        out_of_stock = any(
            item.quantity > Product_Variant.objects.get(product=item.product, size=item.size).stock
            for item in cart_items
        )
        grand_total = 0
        for cart_item in cart_items:
            sub_total = cart_item.calculate_sub_total()
            grand_total += sub_total

        context['out_of_stock'] = out_of_stock
        context['grand_total'] = grand_total
        context['user'] = profile
        context['products'] = cart_items
    except Exception as e:
        messages.error(request, e)
        return redirect('/404error')
    number_in_cart = 0
    for item in cart_items:
        number_in_cart += 1
    context['number_in_cart'] = number_in_cart
    
    return render(request, 'userside/cart.html', context)


def order_details(request, uid):
    context = {}
    user_id = request.user.userprofile.uid
    user_cart = Cart.objects.get(user_id = user_id)
    cart_items = CartItems.objects.filter(cart = user_cart)
    number_in_cart = 0
    for item in cart_items:
        number_in_cart += 1
    context['number_in_cart'] = number_in_cart
    user = UserProfile.objects.get(uid = user_id)
    order = Order.objects.get(uid = uid)
    order_items = OrderItems.objects.filter(order = order)
    # print(order_items)
    print('bllllllllllllllll',order.payment_method)
    context['user'] = user
    context['order'] = order
    context['order_items'] = order_items
    return render(request, 'userside/orderdetails.html', context)


def cancel_order(request, uid):
    order = Order.objects.get(uid = uid)
    order.status = 'Cancelled'
    order.save()
    return redirect(request.META.get("HTTP_REFERER"))



