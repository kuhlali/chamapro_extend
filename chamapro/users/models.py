from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Add custom fields as needed
    phone_number = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return self.email or self.username