from django.db import models
from auth_user.models import Grower
from django.core.exceptions import ValidationError
from django.utils import timezone
from auth_user.models import User

class FarmLocation(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, default=None)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, default=None)
    description = models.TextField(blank=True, null=True)
    grower = models.ForeignKey(Grower, related_name='farm_locations', null=False, blank=True, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.name
    
class LivestockFamilyManager(models.Manager):
    def get_available_hens(self):
        return self.filter(gender='Female', family_female__isnull=True)
    
class LivestockFamily(models.Model):
    family_id = models.CharField(primary_key=True, max_length=155, unique=True)
    cage_location = models.CharField(max_length=100)
    date_recorded = models.DateField(default=timezone.now)
    brood_generation_number = models.IntegerField(null=True, blank=True, default=1)
    max_roosters = models.IntegerField(default=1)  # Admin configurable
    max_hens = models.IntegerField(default=8)      # Admin configurable

    def clean(self):    
        roosters = Livestock.objects.filter(livestock_family=self, gender='Male').count()
        hens = Livestock.objects.filter(livestock_family=self, gender='Female').count()

        if roosters >= self.max_roosters:
            raise ValidationError(f"Only {self.max_roosters} rooster(s) allowed per family.")
        if hens >= self.max_hens:
            raise ValidationError(f"Only {self.max_hens} hens allowed per family.")

        tag_colors = Livestock.objects.filter(livestock_family=self).values_list('tag_color', flat=True).distinct()
        if len(tag_colors) > 1:
            raise ValidationError("All chickens in a family must have the same tag color.")
    
    def __str__(self):
        return self.family_id  # ✅ Only displays the ID

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
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
    profile_picture = models.ImageField(upload_to='livestock_images/', null=True, blank=True)

    def __str__(self):
        return self.ls_code

    def update_age(self):
        if self.date_recorded and self.age_in_days is not None:
            self.age_in_days += (timezone.now().date() - self.date_recorded).days
            self.save()

    
class Dispersal(models.Model):
    dispersal_date = models.DateField()
    families_dispersed = models.ManyToManyField(LivestockFamily)
    farmlocation = models.ForeignKey(FarmLocation, on_delete=models.CASCADE)

    def clean(self):
        if self.dispersal_date > timezone.now().date():
            raise ValidationError("Dispersal date cannot be in the future.")

class Message(models.Model):
    name = models.CharField(max_length=100, blank=False)  # Name with spaces allowed
    email = models.EmailField()
    message = models.CharField(max_length=225)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Optional user link
    message_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the message was created

    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    
class SystemSettings(models.Model):
    max_roosters = models.IntegerField(default=1, help_text="Max roosters per family")
    max_hens = models.IntegerField(default=8, help_text="Max hens per family")

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        if SystemSettings.objects.exists() and not self.pk:
            raise ValidationError("There can only be one SystemSettings instance.")
        super(SystemSettings, self).save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        return cls.objects.first() or cls.objects.create()
