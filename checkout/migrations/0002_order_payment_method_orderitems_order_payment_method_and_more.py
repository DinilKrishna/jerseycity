# Generated by Django 4.2.6 on 2023-11-24 04:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_cart_cartitems_cart_product_cart_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('checkout', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order_id', models.PositiveIntegerField(blank=True, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=10, null=True)),
                ('city', models.CharField(blank=True, max_length=50, null=True)),
                ('district', models.CharField(blank=True, max_length=50, null=True)),
                ('state', models.CharField(blank=True, max_length=50, null=True)),
                ('pincode', models.CharField(blank=True, max_length=6, null=True)),
                ('bill_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('amount_to_pay', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('razor_pay_id', models.CharField(blank=True, max_length=100, null=True)),
                ('address', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='checkout.address')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Payment_Method',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('method', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OrderItems',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('quantity', models.IntegerField()),
                ('product_price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('sub_total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('discounted_subtotal', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('status', models.CharField(default='Pending', max_length=40)),
                ('is_paid', models.BooleanField(default=False)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orderitems', to='checkout.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product')),
                ('size', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.size')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='checkout.payment_method'),
        ),
        migrations.AddField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(through='checkout.OrderItems', to='products.product'),
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
