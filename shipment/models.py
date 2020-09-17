import uuid
import pdfkit
from datetime import timedelta, datetime
from geopy import distance
from jinja2 import Environment, FileSystemLoader
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from eventful.models import Event
from .estimation_model import predict


def generate_tracking_id():
    return str(uuid.uuid4()).replace('-', '')


class Shipment(models.Model):
    PENDING = 'PENDING'
    SCHEDULED = "SCHEDULED"
    PREPARED = "PREPARED"
    DELIVERED = "DELIVERED"

    STATES_CHOCIES = (
        (PENDING, PENDING),
        (SCHEDULED, SCHEDULED),
        (PREPARED, PREPARED),
        (DELIVERED, DELIVERED),
    )

    driver = models.ForeignKey(settings.AUTH_USER_MODEL,
                               null=True,
                               blank=True,
                               on_delete=models.DO_NOTHING)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='shipments',
                              null=True,
                              blank=True,
                              on_delete=models.DO_NOTHING)

    title = models.CharField(max_length=250)
    receiver_name = models.CharField(max_length=250)
    receiver_country = models.CharField(max_length=60)
    receiver_address = models.CharField(max_length=300)
    estimated_shipping_date = models.DateField(null=True)
    scheduled_at = models.DateField(null=True)
    weight = models.FloatField()
    lat = models.DecimalField(max_digits=12, decimal_places=8)
    lon = models.DecimalField(max_digits=12, decimal_places=8)
    tracking_id = models.CharField(max_length=35, unique=True, default=generate_tracking_id)
    state = models.CharField(max_length=15, choices=STATES_CHOCIES, default=PENDING)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def schedule(self):
        """
        Schedual the shipment delivery
        This will change it's state to `SCHEDULED`, also will calculate the estimated delivery date

        Args:
            self: The shipment object

        Returns:
            None
        """

        self.check_state_transition(self.SCHEDULED)
        self.state = self.SCHEDULED
        self.scheduled_at = datetime.now()
        self.estimated_shipping_date = self.estimate_delivery_date()
        self.save()

    def update_state(self, state):
        """
        Change the state of the shipment.

        Args:
            self: The shipment object
            state: the new state of the shipment

        Returns:
            None

        Raises:
            ValidationError: if the transition can not happend.
        """

        state = state.upper()
        self.check_state_transition(state)
        self.state = state
        self.save()
        Event.dispatch("SHIPMENT_STATE_CHANGED", self.owner_id, self.to_dict())

    def check_state_transition(self, final_state):
        """
        Check if state transition is valid

        Args:
            self: The shipment object
            final_state: the new state of the shipment

        Returns:
            True: if the transition can happen.

        Raises:
            ValidationError: if the transition can not happend.
        """

        state_graph = {
            self.PENDING: [self.SCHEDULED],
            self.SCHEDULED: [self.PREPARED],
            self.PREPARED: [self.DELIVERED],
            self.DELIVERED: []
        }
        if final_state not in state_graph[self.state]:
            raise ValidationError(f"Cannot change state from {self.state} to {final_state}")
        return True

    def get_label(self):
        """
        Return the pdf representation of this shipment

        Args:
            self: The shipment object

        Returns:
            Byte: the Byte representation of the shipment label in pdf format.
        """

        file_loader = FileSystemLoader('shipment/templates')
        env = Environment(loader=file_loader)
        template = env.get_template('label.html')

        str_temp = template.render(**self.to_dict())
        return pdfkit.from_string(str_temp, False)

    def estimate_delivery_date(self):
        """
        Estimate the delivery date of the shipment based on the distance and system load.

        Args:
            self: The shipment object

        Returns:
            DateTime: the estimated delivery date.
        """

        distance = self.calculate_distance()
        number_of_days = predict(distance, .5)
        return datetime.now() + timedelta(days=round(number_of_days))

    def calculate_distance(self):
        """
        Calculate the distance between the shipping store and the destination

        Args:
            self: The shipment object

        Returns:
            Float: the Distance in (KM) from the shipping store to the final destination.
        """

        coordinates_from = [settings.STORE_LAT, settings.STORE_LON]
        coordinates_to = [self.lat, self.lon]
        return distance.distance(coordinates_from, coordinates_to).km

    def to_dict(self):
        """
        Return te Dict representation of the shipment object

        Args:
            self: The shipment object

        Returns:
            DICT: a doctionary representation of the shipment object.
        """

        return {
            "title": self.title,
            "receiver_name": self.receiver_name,
            "receiver_country": self.receiver_country,
            "receiver_address": self.receiver_address,
            "weight": self.weight,
            "state": self.state,
            "tracking_id": self.tracking_id,
            "estimated_shipping_date": self.estimated_shipping_date,
            "scheduled_at": self.scheduled_at,
            "lat": self.lat,
            "lon": self.lon
        }

    class Meta:
        permissions = [("change_shipment_state", "Can change the status of shipments"),
                       ("print_shipment_labels", "Can print labels for given shipments"),
                       ("schedule_shipment", "Can schedule shipments delivery"),
                       ("attach_documents", "Can attache documents to a shipment"),
                       ("subscribe_webhook", "Can subscribe to a webhook of an event")]


class ShipmentDocument(models.Model):
    shipment = models.ForeignKey(Shipment, related_name="documents", on_delete=models.CASCADE)
    document = models.FileField(upload_to='document')
