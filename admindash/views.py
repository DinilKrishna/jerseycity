from datetime import date, datetime, timedelta
import re
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from userauth.views import validate_image
from products.models import *
from django.urls import reverse
from . decorators import admin_required
from userauth.models import UserProfile
from django.db.models import Q
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from checkout.models import *
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.db.models import F, Case, When, Value
from django.db.models.functions import Now
from django.db.models import Sum
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder

# Create your views here.

@never_cache
def admin_login_page(request):
    try:
        if request.user.is_authenticated and request.user.is_staff:
            return redirect ('admin_dashboard')
        return render (request, 'adminside/adminlogin.html')
    except:
        return redirect('/404error/')

@never_cache
def admin_log_out(request):
    try:
        if request.user.is_authenticated:
            logout(request)  
            request.session.flush()
        return redirect('admin_login_page')
    except:
        return redirect('/404error/')

def admin_dashboard(request):
    try:
        if request.user.is_authenticated and request.user.is_staff:
            context = {}
            
            total_users = UserProfile.objects.count()
            active_users = UserProfile.objects.filter(is_blocked=False).count()
            total_orders = Order.objects.count()
            returned_orders = Order.objects.filter(status='Returned').count()
            cancelled_orders = Order.objects.filter(status='Cancelled').count()
            total_products = Product.objects.count()
            selling_products = Product.objects.filter(is_selling=True).count()
            total_categories = Category.objects.count()
            all_orders = Order.objects.all()
            completed_orders = Order.objects.filter(payed=True).exclude(status__in=['Returned', 'Cancelled'])
            total_amount = all_orders.aggregate(total_amount=Sum('amount_to_pay'))['total_amount'] or 0
            profit_amount = completed_orders.aggregate(total_amount=Sum('amount_to_pay'))['total_amount'] or 0
            current_month = timezone.now().month
            current_year = timezone.now().year
            years = list(range(2022, current_year + 1))
            monthly_sales_sum = Order.objects.filter(created_at__month=current_month).aggregate(monthly_sales=Sum('amount_to_pay'))['monthly_sales'] or 0
            yearly_sales_sum = Order.objects.filter(created_at__year=current_year).aggregate(yearly_sales=Sum('amount_to_pay'))['yearly_sales'] or 0

            # New: Calculate total order amount for the current year
            total_yearly_sales = Order.objects.filter(created_at__year=current_year).aggregate(total_yearly_sales=Sum('amount_to_pay'))['total_yearly_sales'] or 0

            context['total_orders'] = total_orders
            context['returned_orders'] = returned_orders
            context['cancelled_orders'] = cancelled_orders
            context['total_users'] = total_users
            context['active_users'] = active_users
            context['total_amount'] = total_amount
            context['profit_amount'] = profit_amount
            context['total_products'] = total_products
            context['selling_products'] = selling_products
            context['total_categories'] = total_categories
            context['monthly_sales'] = monthly_sales_sum
            context['yearly_sales'] = yearly_sales_sum
            context['total_yearly_sales'] = total_yearly_sales  
            context['year'] = current_year
            context['years'] = years

            if request.method == 'POST':
                selected_year = int(request.POST.get('selected_year', current_year))
                context['year'] = selected_year

            monthly_sales_data = Order.objects.filter(created_at__year=context['year']).values('created_at__month').annotate(monthly_sales=Sum('amount_to_pay'))
            months = [entry['created_at__month'] for entry in monthly_sales_data]
            monthly_sales = [entry['monthly_sales'] or 0 for entry in monthly_sales_data]

            context['monthly_sales'] = json.dumps([float(sale) for sale in monthly_sales], cls=DjangoJSONEncoder)
            context['months'] = json.dumps(months)

            return render(request, 'adminside/adminpanel.html', context)
        return redirect('admin_login_page')
    except:
        return redirect('/404error/')


def report(request):
    try:
        context = {}
        if request.method == 'POST':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            try:
                if start_date > end_date:
                    messages.error(request, 'Use a valid date range')
                    return redirect(request.META.get('HTTP_REFERER'))  # Redirect to the same page to display the error message
                
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

                # Retrieve orders between the specified start and end dates
                orders = Order.objects.filter(created_at__range=[start_date, end_date]).order_by('created_at')
                context['orders'] =orders
                for order in orders:
                    print("----------------", order.amount_to_pay)
            except ValueError:
                messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
                return HttpResponseRedirect(request.path_info)  # Redirect to the same page to display the error message

        return render(request, 'adminside/reportpage.html', context)
    except:
        return redirect('/404error/')


