# Generated by Django 4.2.6 on 2023-12-02 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0012_remove_coupon_max_use'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='maximum_use',
            field=models.IntegerField(default=1),
        ),
    ]