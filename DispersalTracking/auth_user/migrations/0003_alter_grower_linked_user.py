# Generated by Django 5.1.6 on 2025-03-25 03:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_user', '0002_remove_grower_name_grower_first_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='grower',
            name='linked_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='growers', to=settings.AUTH_USER_MODEL),
        ),
    ]
