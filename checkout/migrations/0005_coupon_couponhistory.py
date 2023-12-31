# Generated by Django 4.2.6 on 2023-11-29 06:11

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0009_alter_userprofile_profile_image'),
        ('checkout', '0004_order_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=10)),
                ('expiry_date', models.DateTimeField()),
                ('discount_percentage', models.IntegerField()),
                ('maximum_use', models.IntegerField(default=1)),
                ('minimum_amount', models.IntegerField(default=1000)),
                ('unlisted', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CouponHistory',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='checkout.coupon')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='userauth.userprofile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
