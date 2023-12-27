from django.http import JsonResponse
from django.shortcuts import render, redirect
from products.models import *
from userauth.models import UserProfile
from django.contrib.auth.models import User
from .models import *
from django.contrib import messages
from userauth.decorator import login_required
from userauth.views import is_valid_address, is_valid_city, is_valid_district, is_valid_phone_number, is_valid_pincode, is_valid_state
from django.utils import timezone
import razorpay

# Create your views here.


@login_required
def checkout(request):
    try:
        uid = request.user.userprofile.uid
        context = {}
        profile = UserProfile.objects.get(uid=uid)
        current_user_coupons = Coupon.objects.filter(users=profile)

        coupons_not_associated_with_current_user = Coupon.objects.exclude(uid__in=current_user_coupons.values_list('uid', flat=True)).filter(expiry_date__gt=timezone.now())
        context['coupons'] = coupons_not_associated_with_current_user
        cart = Cart.objects.get(user=profile)
        cart_items = CartItems.objects.filter(cart__user=profile,product__is_selling = True,product__category__is_listed = True)
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart
        wishlist = Wishlist.objects.get(user = profile)
        wishlist_items = WishlistItems.objects.filter(wishlist = wishlist)       
        number_in_wishlist = 0
        for item in wishlist_items:
            number_in_wishlist += 1
        context['number_in_wishlist'] = number_in_wishlist
        addresses = Address.objects.filter(unlisted=False, user=request.user)
        if not cart_items:
            messages.warning(request, "Cart is empty!")
            return redirect(f'/userauth/cart/{uid}')
        out_of_stock = False
        grand_total = 0
        for cart_item in cart_items:
            sub_total = cart_item.calculate_sub_total()
            grand_total += sub_total
            variant = Product_Variant.objects.get(product = cart_item.product, size = cart_item.size)
            if cart_item.quantity > variant.stock:
                out_of_stock = True
        discounted_total = grand_total
        if cart.coupon:
            discounted_total = grand_total - (grand_total * cart.coupon.discount_percentage)/100
            discounted_total = round(discounted_total, 2)
        context['discounted_total'] = discounted_total
        context['cart'] = cart
        context['out_of_stock'] = out_of_stock
        context['products'] = cart_items
        context['grand_total'] = grand_total
        context['user'] = profile
        context['addresses'] = addresses
        context['offf'] = grand_total - discounted_total
        if request.method == 'POST':
            if addresses == None:
                messages.error(request, "Enter an address")
                return redirect(request.META.get('HTTP_REFERER'))
            selected_address_id = request.POST.get('selected_address')
            request.session['selected_address_id'] = selected_address_id
            payment_option = request.POST.get('payment_option')
            if payment_option:
                print(payment_option)
            else:
                messages.warning(request, "Please select a payment option.")
            if selected_address_id:
                selected_address = Address.objects.get(uid=selected_address_id)
                print(selected_address.address,' : ', selected_address.pincode)

            else:
                messages.warning(request, "Please select an address.")
                return redirect(request.META.get('HTTP_REFERER'))

            if payment_option == 'wallet':
                # Handle Direct Bank Transfer logic
                
                messages.warning(request, 'You chose ', payment_option)
                print("Selected Payment Option: Direct Bank Transfer")
                return redirect('wallet_payment')
            
            elif payment_option == 'razorpay':
                
                print("Selected Payment Option: RazorPay")
                discounted_total = float(discounted_total)
                request.session['discounted_total'] = discounted_total
                discounted_total = int(discounted_total * 100)
                
                
                client = razorpay.Client(auth=("rzp_test_KSJKvKAn2yU3LA", "1aqi5ebdJfkUFfAiXFOFuALn"))

                DATA = {
                    "amount": int(discounted_total),
                    "currency": "INR",
                    "payment_capture":'1'
                    
                }
                client.order.create(data=DATA)

                return render(request,"checkout/razorpay.html", {"grand_total":discounted_total})
            elif payment_option == 'cash_on_delivery':
                # Handle Cash on Delivery logic
                print("Selected Payment Option: Cash on Delivery")

                payment_method_instance = Payment_Method.objects.get(method='cash_on_delivery')            
                print('instance: ', payment_method_instance)
                for item in cart_items:
                    product_stock = Product_Variant.objects.get(product=item.product, size=item.size)
                    if product_stock.stock < item.quantity:
                        messages.error(request, "Product Out of Stock")
                        return redirect('cart')
                order = Order.objects.create(
                    user=request.user,
                    address=selected_address,
                    phone_number=selected_address.phone_number,
                    city=selected_address.city,
                    district=selected_address.district,
                    state=selected_address.state,
                    pincode=selected_address.pincode,
                    payment_method=payment_method_instance
                )

                print('Order created:', order.city)

                for item in cart_items:
                    sub_total = item.quantity * item.product.selling_price

                    order_item = OrderItems.objects.create(
                        order=order,  
                        product=item.product,
                        quantity=item.quantity,
                        product_price=item.product.selling_price,
                        size=item.size,
                        sub_total=sub_total,
                        discounted_subtotal=sub_total,
                    )

                    
                    product_stock.stock -= item.quantity
                    product_stock.sold += item.quantity
                    product_stock.save()
                    print('Product stock updated')

                order.calculate_bill_amount()
                if cart.coupon:
                    if cart.coupon.unlisted is False:
                        order.amount_to_pay = discounted_total
                        print(discounted_total, 'discounttttt')
                    else:
                        order.amount_to_pay = order.bill_amount
                        print(order.bill_amount, 'billlllllllllllllllll')
                else:
                    order.amount_to_pay = order.bill_amount
                order.status = 'Confirmed'
                order.save()
                print('Order saved again')

                # Clear the user's cart
                cart_items.delete()
                cart.coupon = None
                cart.save()
                print('Cart cleared')

                return redirect(f'/checkout/success_page/')

            else:
                messages.warning(request, 'Please choose a payment option')
            
            return redirect(request.META.get("HTTP_REFERER"))
        
        return render(request, 'checkout/checkout.html', context)
    except:
        return redirect('/404error/')


