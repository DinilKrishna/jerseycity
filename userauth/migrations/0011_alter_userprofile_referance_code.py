# Generated by Django 4.2.6 on 2023-12-07 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0010_userprofile_referance_code_userprofile_refered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='referance_code',
            field=models.CharField(default='', max_length=12),
        ),
    ]
