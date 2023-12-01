from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from products.models import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
import random
from django.core.mail import send_mail

# Create your views here.

def landing_page(request):
    context = {}
    products = Product.objects.all()
    categories = Category.objects.all()
    sizes = Size.objects.all()
    context['categories'] = categories
    context['products'] = products
    context['sizes'] = sizes
    # print(products)
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('home_page')
    elif request.user.is_authenticated:
        logout(request)
    return render(request, 'pages/landing.html', context)


def login_page(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('user_profile')
    elif request.user.is_authenticated:
        logout(request)
    return render(request, 'pages/login.html')

def signup_page(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('user_profile')
    elif request.user.is_authenticated:
        logout(request)
    return render(request, 'pages/signup.html')


def home_page(request):
    context = {}
    
    products = Product.objects.filter(is_selling=True).order_by('-updated_at')[:6]
    categories = Category.objects.all()
    sizes = Size.objects.all()
    context['categories'] = categories
    context['products'] = products
    context['sizes'] = sizes
    
    if request.user.is_authenticated and not request.user.is_staff:
        uid = request.user.userprofile.uid
        profile = UserProfile.objects.get(uid = uid)
        user_cart = Cart.objects.get(user = profile)
        cart_items = CartItems.objects.filter(cart=user_cart,product__is_selling = True,product__category__is_listed = True).order_by("-created_at")
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
        return render(request, 'pages/home.html', context)
    elif request.user.is_authenticated:
        logout(request)
    return redirect('landing_page')


def shop_page(request):
    context = {}
    products = Product.objects.filter(is_selling=True).order_by('created_at')
    if request.user.is_authenticated and not request.user.is_staff:
        user_id = request.user.userprofile.uid
        profile = UserProfile.objects.get(uid = user_id)
        user_cart = Cart.objects.get(user_id = user_id)
        cart_items = CartItems.objects.filter(cart = user_cart)
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
    categories = Category.objects.filter(is_listed = True)
    sizes = Size.objects.all()

    # Get the search query from the GET parameters
    search_query = request.GET.get('q', '')

    # Filter products based on the search query
    products = Product.objects.filter(
        Q(category__is_listed = True) &
        Q(is_selling = True) & 
        (Q(product_name__icontains=search_query) |
        Q(description__icontains=search_query))
    ).order_by('created_at')

    # Initialize selected_category as None
    selected_category = None
    # Get the selected category from the GET parameters
    selected_category_id = request.GET.get('category_id')
    if selected_category_id:
        selected_category = get_object_or_404(Category, pk=selected_category_id)
        products = products.filter(category=selected_category)

    price_range = request.GET.get('price_range')

    if price_range:
        price_ranges = [
            ('0-40', Q(selling_price__lte=40)),
            ('40-60', Q(selling_price__gt=40, selling_price__lte=60)),
            ('60+', Q(selling_price__gt=60)),
        ]

        selected_price_filter = None

        for range_key, q_object in price_ranges:
            if range_key == '60+' and price_range.startswith('60'):
                selected_price_filter = q_object
                break
            elif range_key == price_range:
                selected_price_filter = q_object
                break

        if selected_price_filter:
            products = products.filter(selected_price_filter)

    items_per_page = 3
    paginator = Paginator(products, items_per_page)
    
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If the page parameter is not an integer, deliver the first page.
        products = paginator.page(1)
    except EmptyPage:
        # If the page is out of range (e.g., 9999), deliver the last page of results.
        products = paginator.page(paginator.num_pages)

    # Get the current page number
    current_page = products.number

    # Calculate the range of page numbers to display
    start_page = max(1, current_page - 1)
    end_page = min(paginator.num_pages, current_page + 1)

    # If the last product of the current page is removed, and there are more products, fetch the next page
    if current_page < paginator.num_pages and len(products) <= items_per_page:
        next_page = paginator.page(current_page + 1)
        products.object_list = list(products.object_list)
        products.object_list.extend(next_page.object_list[:items_per_page - len(products)])
        paginator.count += len(products.object_list)

    

    # Adjust the start and end page if there are not enough pages to display
    if end_page - start_page < 2:
        if start_page == 1:
            end_page = min(3, paginator.num_pages)
        else:
            start_page = max(1, paginator.num_pages - 2)

    # Create a list of page numbers to display
    page_numbers = range(start_page, end_page + 1)

    context['categories'] = categories
    context['selected_category'] = selected_category
    context['products'] = products
    context['sizes'] = sizes
    context['page_numbers'] = page_numbers
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
    return render(request, 'pages/shop.html', context)


def product_details(request, uid):
    try:
        context = {}
        if request.user.is_authenticated and not request.user.is_staff:
            user_id = request.user.userprofile.uid
            profile = UserProfile.objects.get(uid = user_id)
            user_cart = Cart.objects.get(user_id = user_id)
            cart_items = CartItems.objects.filter(cart = user_cart)
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
        product_obj = Product.objects.get(uid = uid)
        product_img_obj = Product_Image.objects.get(product = product_obj)
        category_obj = product_obj.category
        sizes = Size.objects.all()
        products_with_category = Product.objects.filter(category = category_obj)
        if request.method == "POST":
            size = request.POST.get('size')
            size_obj  = Size.objects.get(id = size)
            return redirect(f'/products/add_to_cart/{product_obj.uid}/{size_obj.id}')

        if request.user.is_authenticated and request.user.is_staff is False:
            # context['wishlist'] = [item.product for item in Wishlist.objects.filter(user=request.user.profile)]
            context['user'] = profile
        # context['reviews'] = Review.objects.filter(product = product_obj).exclude(review = "")
        print(product_obj.uid)
        offer_percentage = (1 - (product_obj.selling_price/product_obj.price)) * 100
        context['products'] = product_obj
        context['offer_percentage'] = round(offer_percentage)
        context['sizes'] = sizes
        context['images'] = product_img_obj
        context['category_products'] = products_with_category
        
        return render(request, 'pages/productdetails.html', context)
    except Exception as e:
        return HttpResponse(e)


def about_page(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
    context = {}
    user_id = request.user.userprofile.uid
    profile = UserProfile.objects.get(uid = user_id)
    user_cart = Cart.objects.get(user_id = user_id)
    cart_items = CartItems.objects.filter(cart = user_cart)
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
    return render(request, 'pages/about.html', context)

def contact_page(request):
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
    context = {}
    user_id = request.user.userprofile.uid
    profile = UserProfile.objects.get(uid = user_id)
    user_cart = Cart.objects.get(user_id = user_id)
    cart_items = CartItems.objects.filter(cart = user_cart)
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
    return render(request, 'pages/contact.html', context)

def error(request):
    return render(request, '404/index.html')

