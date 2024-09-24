from django.db import models
from auth_user.models import Grower
from django.core.exceptions import ValidationError
from django.utils import timezone

class FarmLocation(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=False, blank=True, default=0.0)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=False, blank=True, default=0.0)
    description = models.TextField(blank=True, null=True)
    grower = models.ForeignKey(Grower, related_name='farm_locations', null=False, blank=True, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.name
    
class LivestockFamilyManager(models.Manager):
    def get_available_hens(self):
        return self.filter(gender='Female', family_female__isnull=True)
    
class LivestockFamily(models.Model):
    family_id = models.CharField(primary_key=True, max_length=155, null=False)
    cage_location = models.CharField(max_length=100)
    date_recorded = models.DateField(default=timezone.now)
    brood_generation_number = models.IntegerField(null=True, blank=True, default=1)
    objects = LivestockFamilyManager()

    def __str__(self):
        return f"Family {self.family_id} at {self.cage_location}"

class Livestock(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]

    ls_code = models.CharField(max_length=50, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    age_in_days = models.IntegerField()
    generation = models.IntegerField()
    batch_no = models.IntegerField()
    tag_color = models.CharField(max_length=50)
    date_recorded = models.DateField(default=timezone.now)
    livestock_family = models.ForeignKey('LivestockFamily', on_delete=models.CASCADE, null=True, blank=True)
    objects = models.Manager()  # The default manager
    chicken_family_objects = LivestockFamilyManager()  # The custom manager.

    def __str__(self):
        return self.ls_code

    def update_age(self):
        if self.date_recorded:
            current_age = (timezone.now().date() - self.date_recorded).days
            self.age_in_days = current_age
            self.save()

    
class Dispersal(models.Model):
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE)
    dispersal_date = models.DateField()
    chickens_dispersed = models.ManyToManyField(Livestock)
    farmlocation = models.ForeignKey(FarmLocation, on_delete=models.CASCADE)

    def __str__(self):
        return f"Dispersed to {self.grower} on {self.dispersal_date}"

    def clean(self):
        if self.dispersal_date > timezone.now().date():
            raise ValidationError("Dispersal date cannot be in the future.")

class Messages(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)  
    email = models.EmailField(max_length=254)  
    subject = models.CharField(max_length=100, blank=True, null=True) 
    message = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)  

    class Meta:
        verbose_name_plural = "Messages"  
        ordering = ['-created_at'] 

    def __str__(self):
        return f"Message from {self.name or 'Anonymous'} ({self.email})"