def admin_products(request):
    try:
        if request.user.is_authenticated and request.user.is_staff:
            context = {}
            search_query = request.GET.get('search', '')
            
            if search_query:
                products = Product.objects.filter(
                    Q(product_name__icontains=search_query) |
                    Q(description__icontains=search_query)
                ).order_by('-created_at')
            else:
                products = Product.objects.all().order_by('-created_at')

            categories = Category.objects.all()
            sizes = Size.objects.all()
            context['categories'] = categories
            context['sizes'] = sizes

            # Pagination
            items_per_page = 5
            paginator = Paginator(products, items_per_page)
            
            page = request.GET.get('page')
            try:
                products = paginator.page(page)
            except PageNotAnInteger:
                products = paginator.page(1)
            except EmptyPage:
                products = paginator.page(paginator.num_pages)

            current_page = products.number

            start_page = max(1, current_page - 1)
            end_page = min(paginator.num_pages, current_page + 1)

            if end_page - start_page < 2:
                if start_page == 1:
                    end_page = min(3, paginator.num_pages)
                else:
                    start_page = max(1, paginator.num_pages - 2)

            # Create a list of page numbers to display
            page_numbers = range(start_page, end_page + 1)

            context['products'] = products
            context['search_query'] = search_query
            context['page_numbers'] = page_numbers
            return render(request, 'adminside/adminproducts.html', context)
        return redirect('admin_login_page')
    except:
        return redirect('/404error/')


def users(request):
    try:
        context = {}
        if request.user.is_authenticated and request.user.is_staff:
            profile_obj = UserProfile.objects.all().order_by('-created_at')

            search_query = request.GET.get('search', '')

            if search_query:
                profile_obj = profile_obj.filter(
                    Q(user__first_name__icontains=search_query) |
                    Q(user__last_name__icontains=search_query) |
                    Q(user__email__icontains=search_query)
                ).order_by('-created_at')

            paginator = Paginator(profile_obj, 5)
            page = request.GET.get('page')

            try:
                profile_obj = paginator.page(page)
            except PageNotAnInteger:
                profile_obj = paginator.page(1)
            except EmptyPage:
                profile_obj = paginator.page(paginator.num_pages)

            current_page = profile_obj.number

            start_page = max(1, current_page - 1)
            end_page = min(paginator.num_pages, current_page + 1)
            if current_page < paginator.num_pages and len(profile_obj) <= paginator.num_pages:
                next_page = paginator.page(current_page + 1)
                profile_obj.object_list = list(profile_obj.object_list)
                profile_obj.object_list.extend(next_page.object_list[:5 - len(profile_obj)])
                paginator.count += len(profile_obj.object_list)

            if end_page - start_page < 2:
                if start_page == 1:
                    end_page = min(3, paginator.num_pages)
                else:
                    start_page = max(1, paginator.num_pages - 2)

            page_numbers = range(start_page, end_page + 1)
            context['page_numbers'] = page_numbers
            context['profiles'] = profile_obj
            context['search_query'] = search_query

            return render(request, 'adminside/users.html', context)
        else:
            return redirect('admin_login_page')
    except:
        return redirect('/404error/')

def user_details(request):
    try:
        if request.user.is_authenticated and request.user.is_staff:
            return render (request, 'adminside/userdetails.html')
        return redirect('admin_login_page')
    except:
        return redirect('/404error/')

def add_product_page(request):
    try:
        context = {}
        if request.user.is_authenticated and request.user.is_staff:        
            categories = Category.objects.all()
            sizes = Size.objects.all()
            context['categories'] = categories
            context['sizes'] = sizes
            return render (request, 'adminside/addproduct.html', context)

        return redirect('admin_login_page')
    except:
        return redirect('/404error/')


@admin_required
def categories(request):
    try:
        context = {}
        categories = Category.objects.all()
        context['categories'] = categories
        if request.method == "POST":
            category_name = request.POST.get('category_name')
            category_slug = request.POST.get('category_slug')
            if Category.objects.filter(category_name = category_name).exists():
                messages.error(request, 'Categorie already exists!!')
            elif Category.objects.filter(category_slug = category_slug).exists():
                messages.error(request, 'Slug already exists!!')
            else:
                new_category = Category(
                    category_name=category_name,
                    category_slug=category_slug,
                )
                new_category.save()

        return render(request, 'adminside/categories.html', context)
    except:
        return redirect('/404error/')


