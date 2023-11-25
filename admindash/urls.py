
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.admin_login_page, name="admin_login_page"),
    path('admin_login/', views.admin_login, name="admin_login"),
    path('admin_log_out/', views.admin_log_out, name="admin_log_out"),
    path('admin_dash/',views.admin_dashboard, name='admin_dashboard'),

    path('admin_products/',views.admin_products, name='admin_products'),   
    path('add_product_page/',views.add_product_page, name='add_product_page'),
    path('add_product/',views.add_product, name='add_product'),
    # path('edit_product_page/',views.edit_product_page, name='edit_product_page'),
    path('edit_product/<uid>',views.edit_product, name='edit_product'),
    path('delete_product/<uid>',views.delete_product, name='delete_product'),

    path('categories/',views.categories, name='categories'),
    path('edit_category/<id>',views.edit_category, name='edit_category'),
    path('delete_category/<id>',views.delete_category, name='delete_category'),

    path('users/',views.users, name='users'),
    path('block_user/<uid>',views.block_user, name='block_user'),
    path('user_details/',views.user_details, name='user_details'),

    path('orders/',views.orders, name='orders'),
    path('order_info/<uid>',views.order_info, name='order_info'),
    
]
