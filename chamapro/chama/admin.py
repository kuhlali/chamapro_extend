from django.contrib import admin
from .models import Chama, Investment, Loan


# Register your models here.
admin.site.register(Chama)
admin.site.register(Investment)
admin.site.register(Loan)