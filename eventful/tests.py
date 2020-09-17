import json
import mock
import responses

from django.test import TestCase
from django.contrib.auth.models import Group

from profiles.fixtures_factory import (
    UserFactory,
    DeveloperProfileFactory,
)
from eventful.tasks import notify
from eventful.models import Event

APPLY_ASYNC = mock.Mock()


class TestEventAPI(TestCase):
    fixtures = ['auth.json']

    def setUp(self):
        self.developer1 = UserFactory(username="dev", role="DEVELOPER")
        self.developer1.set_password("dev")
        self.developer1.save()
        DeveloperProfileFactory(user=self.developer1)
        Group.objects.get(name="DEVELOPER").user_set.add(self.developer1)

        self.developer2 = UserFactory(username="dev2", role="DEVELOPER")
        self.developer2.set_password("dev2")
        self.developer2.save()
        DeveloperProfileFactory(user=self.developer2)
        Group.objects.get(name="DEVELOPER").user_set.add(self.developer2)

    def _get_access_token(self, username, password):

        response = self.client.post(
            '/api/v1/token/',
            data=json.dumps({
                "username": username,
                "password": password
            }),
            content_type='application/json',
        )

        return response.json()['access']

    def test_developer_can_subscribe_webhook(self):

        access_token = self._get_access_token(self.developer1.username, "dev")

        # create developer account
        response = self.client.post(
            '/api/v1/events/',
            data=json.dumps({
                "webhook": "http://www.google.com",
                "event_name": "SHIPMENT_STATE_CHANGED",
                "headers": "{}"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(201, response.status_code)
        self.assertEquals(
            {
                'id': 1,
                'event_name': 'SHIPMENT_STATE_CHANGED',
                'webhook': 'http://www.google.com',
                'max_retry': 1,
                'headers': '{}'
            }, response.json())

    def test_developer_can_get_subscriptions(self):

        Event.objects.create(user=self.developer1)
        Event.objects.create(user=self.developer2)

        access_token = self._get_access_token(self.developer1.username, "dev")

        # create developer account
        response = self.client.get(
            '/api/v1/events/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.json()))


class TestEventDispatch(TestCase):
    """Testing event notification dispatching"""
    @mock.patch("eventful.models.notify.apply_async")
    def test_event_dispatch(self, notify_mock):
        user = UserFactory()
        event = Event.objects.create(user=user, webhook="http://test.com", headers='{"Auth": "123"}')
        Event.dispatch(event.event_name, user.id, {"test": "test1"})
        notify_mock.assert_called_with(
            ('http://test.com', 'SHIPMENT_STATE_CHANGED', {
                'test': 'test1'
            }, {
                "Auth": "123"
            }),
            retry=True,
            retry_policy={'max_retries': 1},
        )

    @responses.activate
    def test_notify_event(self):
        responses.add(
            responses.POST,
            "http://test.com",
        )
        notify('http://test.com', 'SHIPMENT_STATE_CHANGED', {'test': 'test1'}, {"Auth": "123"})

        self.assertEquals("123", responses.calls[0].request.headers['Auth'])
        self.assertEquals({
            "event": "SHIPMENT_STATE_CHANGED",
            "payload": {
                "test": "test1"
            }
        }, json.loads(responses.calls[0].request.body))
