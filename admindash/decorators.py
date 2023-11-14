from django.shortcuts import redirect
from functools import wraps
from django.urls import reverse
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Access denied. You must be a staff or admin user.")
            return redirect(reverse('admin_login_page')) 
    return _wrapped_view