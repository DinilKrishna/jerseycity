# Generated by Django 4.2.6 on 2023-12-11 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_productoffer_product_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='productoffer',
            name='is_listed',
            field=models.BooleanField(default=True),
        ),
    ]