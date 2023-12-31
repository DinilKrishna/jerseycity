# Generated by Django 4.2.6 on 2023-11-10 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0005_alter_userprofile_profile_image'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='email_verified',
            new_name='is_verified',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='otp',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
