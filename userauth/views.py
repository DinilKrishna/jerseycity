import re
import time
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from . models import UserProfile
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from django.shortcuts import get_object_or_404
import random
from django.core.mail import send_mail
from products.models import *
from checkout.models import Address, Order, OrderItems, Wallet, WalletHistory
from userauth.decorator import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions

# Create your views here.


def log_in(request):
    try:
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
    except:
        return redirect('/404error/')


def is_valid_name(name):
    try:

        name = name.strip()

        if not name:
            return False

        if not any(char.isalpha() for char in name):
            return False

        if not re.match(r'^[A-Z][a-z]*( [A-Z][a-z]*)*$', name):
            return False

        return True
    except:
        return redirect('/404error/')


def is_valid_email(email):
    try:

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        match = re.match(email_pattern, email)

        return bool(match)        
    except:
        return redirect('/404error/')


def is_valid_password(password):
    try:

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
    except:
        return redirect('/404error/')


def sign_up(request):
    try:
        if request.method == "POST":
            fname = request.POST.get('first_name')
            lname = request.POST.get('last_name')
            email = request.POST.get('email')
            pass1 = request.POST.get('password')
            pass2 = request.POST.get('confirm_password')
            referal = request.POST.get('referal')
            if referal is None:
                referal = "None"

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
                userprofile, created = UserProfile.objects.get_or_create(user=user)
                userprofile.refered = referal
                userprofile.save()

                print(f"UserProfile UID: {userprofile.uid}")  # Add this line for debugging

                # Creating Wallet, Cart, and Wishlist instances after userprofile.save()
                # This ensures that the UserProfile is completely saved to the database
                wallet, wallet_created = Wallet.objects.get_or_create(user=userprofile)

                print(f"Wallet created: {wallet_created}")  # Add this line for debugging

                cart, cart_created = Cart.objects.get_or_create(user=userprofile)
                wishlist, wishlist_created = Wishlist.objects.get_or_create(user=userprofile)

                request.session['email'] = email
                request.session['password'] = pass1
                otp = random.randint(1000, 9999)
                request.session['otp'] = otp
                print('The OTP is ========================================================', otp)

                subject = "JERSEY CITY OTP AUTHENTICATION"
                message = f"{otp} - OTP"
                from_email = "dinilkrishna594@gmail.com"
                recipient_list = [email]
                expiration_time = 60

                try:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                    request.session['otp_expiration'] = time.time() + expiration_time
                except Exception as e:
                    print(f"Error sending email: {e}")

                return redirect(f'/userauth/verify_otp/{user.userprofile.uid}')

        return render(request, 'pages/signup.html')
    except:
        return redirect('/404error/')


def google_signup(request):
    try:
        user = request.user
        # Ensure that the UserProfile object is created
        userprofile, created = UserProfile.objects.get_or_create(user=user)
        
        if created:
            # If the UserProfile was just created, you might want to set additional fields
            userprofile.generate_reference_code()
            userprofile.is_verified = True
            userprofile.save()

            # Create Wallet, Cart, and Wishlist instances
            Wallet.objects.get_or_create(user=userprofile)
            Cart.objects.get_or_create(user=userprofile)
            Wishlist.objects.get_or_create(user=userprofile)

        return redirect('home_page')
    except:
        return redirect('/404error/')


def verify_otp(request, uid):
    try:
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
                refered_user = UserProfile.objects.filter(referance_code = user.refered)
                if refered_user.exists():
                    r_user = UserProfile.objects.get(referance_code = user.refered)
                    user_wallet = Wallet.objects.get(user = user)
                    user_wallet.amount += 50
                    user_wallet.save()
                    refered_wallet= Wallet.objects.get(user = r_user)
                    
                    refered_wallet.amount += 100
                    refered_wallet.save()
                messages.success(request, "Signup successful!")
                return redirect('login_page')
            else:
                messages.error(request, "Invalid otp")
                redirect(f'/otp/{user.uid}')
        return render(request,'pages/otpverification.html', {'remaining_time': remaining_time})
    except:
        return redirect('/404error/')


def forgot_password(request):
    try:
        if request.user.is_staff:
            logout(request)
        if request.method == 'POST':
            email = request.POST.get('email')
            try:
                users = User.objects.get(username=email)
            except User.DoesNotExist:
                messages.error(request, "User Not found!")
                return redirect('forgot_password')
            try:
                user = UserProfile.objects.get(user = users)
                if user.is_verified is False:
                    raise user.DoesNotExist
            except UserProfile.DoesNotExist:
                messages.warning(request, "User Not Verified !")
                return redirect('forgot_password')      
            
            if user.is_blocked:
                messages.warning(request, 'Your account has been blocked.')
                return redirect('forgot_password')

            otp = random.randint(1000, 9999)
            request.session['email'] = email
            request.session['otp'] = otp
            print('The OTP in session is  ========================================================', otp)
            subject = "JERSEY CITY OTP AUTHENTICATION"
            message = f"{otp} - OTP"
            from_email = "dinilkrishna594@gmail.com"
            recipient_list = [email]
            expiration_time = 60
            try:
                
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                request.session['otp_expiration'] = time.time() + expiration_time   

            except Exception as e:
                print(f"Error sending email: {e}")
            return redirect('forgot_pass_otp')
        
        return render(request, 'pages/forgotpass.html')
    except:
        return redirect('/404error/')


