import factory
from factory.django import DjangoModelFactory

from profiles.fixtures_factory import UserFactory
from shipment.models import Shipment


class ShipmentFactory(DjangoModelFactory):
    class Meta:
        model = Shipment

    title = factory.Faker('word')
    receiver_name = factory.Faker('first_name')
    receiver_address = factory.Faker('word')
    receiver_country = factory.Faker('word')
    weight = 5
    tracking_id = factory.Faker('word')
    lat = factory.Faker('latitude')
    lon = factory.Faker('longitude')
    owner = factory.SubFactory(UserFactory)
    driver = factory.SubFactory(UserFactory)