def admin_login(request):
    try:
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
    except:
        return redirect('/404error/')


def is_valid_description(description):
    try:
        
        description = description.strip()

        if not description:
            return False
        
        if not (5 <= len(description) <= 100):
            return False
        
        return True
    except:
        return redirect('/404error/')


def is_valid_product_title(title):
    try:
        title = title.strip()

        if not title:
            return False

        # Allow any characters, including symbols
        if not re.match(r'^[^\n\r\t\v\f]*$', title):
            return False

        if not (3 <= len(title) <= 100):
            return False
        
        return True
    except:
        return redirect('/404error/')


def is_valid_price(price):
    try:
        price = float(price)

        if price > 0:
            return True
        else:
            return False
    except ValueError:
            return False
    

def is_valid_stock(stock):
    try:

        stock = int(stock)

        if stock >= 0:
            return True
        else:
            return False
    except ValueError:

        return False
    

def add_product(request):
    try:
        context = {}
        
        if request.method == "POST":
            product_name = request.POST.get('product_name')
            price = request.POST.get('price')
            selling_price = price
            category = request.POST.get('category')

            if not is_valid_product_title(product_name):
                messages.error(request, f'{product_name} Not a valid product Name')
                return redirect('add_product_page')
            if not is_valid_price(price):
                messages.error(request, 'Price should be a positive number')
                return redirect('add_product_page')
            if not is_valid_price(selling_price):
                messages.error(request, 'Price should be a positive number')
                return redirect('add_product_page')
            
            s_stock = request.POST.get('s_stock')
            m_stock = request.POST.get('m_stock')
            l_stock = request.POST.get('l_stock')
            xl_stock = request.POST.get('xl_stock')
            
            if not is_valid_stock(s_stock):
                messages.error(request, 'Stock should be a positive Integer')
                return redirect('add_product_page')
            if not is_valid_stock(m_stock):
                messages.error(request, 'Stock should be a positive Integer')
                return redirect('add_product_page')
            if not is_valid_stock(l_stock):
                messages.error(request, 'Stock should be a positive Integer')
                return redirect('add_product_page')
            if not is_valid_stock(xl_stock):
                messages.error(request, 'Stock should be a positive Integer')
                return redirect('add_product_page')

            description = request.POST.get('description')
            if not is_valid_description(description):
                messages.error(request, 'Invalid Description')
                return redirect('add_product_page')

            image_front = request.FILES.get('image_front')
            if image_front:
                try:
                    # Open the image file
                    img = Image.open(image_front.file)
                    img.verify()  # This will raise an exception if the image is not valid
                except Exception as e:
                    messages.error(request, 'Invalid image file. Please upload a valid image.')
                    return redirect(request.META.get("HTTP_REFERER"))
            image_back = request.FILES.get('image_back')
            extra_image_one = request.FILES.get('extra_image_one')
            extra_image_two = request.FILES.get('extra_image_two')
            if image_back:
                try:
                    # Open the image file
                    img = Image.open(image_back.file)
                    img.verify()  # This will raise an exception if the image is not valid
                except Exception as e:
                    messages.error(request, 'Invalid image file. Please upload a valid image.')
                    return redirect(request.META.get("HTTP_REFERER"))
            if extra_image_one:
                try:
                    # Open the image file
                    img = Image.open(extra_image_one.file)
                    img.verify()  # This will raise an exception if the image is not valid
                except Exception as e:
                    messages.error(request, 'Invalid image file. Please upload a valid image.')
                    return redirect(request.META.get("HTTP_REFERER"))
            if extra_image_two:
                try:
                    # Open the image file
                    img = Image.open(extra_image_two.file)
                    img.verify()  # This will raise an exception if the image is not valid
                except Exception as e:
                    messages.error(request, 'Invalid image file. Please upload a valid image.')
                    return redirect(request.META.get("HTTP_REFERER"))

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
    except:
        return redirect('/404error/')



