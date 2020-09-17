import factory
from factory.django import DjangoModelFactory

from profiles.models import User, AdminProfile, DeveloperProfile, DriverProfile


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    password = "test"
    is_superuser = False
    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name_female')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    is_staff = False
    is_active = True


class AdminProfileFactory(DjangoModelFactory):
    class Meta:
        model = AdminProfile

    user = factory.SubFactory(UserFactory)


class DeveloperProfileFactory(DjangoModelFactory):
    class Meta:
        model = DeveloperProfile

    user = factory.SubFactory(UserFactory)


class DriverProfileFactory(DjangoModelFactory):
    class Meta:
        model = DriverProfile

    user = factory.SubFactory(UserFactory)
