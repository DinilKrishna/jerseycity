from django.utils import timezone
from django.db import models
from base.models import BaseModel
from django.dispatch import receiver
from django.db.models.signals import post_save
from PIL import Image

from userauth.models import UserProfile


# Create your models here.


class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    offer = models.IntegerField(null = True, blank=True)
    category_slug = models.SlugField(unique=True, null=True, blank=True)
    is_listed = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.category_name
    

class Size(models.Model):
    size = models.CharField(max_length=6)

    def __str__(self) -> str:
        return self.size
    

class ProductOffer(BaseModel):
    offer_name = models.TextField(max_length= 15)
    percentage = models.IntegerField(default=0)
    expiry_date = models.DateField(default=timezone.now)
    is_listed = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.offer_name
    

class Product(BaseModel):
    product_name = models.CharField(max_length=100)
    description = models.TextField()
    image_front = models.ImageField(upload_to='product_images')
    price = models.DecimalField(max_digits=7, decimal_places=2)
    selling_price = models.DecimalField(max_digits=7, decimal_places=2, default=0.0)
    category = models.ForeignKey(Category, related_name='category_of_product', on_delete=models.CASCADE)
    is_selling = models.BooleanField(default=True)
    offer = models.ForeignKey(ProductOffer, on_delete=models.CASCADE, null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)


    def __str__(self):
        return self.product_name
    

class Product_Variant(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock = models.IntegerField(default=0)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    sold = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.product_name} : {self.size}"
    

class Product_Image(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    image_back = models.ImageField(upload_to='product_images')
    extra_image_one = models.ImageField(upload_to='product_images')
    extra_image_two = models.ImageField(upload_to='product_images')

    def __str__(self):
        return self.product.product_name
    

@receiver(post_save, sender='products.Product_Image')
def resize_images(sender, instance, **kwargs):
    #Open the images
    image_front = Image.open(instance.product.image_front.path)
    image_back = Image.open(instance.image_back.path)
    extra_image_one = Image.open(instance.extra_image_one.path)
    extra_image_two = Image.open(instance.extra_image_two.path)

    #Resize the images
    image_front = image_front.resize((840, 840), Image.LANCZOS)
    image_back = image_back.resize((840, 840), Image.LANCZOS)
    extra_image_one = extra_image_one.resize((840,840), Image.LANCZOS)
    extra_image_two = extra_image_two.resize((840,840), Image.LANCZOS)

    #Save the images
    image_front.save(instance.product.image_front.path)
    image_back.save(instance.image_back.path)
    extra_image_one.save(instance.extra_image_one.path)
    extra_image_two.save(instance.extra_image_two.path)


class Cart(BaseModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    product = models.ManyToManyField(Product, through="CartItems")
    coupon = models.ForeignKey("checkout.Coupon",on_delete= models.CASCADE, null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.user.user.username} : Cart'
        
class CartItems(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
                                            
    
    def __str__(self) -> str:
        return f'{self.quantity} x {self.product.product_name} in Cart'

    def calculate_sub_total(self):
        return self.product.selling_price * self.quantity
    

class Wishlist(BaseModel):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    product = models.ManyToManyField(Product, through="WishlistItems")

    def __str__(self) -> str:
        return f'{self.user.user.username} : Wishlist'
    
class WishlistItems(BaseModel):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
                                            
    
    def __str__(self) -> str:
        return f'{self.wishlist.user.user.first_name} x {self.product.product_name} in Wishlist'
    

class Return(BaseModel):
    order = models.ForeignKey("checkout.Order", on_delete=models.CASCADE)
    description = models.TextField()


class CategoryOffer(BaseModel):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name="category_offer")
    percentage = models.IntegerField(null=True, blank = True)
    expiry_date = models.DateField(null = True, blank=True)

    def is_valid(self):
        return self.expiry_date >= timezone.now().date()

    def __str__(self):
        return f"{self.category.category_name} Offer"





