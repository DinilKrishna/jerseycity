import random
from django.db import models
from django.dispatch import receiver
from base.models import BaseModel
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from userauth.models import UserProfile
from products.models import Product, Size

# Create your models here.

class Address(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=10)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    unlisted = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.first_name} : {self.pincode}"
    

class Payment_Method(BaseModel):
    method = models.CharField( max_length=50)
    
    def __str__(self) -> str:
        return self.method


class Coupon(BaseModel):
    code = models.CharField(max_length=10)
    expiry_date = models.DateTimeField()
    discount_percentage = models.IntegerField()
    # maximum_use = models.IntegerField(default=1)
    minimum_amount = models.IntegerField(default = 60)
    unlisted = models.BooleanField(default=False)


class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    payment_method = models.ForeignKey(Payment_Method, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through="OrderItems")
    bill_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_to_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    razor_pay_id = models.CharField(blank=True, null=True, max_length=100)
    status = models.CharField(max_length=50, null = True, blank = True)
    payed = models.BooleanField(default=False)
    coupon = models.ForeignKey(Coupon,on_delete= models.CASCADE, null=True, blank=True)
    # return_product = models.BooleanField(default=False)
    

#     wallet_applied = models.BooleanField(default=False)
    

    def calculate_bill_amount(self):
        # Calculate the bill_amount as the sum of sub_total for all OrderItems
        total = sum(item.sub_total for item in self.orderitems.all())
        self.bill_amount = total 
        self.save()



class OrderItems(BaseModel):
    order = models.ForeignKey(Order, related_name='orderitems', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discounted_subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=40, default="Pending")
    is_paid = models.BooleanField(default=False)







class Wallet(BaseModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="wallet")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

