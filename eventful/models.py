from django.db import models
from django.conf import settings
from eventful.tasks import notify


class Event(models.Model):
    SHIPMENT_STATE_CHANGED = "SHIPMENT_STATE_CHANGED"

    EVENT_CHOICES = ((SHIPMENT_STATE_CHANGED, SHIPMENT_STATE_CHANGED), )

    event_name = models.CharField(max_length=255, choices=EVENT_CHOICES, default=SHIPMENT_STATE_CHANGED)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="events")
    webhook = models.URLField()
    headers = models.TextField(default="{}")
    max_retry = models.IntegerField(default=1)

    class Meta:
        unique_together = (('user', 'event_name'), )

    @staticmethod
    def dispatch(event_name, user_id, payload):
        """
        Dispatch an Event to the subscribers

        Args:
            event_name (str): The event happened
            user_id (int): The id of the user that is interested in this event
            payload (Dict): The Bayload that will be sent to the user's webhook

        Returns:
            None
        """

        event = Event.objects.filter(event_name=event_name, user_id=user_id)
        if not event:
            return

        event = event.first()

        headers = eval(event.headers or "{}")  # pylint: disable=eval-used

        notify.apply_async(
            (event.webhook, event_name, payload, headers),
            retry=True,
            retry_policy={"max_retries": event.max_retry},
        )

    def __str__(self):
        return f"{self.event_name} for owner {self.user.username}"
