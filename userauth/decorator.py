from django.shortcuts import redirect
from functools import wraps
from django.urls import reverse

def login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff is False and request.user.userprofile:
            return view_func(request, *args, **kwargs)
        else:
            return redirect(reverse('login_page'))  # Replace 'logining' with your admin login URL
    return _wrapped_view