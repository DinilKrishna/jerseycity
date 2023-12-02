from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from checkout.models import *
from userauth.decorator import login_required
from .models import *
from django.contrib import messages

# Create your views here.

@login_required
def add_to_cart(request):
    try:
        if request.method == 'POST':
            product = request.POST.get('product_uid')
            print(product)
            size_id = request.POST.get('size_id')
            print(size_id)
            product_obj = Product.objects.get(uid = product)
            size = Size.objects.get(id = size_id)
            product_variant = Product_Variant.objects.get(product = product_obj, size = size_id)
            cart, created = Cart.objects.get_or_create(user = request.user.userprofile)
            if product_variant.stock <= 1:
                return JsonResponse({'stock' : True})
            
            cart_item, item_created = CartItems.objects.get_or_create(
                cart= cart, 
                product = product_obj,
                size = size
                )
            # messages.success(request, "Added to cart")
            
            if not item_created:
                if cart_item.quantity < product_variant.stock:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    return JsonResponse({'stock' : True})
            return JsonResponse({'success': True})
    except Exception as e:
        print('excepteddddddddddddddddddddddddddddddddddddddddddddd')
        return JsonResponse({'success': False, 'error_message': str(e)})
    

def add_quantity(request, uid):
    user_uid = request.user.userprofile.uid
    profile = get_object_or_404(UserProfile, uid=user_uid)
    cart = Cart.objects.get(user = profile)
    cart_item = CartItems.objects.get(uid=uid)
    cart_items = CartItems.objects.filter(cart=cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
    product_variant = Product_Variant.objects.get(product=cart_item.product, size=cart_item.size)
    
    if cart_item.quantity == product_variant.stock:
        return JsonResponse({'success': False})
        
    else:
        cart_item.quantity += 1
        cart_item.save()
        subtotal = cart_item.calculate_sub_total()
    grand_total = 0
    try:
        for item in cart_items:
            sub_total = item.calculate_sub_total()
            grand_total += sub_total
            
    except Exception as e:
        return HttpResponse(e)

    return JsonResponse({'success': True, 'quantity': cart_item.quantity, 'subtotal': subtotal, 'grand_total': grand_total})



def decrease_quantity(request, uid):
    user_uid = request.user.userprofile.uid
    profile = get_object_or_404(UserProfile, uid=user_uid)
    cart = Cart.objects.get(user = profile)
    cart_item = CartItems.objects.get(uid=uid)
    cart_items = CartItems.objects.filter(cart=cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
    
    if cart_item.quantity == 1:
        return JsonResponse({'success': False})
    else:
        cart_item.quantity -= 1
        cart_item.save()
        subtotal = cart_item.calculate_sub_total()
    grand_total = 0
    try:
        for item in cart_items:
            sub_total = item.calculate_sub_total()
            grand_total += sub_total
    except Exception as e:
        return HttpResponse(e)

    return JsonResponse({'success': True, 'quantity': cart_item.quantity, 'subtotal': subtotal, 'grand_total': grand_total})


def remove_from_cart(request, uid):
    try:
        cart = CartItems.objects.get(uid=uid)
        cart.delete()
        return redirect(request.META.get("HTTP_REFERER"))
    except Cart.DoesNotExist:
        return HttpResponse("Cart not found")
    except Exception as e:
        return redirect("/404error")
    

def add_to_wishlist(request, uid):
    try:
        product = Product.objects.get(uid=uid)
        user_id = request.user.userprofile.uid
        user = UserProfile.objects.get(uid=user_id)
        wishlist = Wishlist.objects.get(user=user)

        # Check if the product is already in the wishlist
        if WishlistItems.objects.filter(wishlist=wishlist, product=product).exists():
            return JsonResponse({'success': False, 'message': 'Product is already in the wishlist'})

        # If not, add the product to the wishlist
        wishlist_item = WishlistItems.objects.create(wishlist=wishlist, product=product)
        wishlist_item.save()

        return JsonResponse({'success': True, 'message': 'Product added to wishlist successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
    

def remove_from_wishlist(request, uid):
    try:
        print(uid)
        user = UserProfile.objects.get(uid = request.user.userprofile.uid)
        print(user)
        wishlist = Wishlist.objects.get(user = user)
        print(wishlist)
        wishlist_items = WishlistItems.objects.get(wishlist = wishlist, product__uid = uid )
        wishlist_items.delete()
        return redirect(request.META.get("HTTP_REFERER"))
    except Wishlist.DoesNotExist:
        return HttpResponse("Wishlist not found")
    except Exception as e:
        return HttpResponse(e)
    

def return_order(request, uid):
    order = Order.objects.get(uid=uid)
    order.status = 'Returned'
    order.save()
    amount = order.amount_to_pay
    user = UserProfile.objects.get(uid = request.user.userprofile.uid)
    wallet = Wallet.objects.get(user = user)
    order_items = OrderItems.objects.filter(order = order)
    wallet.amount += amount
    wallet.save()
    for item in order_items:
        product_variant = Product_Variant.objects.get(product=item.product, size=item.size)
        product_variant.stock += item.quantity  # Increase stock by the quantity returned
        product_variant.save()

    return redirect(request.META.get('HTTP_REFERER'))