def forgot_pass_otp(request):
    try:
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
                uid = user.userprofile.uid
                if user is not None:
                    return redirect(f"/userauth/forgot_pass_change/{uid}/")
                else:
                    messages.error(request, 'Invalid Credentials')  
            else:
                messages.error(request, 'Invalid OTP')

        return render(request, 'pages/forgotpassotp.html', {'remaining_time': remaining_time})
    except:
        return redirect('/404error/')


def forgot_pass_change(request, uid):
    try:
        user_profile = UserProfile.objects.get(uid = uid)
        print(user_profile)
        if request.method == 'POST':
            pass1 = request.POST['password']
            pass2 = request.POST['cpassword']

            if pass1 != pass2:
                messages.error(request, 'Both passwords does not match')
                return redirect(request.META.get("HTTP_REFERER"))
            
            elif not is_valid_password(pass1):
                messages.error(request, "Password should contain atleast 8 characters including atleast one special character, one lowercase letter, one uppercase letter and a number")
                return redirect(request.META.get("HTTP_REFERER"))
            user_profile.user.set_password(pass1)
            user_profile.user.save()
            return redirect('login_page')
        return render (request, 'pages/forgotpasschange.html')
    except:
        return redirect('/404error/')




def otp_login(request):
    try:
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
            expiration_time = 60
            try:
                
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                request.session['otp_expiration'] = time.time() + expiration_time   

            except Exception as e:
                print(f"Error sending email: {e}")
            return redirect('otp_login_verify')
            
        return render (request, 'pages/otplogin.html')
    except:
        return redirect('/404error/')

def otp_login_verify(request):
    try:
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
                print('email', email)
                user = User.objects.get(username=email)
                print(user, '001')

                if user is not None:
                    login(request, user, backend ='django.contrib.auth.backends.ModelBackend')
                    print("reached here")
                    return redirect('home_page')  
                else:
                    messages.error(request, 'Invalid Credentials')  
            else:
                messages.error(request, 'Invalid OTP')

        return render(request, 'pages/otploginverify.html', {'remaining_time': remaining_time})
    except:
        return redirect('/404error/')


def resend_otp(request):
    try:
        email = request.session.get('email')
        otp = random.randint(1000, 9999)
        request.session['email'] = email
        request.session['otp'] = otp
        print('The OTP is ========================================================', otp)
        subject = "JERSEY CITY OTP AUTHENTICATION"
        message = f"{otp} - OTP"
        from_email = "dinilkrishna594@gmail.com"
        recipient_list = [email]
        expiration_time = 60  
        try:
            
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            request.session['otp_expiration'] = time.time() + expiration_time   
        except Exception as e:
            print(f"Error sending email: {e}")

        return redirect(request.META.get("HTTP_REFERER"))
    except:
        return redirect('/404error/')


def log_out(request):
    try:
        if request.user.is_authenticated:
            logout(request)
            request.session.flush()
        return redirect('landing_page')
    except:
        return redirect('/404error/')