def edit_product(request, uid):
    # try:
    context = {}
    products = Product.objects.get(uid = uid)
    image = Product_Image.objects.get(product = products)
    categ = products.category
    cat_offer = None  # Initialize cat_offer outside the try block

    try:
        cat_offer = CategoryOffer.objects.get(category=categ)
    except CategoryOffer.DoesNotExist:
        pass  # You can leave this block empty since cat_offer is already initialized to None

    # Set cat_off_percentage directly inside the try block
    cat_off_percentage = cat_offer.percentage if cat_offer else 0
    categories = Category.objects.all()
    current_datetime = datetime.now()
    product_offers = ProductOffer.objects.filter(expiry_date__gt=current_datetime)
    sizes = Size.objects.all()
    size_obj_s = Size.objects.get(size='S')
    size_obj_m = Size.objects.get(size='M')
    size_obj_l = Size.objects.get(size='L')
    size_obj_xl = Size.objects.get(size='XL')

    if request.method == "POST":
        product_name = request.POST.get('product_name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        selling_price = price
        if not is_valid_product_title(product_name):
            messages.error(request, f'{product_name} Not a valid product Name')
            return redirect(request.META.get("HTTP_REFERER"))
        if not is_valid_price(price):
            messages.error(request, 'Price should be a positive number')
            return redirect(request.META.get("HTTP_REFERER"))
        if not is_valid_price(selling_price):
            messages.error(request, 'Price should be a positive number')
            return redirect(request.META.get("HTTP_REFERER"))
        s_stock = request.POST.get('s_stock')
        m_stock = request.POST.get('m_stock')
        l_stock = request.POST.get('l_stock')
        xl_stock = request.POST.get('xl_stock')

        if not is_valid_stock(s_stock):
            messages.error(request, 'Stock should be a positive Integer')
            return redirect('add_product_page')
        if not is_valid_stock(m_stock):
            messages.error(request, 'Stock should be a positive Integer')
            return redirect(request.META.get("HTTP_REFERER"))
        if not is_valid_stock(l_stock):
            messages.error(request, 'Stock should be a positive Integer')
            return redirect(request.META.get("HTTP_REFERER"))
        if not is_valid_stock(xl_stock):
            messages.error(request, 'Stock should be a positive Integer')
            return redirect(request.META.get("HTTP_REFERER"))
        if not is_valid_description(description):
            messages.error(request, 'Invalid Description')
            return redirect(request.META.get("HTTP_REFERER"))
        
        image_front = request.FILES.get('image_front') if 'image_front' in request.FILES else None
        category = request.POST.get('category')
        if image_front:
            try:
                # Open the image file
                img = Image.open(image_front.file)
                img.verify()  # This will raise an exception if the image is not valid
            except Exception as e:
                messages.error(request, 'Invalid image file. Please upload a valid image.')
                return redirect(request.META.get("HTTP_REFERER"))
        
        try:
            offer_name = request.POST.get('offer')
            if offer_name == 'none':
                offer = None
                selling_price = float(price) - (float(price) * float(cat_offer.percentage))/100
                selling_price = float(selling_price)
            else:
                offer = ProductOffer.objects.get(offer_name = offer_name)
                selling_price = float(selling_price) - (float(selling_price) * offer.percentage)/100
                if(cat_off_percentage > offer.percentage):
                    selling_price = float(price) - (float(price) * cat_off_percentage)/100
        except ProductOffer.DoesNotExist:
            offer = None
            selling_price = float(price) - (float(price) * cat_off_percentage)/100
            selling_price = float(selling_price)  # Convert to float if not already
        except Exception as e:
            offer = None
            selling_price = float(price) - (float(price) * cat_off_percentage)/100
            selling_price = float(selling_price)  # Convert to float if not already
        image_back = request.FILES.get('image_back') if 'image_back' in request.FILES else None
        extra_image_one = request.FILES.get('extra_image_one') if 'extra_image_one' in request.FILES else None
        extra_image_two = request.FILES.get('extra_image_two') if 'extra_image_two' in request.FILES else None
        if image_back:
            try:
                # Open the image file
                img = Image.open(image_back.file)
                img.verify()  # This will raise an exception if the image is not valid
            except Exception as e:
                messages.error(request, 'Invalid image file. Please upload a valid image.')
                return redirect(request.META.get("HTTP_REFERER"))
        if extra_image_one:
            try:
                # Open the image file
                img = Image.open(extra_image_one.file)
                img.verify()  # This will raise an exception if the image is not valid
            except Exception as e:
                messages.error(request, 'Invalid image file. Please upload a valid image.')
                return redirect(request.META.get("HTTP_REFERER"))
        if extra_image_two:
            try:
                # Open the image file
                img = Image.open(extra_image_two.file)
                img.verify()  # This will raise an exception if the image is not valid
            except Exception as e:
                messages.error(request, 'Invalid image file. Please upload a valid image.')
                return redirect(request.META.get("HTTP_REFERER"))

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
            products.offer = offer
            products.product_name = product_name
            products.description = description

            
            if image_front is not None:
                products.image_front = image_front
                print('Valid Image Front')
            if image_front is None:
                print('Image is not added')
            
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
            
            
            return redirect(reverse('admin_products'))
            
        except Exception as e:
            messages.error(request, str(e))
            return redirect(request.META.get("HTTP_REFERER"))
            

    context['categories'] = categories
    context['product_offers'] = product_offers
    context['sizes'] = sizes
    context['stock_s'] = Product_Variant.objects.get(product = products, size = size_obj_s).stock
    context['stock_m'] = Product_Variant.objects.get(product = products, size = size_obj_m).stock
    context['stock_l'] = Product_Variant.objects.get(product = products, size = size_obj_l).stock
    context['stock_xl'] = Product_Variant.objects.get(product = products, size = size_obj_xl).stock
    context['product'] = products
    context['image'] = image
    return render(request, 'adminside/editproduct.html', context)
    # except:
    #     return redirect('/404error/')

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
        return redirect('/404error/')

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
        return redirect('/404error/')
    
@admin_required
def edit_category(request, id):
    try:
        context = {}
        category = Category.objects.get(id = id)
        context['categories'] = category
        context['today_date']: date.today().strftime('%Y-%m-%d')

        if request.method == "POST":
            category_name = request.POST.get('category_name')
            category_slug = request.POST.get('category_slug')
            # category_description = request.POST.get('category_description')
            try:
                offer = request.POST.get('offer')
            except:
                offer = 0
            if offer == 'None':
                offer = 0
            elif offer == '':
                offer = 0
            x = 0
            current_datetime = timezone.now()
            tomorrow_datetime = current_datetime + timedelta(days=1)
            try:
                expiry_date = request.POST.get('offer_expiry_date')
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except:
                expiry_date = tomorrow_datetime
                x = 'now'
            if not expiry_date:
                expiry_date = tomorrow_datetime
                x = 'now'
            # if expiry_date and not offer:
            #     messages.error(request, 'Please enter an offer')
            #     return redirect(request.META.get('HTTP_REFERER'))
            if offer and not expiry_date:
                messages.error(request, 'Please select an expiry date')
                return redirect(request.META.get('HTTP_REFERER'))

            try:
                offer = float(offer)
                if not (0 <= offer <= 100):
                    raise ValueError('Offer must be between 0 and 100.')
            except ValueError as ve:
                messages.error(request, str(ve))
                return render(request, 'adminside/editcategory.html', context)

            if Category.objects.filter(category_name__iexact=category_name).exclude(id=id).exists():
                messages.error(request, 'Category with this name already exists.')
                return render(request, 'adminside/editcategory.html', context)

            # Check if a category with the same slug exists
            if Category.objects.filter(category_slug__iexact=category_slug).exclude(id=id).exists():
                messages.error(request, 'Category with this slug already exists.')
                return render(request, 'adminside/editcategory.html', context)

            try:
                category.category_name = category_name
                category.category_slug = category_slug
                category.save()
                if offer == 0:
                    offer = None
                    expiry_date = None
                category_offer, created = CategoryOffer.objects.get_or_create(category=category)
                category_offer.percentage = offer

                # if expiry_date is not None and x == 0:
                category_offer.expiry_date = expiry_date

                category_offer.save()

                print('Category and CategoryOffer saved successfully.')
                products = Product.objects.filter(category = category)
                for product in products:
                    print(product)
                    if product.offer:
                        # print('xxxxxxxxxxxxxxxxxxxxxxxxxxx')
                        product_offer = product.offer.percentage
                    else:
                        # print('oooooooooooooooooooooooooooooooooooo')
                        product_offer = 0
                    # print('1111111111111111111111111')
                    print(product_offer)
                    print('now price ==', product.selling_price)
                    if category_offer.percentage == None:
                        product.selling_price = (float(product.price) - (float(product.price)*float(product_offer)/100))
                    elif product_offer < category_offer.percentage:
                        product.selling_price = (float(product.price) - (float(product.price)*float(category_offer.percentage)/100))
                    else:
                        product.selling_price = (float(product.price) - (float(product.price)*float(product_offer)/100))
                    print('new price == ', product.selling_price)
                    print("---------------------",product.selling_price)
                    product.save()
                if x == 'now':
                    category_offer.expiry_date = None
                return redirect(reverse('categories'))
            except Exception as e:
                return HttpResponse(e)

        return render(request, 'adminside/editcategory.html', context)
    except:
        return redirect('/404error/')

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
        return redirect('/404error/')
    

@admin_required
def orders(request):
    try:
        context = {}
        all_orders = Order.objects.all().order_by('-created_at')

        # Pagination
        items_per_page = 10
        paginator = Paginator(all_orders, items_per_page)
        page = request.GET.get('page')

        try:
            orders = paginator.page(page)
        except PageNotAnInteger:
            # If the page parameter is not an integer, deliver the first page.
            orders = paginator.page(1)
        except EmptyPage:
            # If the page is out of range (e.g., 9999), deliver the last page of results.
            orders = paginator.page(paginator.num_pages)

        context['orders'] = orders
        return render(request, 'adminside/orders.html', context)
    except:
        return redirect('/404error/')


@admin_required
def order_info(request, uid):
    try:
        context = {}
        order = Order.objects.get(uid = uid)
        order_items = OrderItems.objects.filter(order = order)
        if request.method == 'POST':
            new_status = request.POST.get('status', None)
            if new_status:
                order.status = new_status
                order.save()
            return redirect(request.META.get('HTTP_REFERER'))
        context['order'] = order
        context['order_items'] = order_items
        return render(request, 'adminside/orderinfo.html', context)
    except:
        return redirect('/404error/')


@admin_required
def coupons(request):
    try:
        context = {}

        # Order by expiry date in ascending order, expired coupons go last
        all_coupons = Coupon.objects.annotate(
            is_expired=Case(
                When(expiry_date__lt=timezone.now(), then=Value(True)),
                default=Value(False),
                output_field=models.BooleanField(),
            )
        ).order_by('is_expired', 'expiry_date')

        # Pagination
        items_per_page = 10
        paginator = Paginator(all_coupons, items_per_page)
        page = request.GET.get('page')

        try:
            coupons = paginator.page(page)
        except PageNotAnInteger:
            # If the page parameter is not an integer, deliver the first page.
            coupons = paginator.page(1)
        except EmptyPage:
            # If the page is out of range (e.g., 9999), deliver the last page of results.
            coupons = paginator.page(paginator.num_pages)

        context['coupons'] = coupons
        now = timezone.now()
        context['now'] = now
        return render(request, 'adminside/coupons.html', context)
    except:
        return redirect('/404error/')

def unlist_coupon(request, uid):
    try:
        coupon = Coupon.objects.get(uid = uid)
        coupon.unlisted = True
        coupon.save()
        return redirect(request.META.get('HTTP_REFERER'))
    except:
        return redirect('/404error/')

def list_coupon(request, uid):
    try:
        coupon = Coupon.objects.get(uid = uid)
        coupon.unlisted = False
        coupon.save()
        return redirect(request.META.get('HTTP_REFERER'))
    except:
        return redirect('/404error/')


def is_valid_coupon_name(coupon_name):
    try:
        if isinstance(coupon_name, str) and len(coupon_name) >= 5 and coupon_name.isalnum():
            return True
        else:
            return False
    except:
        return redirect('/404error/')
    

def is_valid_minimum_amount(minimum_amount):
    try:
        minimum_amount = int(minimum_amount)
        if minimum_amount >= 0:
            return True
        else:
            return False
    except ValueError:
        return False
    

def is_valid_discount_percentage(discount_percentage):
    try:
        discount_percentage = float(discount_percentage)
        if 0 <= discount_percentage <= 100:
            return True
        else:
            return False
    except ValueError:
        return False


def add_coupon(request):
    try:
        if request.method == 'POST':
            code = request.POST['coupon_code']
            date = request.POST['expiry_date']
            minimum_amount = request.POST['minimum_amount']
            discount_percentage = request.POST['discount_percentage']
            if not is_valid_coupon_name(code):
                messages.error(request, 'Invalid coupon name')
                return redirect(request.META.get('HTTP_REFERER'))
            

            if not is_valid_minimum_amount(minimum_amount):
                messages.error(request, 'Minimum amount should be an integer above zero')
                return redirect(request.META.get('HTTP_REFERER'))

            if not is_valid_discount_percentage(discount_percentage):
                messages.error(request, 'Discount percentage should be an integer between 0 and 100')
                return redirect(request.META.get('HTTP_REFERER'))
            
            try:
                existing_coupon = Coupon.objects.get(code = code)
                messages.error(request, 'Coupon already exists')
                return redirect(request.META.get('HTTP_REFERER'))
            except:
                pass
            
            coupon = Coupon.objects.create(
                code = code,
                expiry_date = date,
                minimum_amount = minimum_amount,
                discount_percentage = discount_percentage
            )
            return redirect('coupons')
        return render (request, 'adminside/addcoupon.html')
    except:
        return redirect('/404error/')


def edit_coupon(request, uid):
    try:
        context = {}
        coupon = Coupon.objects.get(uid = uid)
        if request.method == 'POST':
            code = request.POST['coupon_code']
            date = request.POST['expiry_date']
            minimum_amount = request.POST['minimum_amount']
            discount_percentage = request.POST['discount_percentage']
            if not is_valid_coupon_name(code):
                messages.error(request, 'Invalid coupon name')
                return redirect(request.META.get('HTTP_REFERER'))

            if not is_valid_minimum_amount(minimum_amount):
                messages.error(request, 'Minimum amount should be an integer above zero')
                return redirect(request.META.get('HTTP_REFERER'))

            if not is_valid_discount_percentage(discount_percentage):
                messages.error(request, 'Discount percentage should be an integer between 0 and 100')
                return redirect(request.META.get('HTTP_REFERER'))
            try:
                existing_coupon = Coupon.objects.exclude(uid=uid).get(code=code)
                messages.error(request, 'Coupon already exists')
                return redirect(request.META.get('HTTP_REFERER'))
            except:
                pass
            
            coupon.code = code
            coupon.expiry_date = date
            coupon.minimum_amount = minimum_amount
            coupon.discount_percentage = discount_percentage
            coupon.save()
            return redirect('coupons')
            
        context['coupon'] = coupon
        return render(request, 'adminside/editcoupon.html', context)
    except:
        return redirect('/404error/')


def product_offers(request):
    try:
        context = {}
        product_offers = ProductOffer.objects.all()
        if request.method == 'POST':
            offer_name = request.POST['offer_name']
            discount = request.POST['discount']
            expiry_date = request.POST['expiry_date']
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            try:
                offer = ProductOffer.objects.get(offer_name = offer_name)
                messages.error(request, 'Offer already exists')
            except:
                pass
            ProductOffer.objects.create(offer_name=offer_name, percentage = discount, expiry_date = expiry_date)
            return redirect(request.META.get('HTTP_REFERER'))
        context['product_offers'] = product_offers
        return render(request, 'adminside/productoffers.html', context)
    except:
        return redirect('/404error/')


def edit_offer(request, uid):
    try:
        context = {}
        offer = ProductOffer.objects.get(uid = uid)
        if request.method == 'POST':
            offer_name = request.POST['offer_name']
            discount = request.POST['discount']
            try:
                discount = int(discount)
                if not (0 <= discount <= 100):
                    raise ValueError('Discount must be between 0 and 100.')
            except ValueError as ve:
                messages.error(request, str(ve))
                return redirect(request.META.get('HTTP_REFERER'))
            expiry_date = request.POST['offer_expiry_date']
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            offer.offer_name = offer_name
            offer.percentage = discount
            offer.expiry_date = expiry_date
            offer.save()
            return redirect('product_offers')
        context['offer'] = offer
        return render(request, 'adminside/editoffer.html', context)
    except:
        return redirect('/404error/')


def delete_offer(request, uid):
    try:
        offer = ProductOffer.objects.get(uid = uid)
        if offer.is_listed:
            offer.is_listed = False
        else:
            offer.is_listed = True
        offer.save()
        return redirect(request.META.get('HTTP_REFERER'))
    except:
        return redirect('/404error/')
