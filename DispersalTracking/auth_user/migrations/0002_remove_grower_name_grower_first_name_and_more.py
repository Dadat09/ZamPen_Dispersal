# Generated by Django 5.1.6 on 2025-03-23 03:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_user', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grower',
            name='Name',
        ),
        migrations.AddField(
            model_name='grower',
            name='first_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='grower',
            name='last_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='grower',
            name='linked_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='growers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='grower',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_growers', to=settings.AUTH_USER_MODEL),
        ),
    ]
