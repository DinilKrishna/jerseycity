# Generated by Django 4.2.6 on 2023-12-07 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0009_alter_userprofile_profile_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='referance_code',
            field=models.CharField(default='None', max_length=12),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='refered',
            field=models.CharField(blank=True, default='', max_length=12, null=True),
        ),
    ]
