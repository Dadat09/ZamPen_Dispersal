from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    is_farmer = models.BooleanField(default=False)
    is_grower = models.BooleanField(default=False)

class Farmer(models.Model):
    Name = models.ForeignKey(User, related_name="+", blank=True, null=True, on_delete=models.CASCADE)
    ContactNo = models.CharField(max_length=20, blank=True, null=True)
    Email = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)

class Grower(models.Model):
    Name = models.ForeignKey(User, related_name="+", blank=True, null=True, on_delete=models.CASCADE)
    ContactNo = models.CharField(max_length=20, blank=True, null=True)
    Email = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    geolat = models.FloatField(blank=True, null=True)
    geolong = models.FloatField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)