def wallet_payment(request):
    try:
        context = {}
        uid = request.user.userprofile.uid
        user = UserProfile.objects.get(uid = uid)
        cart_items = CartItems.objects.filter(cart__user=user,product__is_selling = True,product__category__is_listed = True)
        wallet = Wallet.objects.get(user=user)
        out_of_stock = False
        grand_total = 0
        for cart_item in cart_items:
            sub_total = cart_item.calculate_sub_total()
            grand_total += sub_total
            variant = Product_Variant.objects.get(product = cart_item.product, size = cart_item.size)
            if cart_item.quantity > variant.stock:
                out_of_stock = True
        remaining_balance = wallet.amount - grand_total
        if request.method == 'POST':
            if wallet.amount < grand_total:
                messages.error(request, 'Not enough balance in wallet')
                return redirect(request.META.get("HTTP_REFERER"))
            for item in cart_items:
                product_stock = Product_Variant.objects.get(product=item.product, size=item.size)
                if product_stock.stock < item.quantity:
                    messages.error(request, "Product Out of Stock")
                    return redirect('cart')
            wallet.amount = remaining_balance
            wallet.save()
            selected_address_id = request.session.get('selected_address_id')
            request.session.pop('selected_address_id', None)
            selected_address = Address.objects.get(uid=selected_address_id)
            payment_method_instance = Payment_Method.objects.get(method='wallet')
            profile = UserProfile.objects.get(uid=uid)
            print(payment_method_instance)
            cart = Cart.objects.get(user=profile)
            if cart.coupon:
                discounted_total = grand_total - (grand_total * cart.coupon.discount_percentage)/100
                discounted_total = round(discounted_total, 2)
            
            order = Order.objects.create(
                    user=request.user,
                    address=selected_address,
                    phone_number=selected_address.phone_number,
                    city=selected_address.city,
                    district=selected_address.district,
                    state=selected_address.state,
                    pincode=selected_address.pincode,
                    payment_method=payment_method_instance,
                    payed=True
                )
            for item in cart_items:
                sub_total = item.quantity * item.product.selling_price

                order_item = OrderItems.objects.create(
                    order=order,  
                    product=item.product,
                    quantity=item.quantity,
                    product_price=item.product.selling_price,
                    size=item.size,
                    sub_total=sub_total,
                    discounted_subtotal=sub_total,
                )

                product_stock = Product_Variant.objects.get(product=item.product, size=item.size)
                product_stock.stock -= item.quantity
                product_stock.sold += item.quantity
                product_stock.save()

            order.calculate_bill_amount()
            if cart.coupon:
                if cart.coupon.unlisted is False:
                    order.amount_to_pay = discounted_total
                else:
                    order.amount_to_pay = order.bill_amount
            else:
                order.amount_to_pay = order.bill_amount
            order.status = 'Confirmed'
            order.save()
            cart_items.delete()
            cart.coupon = None
            cart.save()
            return redirect(f'/checkout/success_page/')
            
        context['user'] = user
        context['out_of_stock'] = out_of_stock
        context['products'] = cart_items
        context['grand_total'] = grand_total
        context['wallet'] = wallet
        
        
        context['remaining_balance'] = remaining_balance
        return render(request, 'checkout/wallet.html', context)
    except:
        return redirect('/404error/')




