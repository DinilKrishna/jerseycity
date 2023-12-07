import random
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
    referance_code = models.CharField(max_length= 12, default='')
    refered = models.CharField(max_length=12,default="",blank=True,null=True)
    

    def __str__(self) -> str:
        return self.user.username
    
    def generate_reference_code(self):
        while True:
            unique_code = random.randint(1000000, 9999999)  # Generates a 7-digit random number
            if not UserProfile.objects.filter(referance_code=unique_code).exists():
                self.referance_code = f"REF{unique_code}"
                break
    
    def save(self, *args, **kwargs):
        if not self.referance_code:
            self.generate_reference_code()
        super(UserProfile, self).save(*args, **kwargs)
        
