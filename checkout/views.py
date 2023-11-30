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
    uid = request.user.userprofile.uid
    context = {}
    profile = UserProfile.objects.get(uid=uid)
    cart = Cart.objects.get(user=profile)
    cart_items = CartItems.objects.filter(cart__user=profile,product__is_selling = True,product__category__is_listed = True)
    number_in_cart = 0
    for item in cart_items:
        number_in_cart += 1
    context['number_in_cart'] = number_in_cart
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
    context['out_of_stock'] = out_of_stock
    context['products'] = cart_items
    context['grand_total'] = grand_total
    context['user'] = profile
    context['addresses'] = addresses
    if request.method == 'POST':
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

        if payment_option == 'wallet':
            # Handle Direct Bank Transfer logic
            
            messages.warning(request, 'You chose ', payment_option)
            print("Selected Payment Option: Direct Bank Transfer")
            return redirect('wallet_payment')
        elif payment_option == 'razorpay':
            
            print("Selected Payment Option: RazorPay")
            grand_total = grand_total*100
            client = razorpay.Client(auth=("rzp_test_KSJKvKAn2yU3LA", "1aqi5ebdJfkUFfAiXFOFuALn"))

            DATA = {
                "amount": int(grand_total),
                "currency": "INR",
                "payment_capture":'1'
                
            }
            client.order.create(data=DATA)

            return render(request,"checkout/razorpay.html", {"grand_total":grand_total})
        elif payment_option == 'cash_on_delivery':
            # Handle Cash on Delivery logic
            print("Selected Payment Option: Cash on Delivery")

            payment_method_instance = Payment_Method.objects.get(method='cash_on_delivery')            
            print('instance: ', payment_method_instance)

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

                product_stock = Product_Variant.objects.get(product=item.product, size=item.size)
                product_stock.stock -= item.quantity
                product_stock.sold += item.quantity
                product_stock.save()
                print('Product stock updated')

            order.calculate_bill_amount()
            order.amount_to_pay = order.bill_amount
            order.status = 'Confirmed'
            order.save()
            print('Order saved again')

            # Clear the user's cart
            cart_items.delete()
            print('Cart cleared')

            return redirect(f'/checkout/success_page/')

        else:
            messages.warning(request, 'Please choose a payment option')
        
        return redirect(request.META.get("HTTP_REFERER"))
    
    return render(request, 'checkout/checkout.html', context)


def wallet_payment(request):
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
        print('wallet.amount')
        wallet.amount = remaining_balance
        print('                   ',wallet.amount)
        wallet.save()
        print('                                       ',wallet.amount)
        uid = request.user.userprofile.uid
        selected_address_id = request.session.get('selected_address_id')
        print(selected_address_id)
        selected_address = Address.objects.get(uid=selected_address_id)
        payment_method_instance = Payment_Method.objects.get(method='wallet')
        profile = UserProfile.objects.get(uid=uid)
        print(payment_method_instance)
        cart = Cart.objects.get(user=profile)
        cart_items = CartItems.objects.filter(cart__user=profile,product__is_selling = True,product__category__is_listed = True)
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
        order.amount_to_pay = order.bill_amount
        order.status = 'Confirmed'
        order.save()
        print('Order saved again')

        # Clear the user's cart
        cart_items.delete()
        print('Cart cleared')

        return redirect(f'/checkout/success_page/')
        
    context['user'] = user
    context['out_of_stock'] = out_of_stock
    context['products'] = cart_items
    context['grand_total'] = grand_total
    context['wallet'] = wallet
    
    
    context['remaining_balance'] = remaining_balance
    return render(request, 'checkout/wallet.html', context)


def create_order(request):
    uid = request.user.userprofile.uid
    selected_address_id = request.session.get('selected_address_id')
    print(selected_address_id)
    selected_address = Address.objects.get(uid=selected_address_id)
    payment_method_instance = Payment_Method.objects.get(method='razorpay')
    profile = UserProfile.objects.get(uid=uid)
    print(payment_method_instance)
    cart = Cart.objects.get(user=profile)
    cart_items = CartItems.objects.filter(cart__user=profile,product__is_selling = True,product__category__is_listed = True)
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
    order.amount_to_pay = order.bill_amount
    order.status = 'Confirmed'
    order.save()
    print('Order saved again')

    # Clear the user's cart
    cart_items.delete()
    print('Cart cleared')

    return redirect(f'/checkout/success_page/')



def add_new_address(request):
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


def success_page(request):
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


def validate_coupon(request):
    # if request.method == 'POST':
    #     code = request.POST.get('coupon_code')
    #     context = {}
    #     response_data = {}
    #     user_id = request.user.userprofile.uid
    #     user_cart = Cart.objects.get(user_id = user_id)
    #     cart_items = CartItems.objects.filter(cart = user_cart, product__is_selling = True, product__category__is_listed = True)
    #     grand_total = 0
    #     for item in cart_items:
    #         grand_total += (item.quantity * item.product.selling_price)
    #     print(grand_total)
    #     coupon = Coupon.objects.get(code=code)
    #     current_datetime = timezone.now()
    #     no = CouponHistory.objects.filter(user = request.user.profile, coupon = coupon).count()
    #     if coupon.expiry_date >= current_datetime and coupon.minimum_amount <= grand_total and (no+1) <= coupon.maximum_use and coupon.unlisted is False:
    #         response_data['success'] = True
    #         response_data['discount_percent'] = coupon.discount_percentage
    #         grand_total = float(grand_total) * ((100 - float(coupon.discount_percentage))/100)
    #         response_data['total'] = grand_total + 50
    return redirect('checkout')