def create_order(request):
    try:
        uid = request.user.userprofile.uid
        selected_address_id = request.session.get('selected_address_id')
        request.session.pop('selected_address_id', None)
        print(selected_address_id)
        selected_address = Address.objects.get(uid=selected_address_id)
        payment_method_instance = Payment_Method.objects.get(method='razorpay')
        profile = UserProfile.objects.get(uid=uid)
        wallet = Wallet.objects.get(user=profile)
        print(payment_method_instance)
        cart = Cart.objects.get(user=profile)
        cart_items = CartItems.objects.filter(cart__user=profile,product__is_selling = True,product__category__is_listed = True)
        grand_total = 0
        for cart_item in cart_items:
            sub_total = cart_item.calculate_sub_total()
            grand_total += sub_total
        for item in cart_items:
            product_stock = Product_Variant.objects.get(product=item.product, size=item.size)
            if product_stock.stock < item.quantity:
                messages.error(request, "Product Out of Stock")
                messages.error(request, "The amount has been credited back to your wallet")
                wallet.amount += grand_total
                wallet.save()
                return redirect('cart')
        order = Order.objects.create(
                user=request.user,
                address=selected_address,
                phone_number=selected_address.phone_number,
                city=selected_address.city,
                district=selected_address.district,
                state=selected_address.state,
                pincode=selected_address.pincode,
                payment_method=payment_method_instance,
                payed=True
            )
        print('Order created:', order.city)
        for item in cart_items:
            sub_total = item.quantity * item.product.selling_price

            order_item = OrderItems.objects.create(
                order=order,  
                product=item.product,
                quantity=item.quantity,
                product_price=item.product.selling_price,
                size=item.size,
                sub_total=sub_total,
                discounted_subtotal=sub_total,
            )

            product_stock = Product_Variant.objects.get(product=item.product, size=item.size)
            product_stock.stock -= item.quantity
            product_stock.sold += item.quantity
            product_stock.save()
            print('Product stock updated')

        order.calculate_bill_amount()
        discounted_total = request.session.get('discounted_total')
        if cart.coupon:
            if cart.coupon.unlisted is False:
                order.amount_to_pay = discounted_total
                print(discounted_total, 'discounttttt')
            else:
                order.amount_to_pay = order.bill_amount
                print(order.bill_amount, 'billlllllllllllllllll')
        else:
            order.amount_to_pay = order.bill_amount
        request.session.pop('discounted_total', None)
        order.status = 'Confirmed'
        order.save()
        print('Order saved again')

        # Clear the user's cart
        cart_items.delete()
        cart.coupon = None
        cart.save()
        print('Cart cleared')

        return redirect(f'/checkout/success_page/')
    except:
        return redirect('/404error/')



def add_new_address(request):
    try:
        context = {}
        user_id = request.user.userprofile.uid
        user_cart = Cart.objects.get(user_id = user_id)
        cart_items = CartItems.objects.filter(cart = user_cart)
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart
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

            return redirect('checkout')
        return render(request, 'checkout/addnewaddress.html',context)
    except:
        return redirect('/404error/')


def success_page(request):
    try:
        context = {}
        user_id = request.user.userprofile.uid
        user_cart = Cart.objects.get(user_id = user_id)
        cart_items = CartItems.objects.filter(cart = user_cart)
        number_in_cart = 0
        for item in cart_items:
            number_in_cart += 1
        context['number_in_cart'] = number_in_cart
        context['user_id'] = user_id 
        return render (request, 'checkout/successpage.html', context)
    except:
        return redirect('/404error/')


def validate_coupon(request):
    # try:
    if request.method == 'POST':
        response_data = {}
        coupon_code = request.POST.get('coupon_code')
        user_id = request.user.userprofile.uid
        user = UserProfile.objects.get(uid = user_id)
        user_cart = Cart.objects.get(user_id = user_id)
        cart_items = CartItems.objects.filter(cart = user_cart, product__is_selling = True, product__category__is_listed = True)
        grand_total = 0
        for item in cart_items:
            grand_total += (item.quantity * item.product.selling_price)
        try:            
            coupon = Coupon.objects.get(code=coupon_code)
        except:
            messages.error(request, 'Invalid coupon')
            return redirect(request.META.get('HTTP_REFERER'))
        current_datetime = timezone.now()
        
        if user not in coupon.users.all():
            if user_cart.coupon:
                user_cart.coupon.users.remove(user)  # Mark the coupon as used by the current user      
                coupon.save()
            coupon.users.add(user)  # Mark the coupon as used by the current user      
            coupon.save()
        else:
            messages.error(request, 'Coupon already applied')
            return redirect(request.META.get('HTTP_REFERER'))
        if coupon.expiry_date >= current_datetime and coupon.minimum_amount <= grand_total and coupon.unlisted is False:
            new_total = grand_total - (grand_total * coupon.discount_percentage)/100
            new_total = round(new_total, 2)
            response_data['new_total'] = new_total
            user_cart.coupon = coupon
            user_cart.save()
            messages.success(request, 'Coupon applied succesfully')
            return redirect(request.META.get('HTTP_REFERER'))
            # return JsonResponse({'success' : True, 'new_total': new_total})
        messages.error(request, 'Invalid coupon')
        return redirect(request.META.get('HTTP_REFERER'))
        # return JsonResponse({'success' : False})
    return redirect('checkout')
    # except:
    #     return redirect('/404error/')


def remove_coupon(request, uid):
    try:
        cart = Cart.objects.get(uid = uid)
        coupon_code = cart.coupon.code
        user_id = request.user.userprofile.uid
        user = UserProfile.objects.get(uid = user_id)
        coupon = Coupon.objects.get(code=coupon_code)
        coupon.users.remove(user) 
        coupon.save()
        cart.coupon = None
        cart.save()
        return redirect(request.META.get('HTTP_REFERER'))
    except:
        return redirect('/404error/')
