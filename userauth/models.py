from django.db import models
from base.models import BaseModel
from django.contrib.auth.models import User
from .signals import *


# Create your models here.

class UserProfile(BaseModel):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="userprofile")
    is_verified = models.BooleanField(default=False)
    profile_image = models.ImageField(
        null=True,
        default= "userprofile/dummy.jpeg",  # Relative path to the default image
        upload_to='userprofile'
    )
    is_blocked = models.BooleanField(default=False)



    def __str__(self) -> str:
        return self.user.username
        
