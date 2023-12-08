# Generated by Django 4.2.6 on 2023-12-08 10:21

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_return'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='offer',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='CategoryOffer',
            fields=[
                ('uid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('percentage', models.IntegerField(default=0)),
                ('expiry_date', models.DateField()),
                ('category', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='category_offer', to='products.category')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
