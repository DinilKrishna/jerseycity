# Generated by Django 4.2.6 on 2023-12-04 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0009_alter_userprofile_profile_image'),
        ('checkout', '0016_remove_coupon_user_profile_coupon_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='users',
            field=models.ManyToManyField(blank=True, to='userauth.userprofile'),
        ),
    ]
