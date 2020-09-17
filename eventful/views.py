
import logging

from rest_framework import viewsets
from shipment.custom_permissions import CanSubscribeWebhook
from eventful.serializers import EventSerializer
from eventful.models import Event

logger = logging.getLogger(__name__)


class EventResource(viewsets.ModelViewSet):

    permission_classes = (CanSubscribeWebhook, )
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    def get_queryset(self):
        user = self.request.user
        return Event.objects.all() if user.is_staff else Event.objects.filter(user=user)
