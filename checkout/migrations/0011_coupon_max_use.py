# Generated by Django 4.2.6 on 2023-12-02 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0010_remove_order_return_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='max_use',
            field=models.IntegerField(default=1),
        ),
    ]
