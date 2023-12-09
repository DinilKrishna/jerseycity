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
    minimum_amount = models.IntegerField(default = 60)
    unlisted = models.BooleanField(default=False)
    users = models.ManyToManyField(UserProfile, blank=True)


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

    def save(self, *args, **kwargs):
        # Check if the instance has already been saved (update operation)
        if self.pk is not None:
            # Retrieve the previous state of the instance
            old_wallet = Wallet.objects.get(pk=self.pk)
            
            # Determine the action based on the change in amount
            if self.amount > old_wallet.amount:
                action = "Credited"
            elif self.amount < old_wallet.amount:
                action = "Debited"
            else:
                action = None

            # Create a new entry in WalletHistory
            if action:
                WalletHistory.objects.create(wallet=self, amount=abs(self.amount - old_wallet.amount), action=action)

        super(Wallet, self).save(*args, **kwargs)


class WalletHistory(BaseModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="wallet_history")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    action = models.CharField(max_length=10)


