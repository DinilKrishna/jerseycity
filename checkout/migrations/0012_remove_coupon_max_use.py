# Generated by Django 4.2.6 on 2023-12-02 07:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0011_coupon_max_use'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='max_use',
        ),
    ]
