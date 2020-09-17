from django.contrib import admin
from profiles.models import User, DeveloperProfile, DriverProfile, AdminProfile

admin.site.register(User)
admin.site.register(DeveloperProfile)

admin.site.register(DriverProfile)
admin.site.register(AdminProfile)

# Register your models here.
