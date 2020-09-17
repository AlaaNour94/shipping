from django.db import models
from django.contrib.auth.models import AbstractUser
from polymorphic.models import PolymorphicModel

from shipment.models import Shipment


class User(AbstractUser):
    ADMIN = 'ADMIN'
    DRIVER = 'DRIVER'
    DEVELOPER = 'DEVELOPER'

    PROFILE_CHOICES = (
        (ADMIN, ADMIN),
        (DRIVER, DRIVER),
        (DEVELOPER, DEVELOPER),
    )

    role = models.CharField(max_length=30, choices=PROFILE_CHOICES)


class AdminProfile(PolymorphicModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    def get_all_shipments(self):
        """Return a Queryset of all the Shipment objects in the system."""

        return Shipment.objects.all()


class DeveloperProfile(AdminProfile):
    def get_all_shipments(self):
        """Return a Queryset of the Shipment objects created by this developer."""

        return Shipment.objects.filter(owner=self.user)


class DriverProfile(AdminProfile):
    def get_all_shipments(self):
        """Return a Queryset of the Shipment objects that will deliverd by thois driver."""

        return Shipment.objects.filter(driver=self.user)