@login_required
def user_profile(request, uid):
    try:
        if request.user.is_authenticated: 
            context = {}  
            profile = UserProfile.objects.get(uid = uid)
            wallet = Wallet.objects.get(user = profile)
            wallet_history = WalletHistory.objects.filter(wallet = wallet)
            
            user_cart = Cart.objects.get(user_id = uid)
            cart_items = CartItems.objects.filter(cart=user_cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
            number_in_cart = 0
            for item in cart_items:
                number_in_cart += 1
            context['number_in_cart'] = number_in_cart
            
            wishlist = Wishlist.objects.get(user = profile)
            wishlist_items = WishlistItems.objects.filter(wishlist = wishlist)       
            wishlist_items
            number_in_wishlist = 0
            for item in wishlist_items:
                number_in_wishlist += 1
            context['number_in_wishlist'] = number_in_wishlist
            addresses = Address.objects.filter(user = profile.user)
            orders = Order.objects.filter(user = profile.user).order_by('-created_at')

            context['profile'] = profile 
            context['wallet'] = wallet
            context['wallet_history'] = wallet_history
            context['addresses'] = addresses
            context['orders'] = orders
            return render(request, 'userside/user_profile.html', context)
        
        return redirect('login_page')
    except:
        return redirect('/404error/')


def validate_image(image):
    try:
        """
        Validate the uploaded image.
        """
        max_width = 1000
        max_height = 1000

        try:
            width, height = get_image_dimensions(image)

            if width > max_width or height > max_height:
                raise ValidationError("Image dimensions should not exceed {}x{} pixels.".format(max_width, max_height))

        except AttributeError:
            raise ValidationError("Invalid image file.")

        return image
    except:
        return redirect('/404error/')


@login_required
def change_profile_image(request, uid):
    try:
        context = {}  
        profile = UserProfile.objects.get(uid=uid)
        user_cart = Cart.objects.get(user_id=uid)
        cart_items = CartItems.objects.filter(cart=user_cart, product__is_selling=True, product__category__is_listed=True).order_by("-created_at")
        number_in_cart = cart_items.count()
        wishlist = Wishlist.objects.get(user=profile)
        wishlist_items = WishlistItems.objects.filter(wishlist=wishlist)
        number_in_wishlist = wishlist_items.count()
        context['number_in_wishlist'] = number_in_wishlist

        try:
            if request.method == 'POST':
                profile_image = request.FILES.get('profile_image') if 'profile_image' in request.FILES else None

                # Ensure the image is not None before attempting to save
                if profile_image:
                    # Validate the image
                    try:
                        # Open the image file
                        img = Image.open(profile_image.file)
                        img.verify()  # This will raise an exception if the image is not valid
                    except Exception as e:
                        messages.error(request, 'Invalid image file. Please upload a valid image.')
                        return redirect(request.META.get("HTTP_REFERER"))

                    # Add a timestamp to the image filename to make it unique
                    filename = f'profile_image_{timezone.now().timestamp()}.jpg'
                    profile.profile_image.save(filename, profile_image, save=True)

                    return JsonResponse({
                        'status': 'success',
                        'uid': uid,
                    })
        except ValidationError as e:
            messages.error(request, 'Invalid File Format')
            return redirect(request.META.get('HTTP_REFERER'))
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

        context['profile'] = profile
        context['number_in_cart'] = number_in_cart
        return render(request, 'userside/changeprofileimage.html', context)
    except:
        return redirect('/404error/')


def edit_profile(request, uid):
    try:
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
    except:
        return redirect('/404error/')


@login_required
def change_password(request, uid):
    try:
        id = uid
        context = {}
        user_profile = get_object_or_404(UserProfile, uid=uid)
        user_cart = Cart.objects.get(user_id = uid)
        cart_items = CartItems.objects.filter(cart=user_cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart
        wishlist = Wishlist.objects.get(user = user_profile)
        wishlist_items = WishlistItems.objects.filter(wishlist = wishlist)       
        wishlist_items
        number_in_wishlist = 0
        for item in wishlist_items:
            number_in_wishlist += 1
        context['number_in_wishlist'] = number_in_wishlist
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
            # Update the session with the new user credentials
            login(request, user_profile.user, backend= 'django.contrib.auth.backends.ModelBackend')

            # Update the session's password hash to match the new password
            update_session_auth_hash(request, user_profile.user)
            return redirect(reverse('user_profile', kwargs={'uid': id}))

        return render(request, 'userside/changepassword.html', context)        
    except:
        return redirect('/404error/')


def is_valid_phone_number(phone_number):
    try:
        
        phone_number = re.sub(r'\D', '', phone_number)
        
        if not re.match(r'^\d{10}$', phone_number):
            return False
        
        return True
    except:
        return redirect('/404error/')

def is_valid_address(address):
    try:
        address = address.strip()

        if not address:
            return False
        
        if not re.match(r'^[^\n\r\t\v\f]*$', address):
            return False

        return True
    except:
        return redirect('/404error/')


def is_valid_city(city):
    try:
        city = city.strip()

        if not city:
            return False

        if not re.match(r'^[a-zA-Z\s]*$', city):
            return False

        return True 
    except:
        return redirect('/404error/')
    

def is_valid_district(district):
    try:
        district = district.strip()

        if not district:
            return False

        if not re.match(r'^[a-zA-Z\s]*$', district):
            return False

        return True
    except:
        return redirect('/404error/')


def is_valid_state(state):
    try:
        state = state.strip()

        if not state:
            return False

        if not re.match(r'^[a-zA-Z\s]*$', state):
            return False

        return True
    except:
        return redirect('/404error/')

def is_valid_pincode(pincode):
    try:
        pincode = re.sub(r'\D', '', pincode)

        if not re.match(r'^\d{6}$', pincode):
            return False

        return True
    except:
        return redirect('/404error/')


def add_address(request):
    try:
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
    except:
        return redirect('/404error/')


@login_required
def edit_address(request, uid):
    try:
        context = {}
        address = Address.objects.get(uid = uid)
        id = request.user.userprofile.uid
        profile = UserProfile.objects.get(uid = id)
        user_cart = Cart.objects.get(user_id = id)
        cart_items = CartItems.objects.filter(cart=user_cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart
        wishlist = Wishlist.objects.get(user = profile)
        wishlist_items = WishlistItems.objects.filter(wishlist = wishlist)       
        wishlist_items
        number_in_wishlist = 0
        for item in wishlist_items:
            number_in_wishlist += 1
        context['number_in_wishlist'] = number_in_wishlist
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
    except:
        return redirect('/404error/')


@login_required
def delete_address(request, uid):
    try:
        address = get_object_or_404(Address, uid=uid)

        if request.user == address.user:
            address.delete()

        else:
            pass

        return redirect(request.META.get("HTTP_REFERER"))
    except:
        return redirect('/404error/')


@login_required
def wishlist(request):
    try:
        uid = request.user.userprofile.uid
        context = {}
        try:
            profile = UserProfile.objects.get(uid = uid)
            wishlist, created = Wishlist.objects.get_or_create(user = profile)
            wishlist_items = WishlistItems.objects.filter(wishlist = wishlist, product__is_selling=True)         
        
            context['user'] = profile
            context['products'] = wishlist_items
        except Exception as e:
            messages.error(request, e)
            return redirect('/404error')
        number_in_wishlist = 0
        for item in wishlist_items:
            number_in_wishlist += 1
        context['number_in_wishlist'] = number_in_wishlist
        cart = Cart.objects.get(user=profile)
        cart_items = CartItems.objects.filter(cart=cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart

        
        return render(request, 'userside/wishlist.html', context)
    except:
        return redirect('/404error/')

@login_required
def cart(request):
    try:
        uid = request.user.userprofile.uid
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
        wishlist = Wishlist.objects.get(user = profile)
        wishlist_items = WishlistItems.objects.filter(wishlist = wishlist)       
        wishlist_items
        number_in_wishlist = 0
        for item in wishlist_items:
            number_in_wishlist += 1
        context['number_in_wishlist'] = number_in_wishlist
        
        return render(request, 'userside/cart.html', context)
    except:
        return redirect('/404error/')


def order_details(request, uid):
    try:
        context = {}
        user_id = request.user.userprofile.uid
        profile = UserProfile.objects.get(uid = user_id)
        user_cart = Cart.objects.get(user_id = user_id)
        cart_items = CartItems.objects.filter(cart=user_cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart
        wishlist = Wishlist.objects.get(user = profile)
        wishlist_items = WishlistItems.objects.filter(wishlist = wishlist)       
        wishlist_items
        number_in_wishlist = 0
        for item in wishlist_items:
            number_in_wishlist += 1
        context['number_in_wishlist'] = number_in_wishlist
        user = UserProfile.objects.get(uid = user_id)
        order = Order.objects.get(uid = uid)
        try:
            returned = Return.objects.get(order = order)
        except:
            returned = None
        order_items = OrderItems.objects.filter(order = order)
        discount = order.bill_amount - order.amount_to_pay
        context['discount'] = discount
        context['returned'] = returned
        context['user'] = user
        context['order'] = order
        context['order_items'] = order_items
        return render(request, 'userside/orderdetails.html', context)
    except:
        return redirect('/404error/')


def invoice(request, uid):
    try:
        context = {}
        order = Order.objects.get(uid = uid)
        order_items = OrderItems.objects.filter(order = order)
        discount = order.bill_amount - order.amount_to_pay
        context['discount'] = discount

        context['order'] = order
        context['order_items'] = order_items
        return render (request, 'userside/invoice/invoice.html', context)
    except:
        return redirect('/404error/')


def cancel_order(request, uid):
    try:
        order = Order.objects.get(uid = uid)
        order.status = 'Cancelled'
        print(order.payment_method)
        if order.payment_method.method == 'razorpay' or order.payment_method.method == 'wallet':
            profile = UserProfile.objects.get(uid = request.user.userprofile.uid)
            wallet = Wallet.objects.get(user = profile)
            wallet.amount += order.amount_to_pay
            wallet.save()
            order_items = OrderItems.objects.filter(order = order)
        order_items = OrderItems.objects.filter(order = order)
        for item in order_items:
            product = Product_Variant.objects.get(product = item.product, size = item.size)
            product.stock += item.quantity
            product.sold -= item.quantity
            product.save()
        order.save()
        return redirect(request.META.get("HTTP_REFERER"))
    except:
        return redirect('/404error/')
    
