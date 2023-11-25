from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from userauth.decorator import login_required
from .models import *
from django.contrib import messages

# Create your views here.

@login_required
def add_to_cart(request, product_uid, size_id):
    try:
        product_obj = Product.objects.get(uid = product_uid)
        size = Size.objects.get(id = size_id)
        product_variant = Product_Variant.objects.get(product = product_obj, size = size)
        cart, created = Cart.objects.get_or_create(user = request.user.userprofile)
        if product_variant.stock <= 1:
            messages.warning(request, "Out of Stock")
            return redirect(request.META.get("HTTP_REFERER"))
        
        cart_item, item_created = CartItems.objects.get_or_create(
            cart= cart, 
            product = product_obj,
            size = size
            )
        
        if not item_created:
            if cart_item.quantity < product_variant.stock:
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, "Added to cart")
            else:
                messages.warning(request, "Out of stock")
        return redirect(request.META.get("HTTP_REFERER"))
    except Exception as e:
        return HttpResponse(e)
    

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