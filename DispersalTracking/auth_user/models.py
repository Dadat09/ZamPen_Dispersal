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

    def save(self, *args, **kwargs):
        # If a user is linked, set is_farmer = True without overwriting other fields
        if self.Name:
            User.objects.filter(id=self.Name.id).update(is_farmer=True)

        super().save(*args, **kwargs)  # Call the original save method

    def __str__(self):
        return f"{self.Name.first_name} {self.Name.last_name}" if self.Name else "No Name"



class Grower(models.Model):
    linked_user = models.ForeignKey(User, related_name="growers", blank=True, null=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    ContactNo = models.CharField(max_length=20, blank=True, null=True)
    Email = models.EmailField(max_length=100, blank=True, null=True)
    barangay = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=100, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    zipcode = models.CharField(max_length=5, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name="created_growers", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else "Unnamed Grower"
 