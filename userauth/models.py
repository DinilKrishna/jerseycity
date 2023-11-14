import random
from django.db import models
from django.shortcuts import redirect
from base.models import BaseModel
from django.http import HttpResponse
from django.contrib.auth.models import User
# from django.db.models import functions
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from django.utils import timezone
from .signals import *
# from datetime import timedelta 
# import random

# Create your models here.

class UserProfile(BaseModel):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    otp = models.CharField(max_length=6, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(
        null=True,
        default="userprofile/dummy_profile.jpg",  # Relative path to the default image
        upload_to='userprofile'
    )
    is_blocked = models.BooleanField(default=False)
    # email_token_created_at = models.DateTimeField(default=timezone.now)


    def __str__(self) -> str:
        return self.user.username
        
# Signal to send an email for OTP when a new User is created
@receiver(post_save, sender=User)
def send_email_token(sender, instance, created, **kwargs):
    try:
        if created and not instance.is_staff:
            UserProfile.objects.create(user=instance)
            random_num = random.randint(1000, 9999)
            otp = random_num
            user_profile = instance.userprofile
            user_profile.otp = otp
            user_profile.email_token_created_at = timezone.now()
            user_profile.save()
            print('The OTP is ', otp)
            send_otp_email(instance.email, otp, instance.first_name)
            # return redirect('verify_otp', uid=instance.userprofile.user.id, otp_token=otp)
    except Exception as e:
        return HttpResponse(e)