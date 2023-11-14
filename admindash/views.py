from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from products.models import *
from django.urls import reverse
from . decorators import admin_required
from userauth.models import UserProfile
from django.db.models import Q

# Create your views here.


def admin_login_page(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect ('admin_dashboard')
    return render (request, 'adminside/adminlogin.html')

def admin_log_out(request):
    if request.user.is_authenticated:
        logout(request)  
        request.session.flush()
    return redirect('admin_login_page')

def admin_dashboard(request):
    if request.user.is_authenticated and request.user.is_staff:
        return render (request, 'adminside/adminpanel.html')
    return redirect('admin_login_page')


def admin_products(request):
    if request.user.is_authenticated and request.user.is_staff:
        context = {}
        # Get the search query from the form
        search_query = request.GET.get('search', '')
        
        # Filter products based on the search query
        if search_query:
            products = Product.objects.filter(
                Q(product_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            products = Product.objects.all()

        categories = Category.objects.all()
        sizes = Size.objects.all()
        context['categories'] = categories
        context['products'] = products
        context['sizes'] = sizes
        context['search_query'] = search_query
        return render (request, 'adminside/adminproducts.html',context)
    return redirect('admin_login_page')


def users(request):
    context = {}
    if  request.user.is_authenticated and request.user.is_staff is True:
        user_obj = User.objects.all().order_by('-date_joined')
        profile_obj = UserProfile.objects.all()
        context['users'] = user_obj
        context['profiles'] = profile_obj
        return render(request, 'adminside/users.html', context)
    else:
        return redirect('admin_login_page')

def user_details(request):
    if request.user.is_authenticated and request.user.is_staff:
        return render (request, 'adminside/userdetails.html')
    return redirect('admin_login_page')

def add_product_page(request):
    context = {}
    if request.user.is_authenticated and request.user.is_staff:        
        categories = Category.objects.all()
        sizes = Size.objects.all()
        context['categories'] = categories
        context['sizes'] = sizes
        return render (request, 'adminside/addproduct.html', context)

    return redirect('admin_login_page')

# def edit_product_page(request):
#     if request.user.is_authenticated and request.user.is_staff:
#         return render(request, 'adminside/editproducts.html')
#     return redirect('admin_login')

@admin_required
def categories(request):
    context = {}
    categories = Category.objects.all()
    context['categories'] = categories
    if request.method == "POST":
        category_name = request.POST.get('category_name')
        category_slug = request.POST.get('category_slug')
        category_description = request.POST.get('category_description')
        if Category.objects.filter(category_name = category_name).exists():
            messages.error(request, 'Categorie already exists!!')
        elif Category.objects.filter(category_slug = category_slug).exists():
            messages.error(request, 'Slug already exists!!')
        else:
            new_category = Category(
                category_name=category_name,
                category_slug=category_slug,
                category_description=category_description
            )
            new_category.save()

    return render(request, 'adminside/categories.html', context)


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('adminemail')
        password = request.POST.get('adminpassword')        
        authenticated_user = authenticate(username=username, password=password)
        if authenticated_user is not None:
            user = User.objects.get(username =username)
            if user.is_staff or user.is_superuser:
                login(request, authenticated_user)
                return redirect('admin_dashboard')
            else:
                messages.warning(request, 'You do not have staff privileges.')
        else:
            messages.warning(request, 'Invalid credentials.')     
    
    return render(request, "adminside/adminlogin.html") 

def add_product(request):
    context = {}
    
    if request.method == "POST":
        product_name = request.POST.get('product_name')
        price = request.POST.get('price')
        selling_price = request.POST.get('selling_price')
        category = request.POST.get('category')
        # print(category)
        try:
            s_stock = int(request.POST.get('s_stock'))
            m_stock = int(request.POST.get('m_stock'))
            l_stock = int(request.POST.get('l_stock'))
            xl_stock =int(request.POST.get('xl_stock'))
        except Exception as e:
            messages.error(request, e)
            return redirect('add_product_page')

        description = request.POST.get('description')

        image_front = request.FILES.get('image_front')
        image_back = request.FILES.get('image_back')
        extra_image_one = request.FILES.get('extra_image_one')
        extra_image_two = request.FILES.get('extra_image_two')

        try:
            category_obj = Category.objects.get(category_name=category)
            size_obj_s, _ = Size.objects.get_or_create(size='S')
            size_obj_m, _ = Size.objects.get_or_create(size='M')
            size_obj_l, _ = Size.objects.get_or_create(size='L')
            size_obj_xl, _ = Size.objects.get_or_create(size='XL')
            product_obj = Product.objects.filter(
                product_name=product_name,
                price=price,
                selling_price=selling_price,
                category=category_obj,
                description=description,
                image_front=image_front
            )

        except Exception as e:
            messages.error(request, e)
            return redirect('add_product_page')
        
        # Check if a product with the given attributes already exists
        existing_product = Product.objects.filter(
            product_name=product_name,
            price=price,
            selling_price=selling_price,
            category=category_obj,
            description=description,
            image_front=image_front
        ).first()

        if existing_product:
            messages.warning(request, 'Product already exists!')
            return redirect(reverse('add_product'))

        # Convert price and selling_price to float for further checks
        price_float = float(price)
        selling_price_float = float(selling_price)

        # Create the Product instance


        # Attempt to create the variants
        try:

            existing_product = Product.objects.create(
                product_name=product_name,
                price=price_float,
                selling_price=selling_price_float,
                category=category_obj,
                description=description,
                image_front=image_front
            )
            Product_Variant.objects.create(product=existing_product, size=size_obj_s, stock=s_stock)
            Product_Variant.objects.create(product=existing_product, size=size_obj_m, stock=m_stock)
            Product_Variant.objects.create(product=existing_product, size=size_obj_l, stock=l_stock)
            Product_Variant.objects.create(product=existing_product, size=size_obj_xl, stock=xl_stock)
            
        except Exception as e:
            messages.error(request, e)
            return redirect('add_product_page')
        

        # If variants are created successfully, proceed to create the product images
        Product_Image.objects.create(
            product=existing_product,
            image_back=image_back,
            extra_image_one=extra_image_one,
            extra_image_two=extra_image_two
        )

        # After successful creation, return the user to the desired page
        return redirect(reverse('admin_products'))
    if  request.user.is_authenticated and request.user.is_staff is True:
        categories = Category.objects.all()
        sizes = Size.objects.all()
        context['categories'] = categories
        context['sizes'] = sizes
        return render(request, 'adminside/addproduct.html', context)
    else:
        return redirect(admin_login_page)



def edit_product(request, uid):
    context = {}
    products = Product.objects.get(uid = uid)
    image = Product_Image.objects.get(product = products)
    categories = Category.objects.all()
    sizes = Size.objects.all()
    size_obj_s = Size.objects.get(size='S')
    size_obj_m = Size.objects.get(size='M')
    size_obj_l = Size.objects.get(size='L')
    size_obj_xl = Size.objects.get(size='XL')

    if request.method == "POST":
        product_name = request.POST.get('product_name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        selling_price = request.POST.get('selling_price')
        s_stock = request.POST.get('s_stock')
        m_stock = request.POST.get('m_stock')
        l_stock = request.POST.get('l_stock')
        xl_stock = request.POST.get('xl_stock')
        image_front = request.FILES.get('image_front') if 'image_front' in request.FILES else None
        category = request.POST.get('category')
        image_back = request.FILES.get('image_back') if 'image_back' in request.FILES else None
        extra_image_one = request.FILES.get('extra_image_one') if 'extra_image_one' in request.FILES else None
        extra_image_two = request.FILES.get('extra_image_two') if 'extra_image_two' in request.FILES else None

        try:
            
            sizess = [size_obj_s, size_obj_m, size_obj_l, size_obj_xl]
            quantity_of_s =  Product_Variant.objects.get(product = products, size = size_obj_s)  
            quantity_of_m = Product_Variant.objects.get(product = products, size = size_obj_m)
            quantity_of_l = Product_Variant.objects.get(product = products, size = size_obj_l)
            quantity_of_xl =  Product_Variant.objects.get(product = products, size = size_obj_xl)  
            quantity_of_s.stock = s_stock
            quantity_of_m.stock = m_stock
            quantity_of_l.stock = l_stock
            quantity_of_xl.stock = xl_stock
            quantity_of_s.save()
            quantity_of_m.save()
            quantity_of_l.save()
            quantity_of_xl.save()  
            category_instance = Category.objects.get(category_name=category)
            
            products.product_name = product_name
            products.description = description

            
            
            if image_front is not None:
                products.image_front = image_front
            
            products.category = category_instance
            products.price = price
            products.selling_price = selling_price


            if image_back is not None:
                image.image_back = image_back
            if extra_image_one is not None:
                image.extra_image_one = extra_image_one
            if extra_image_two is not None:
                image.extra_image_two = extra_image_two

            products.save()
            if image_front is not None:
                products.image_front.save(image_front.name, image_front)

            image.save()
            if image_back is not None:
                image.image_back.save(image_back.name, image_back)
            if extra_image_one is not None:
                image.extra_image_one.save(extra_image_one.name, extra_image_one)
            if extra_image_two is not None:
                image.extra_image_two.save(extra_image_two.name, extra_image_two)
            
            # messages.success(request, 'Edited Successfully!')
            return redirect(reverse('admin_products'))
            
        except Exception as e:
            messages.error(request, str(e))
            
   
    context['categories'] = categories
    context['sizes'] = sizes
    context['stock_s'] = Product_Variant.objects.get(product = products, size = size_obj_s).stock
    context['stock_m'] = Product_Variant.objects.get(product = products, size = size_obj_m).stock
    context['stock_l'] = Product_Variant.objects.get(product = products, size = size_obj_l).stock
    context['stock_xl'] = Product_Variant.objects.get(product = products, size = size_obj_xl).stock
    context['product'] = products
    context['image'] = image
    return render(request, 'adminside/editproduct.html', context)

@admin_required
def delete_product(request, uid):
    try:
        product = Product.objects.get(uid = uid)
        if product.is_selling is True:
            product.is_selling = False
            product.save()
        elif product.is_selling is False:
            product.is_selling = True
            product.save()
        return redirect(reverse('admin_products'))
    except Exception as e:
        return HttpResponse(e)

@admin_required
def block_user(request, uid):
    try:
        profile_obj = UserProfile.objects.get(uid = uid)
        if profile_obj.is_blocked is True:
            profile_obj.is_blocked = False
            profile_obj.save()
        elif profile_obj.is_blocked is False:
            profile_obj.is_blocked = True
            profile_obj.save()
        return redirect(reverse('users'))
    except Exception as e:
        return HttpResponse(e)
    
@admin_required
def edit_category(request, id):
    context = {}
    categories = Category.objects.get(id = id)
    context['categories'] = categories

    if request.method == "POST":
        category_name = request.POST.get('category_name')
        category_slug = request.POST.get('category_slug')
        category_description = request.POST.get('category_description')

        if Category.objects.filter(category_name__iexact=category_name).exclude(id=id).exists():
            messages.error(request, 'Category with this name already exists.')
            return render(request, 'adminside/editcategory.html', context)

        # Check if a category with the same slug exists
        if Category.objects.filter(category_slug__iexact=category_slug).exclude(id=id).exists():
            messages.error(request, 'Category with this slug already exists.')
            return render(request, 'adminside/editcategory.html', context)


        categories.category_name = category_name
        categories.category_slug = category_slug
        categories.category_description = category_description
        categories.save()
        return redirect(reverse('categories'))

    return render(request, 'adminside/editcategory.html', context)

@admin_required
def delete_category(request, id):
    try:
        category = Category.objects.get(id = id)
        if category.is_listed is True:
            category.is_listed = False
            category.save()
        elif category.is_listed is False:
            category.is_listed = True
            category.save()
        return redirect(reverse('categories'))
    except Exception as e:
        return HttpResponse(e)