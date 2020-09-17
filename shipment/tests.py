import json
import mock
import datetime
import zipfile
import io

from freezegun import freeze_time
from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile

from shipment.models import Shipment
from profiles.fixtures_factory import (
    UserFactory,
    DeveloperProfileFactory,
    DriverProfileFactory,
)

from shipment.fixtures_factory import ShipmentFactory


class ShipmentTests(TestCase):
    fixtures = ['auth.json']

    def setUp(self):
        self.developer1 = UserFactory(username="dev", role="DEVELOPER")
        self.developer1.set_password("dev")
        self.developer1.save()
        DeveloperProfileFactory(user=self.developer1)

        self.developer2 = UserFactory(username="dev2", role="DEVELOPER")
        self.developer2.set_password("dev2")
        self.developer2.save()
        DeveloperProfileFactory(user=self.developer2)

        Group.objects.get(name="DEVELOPER").user_set.add(self.developer1)

        self.driver = UserFactory(username="driver", role="DRIVER")
        self.driver.set_password("driver")
        self.driver.save()
        Group.objects.get(name="DRIVER").user_set.add(self.driver)
        DriverProfileFactory(user=self.driver)

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

    def test_developer_can_create_shipment(self):
        access_token = self._get_access_token(self.developer1.username, "dev")

        # create developer account
        response = self.client.post(
            '/api/v1/shipments/',
            data=json.dumps({
                "receiver_name": "alaa",
                "receiver_country": "EG",
                "receiver_address": "Cairo",
                "weight": 1.5,
                "lat": 23.4545,
                "lon": 32.5454,
                "title": "Test_shipment"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(201, response.status_code)
        response = response.json()
        del response['tracking_id']
        self.assertEquals(
            {
                'receiver_name': 'alaa',
                'receiver_country': 'EG',
                'receiver_address': 'Cairo',
                'estimated_shipping_date': None,
                'state': 'PENDING',
                'scheduled_at': None,
                'weight': 1.5,
                'lat': '23.45450000',
                'lon': '32.54540000',
                'title': 'Test_shipment',
                'documents': []
            }, response)

    def test_driver_can_not_create_shipment(self):
        access_token = self._get_access_token(self.driver.username, "driver")

        # create developer account
        response = self.client.post(
            '/api/v1/shipments/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(403, response.status_code)

    def test_developer_can_list_his_shipments(self):
        ShipmentFactory(owner=self.developer1)
        ShipmentFactory(owner=self.developer1)
        ShipmentFactory(owner=self.developer1)
        ShipmentFactory(driver=self.driver)

        access_token = self._get_access_token(self.developer1.username, "dev")

        # create developer account
        response = self.client.get(
            '/api/v1/shipments/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(3, len(response.json()))

    def test_driver_can_list_his_shipment(self):
        ShipmentFactory(owner=self.developer1)
        ShipmentFactory(owner=self.developer1)
        ShipmentFactory(owner=self.developer1)
        ShipmentFactory(driver=self.driver)

        access_token = self._get_access_token(self.driver.username, "driver")

        # create developer account
        response = self.client.get(
            '/api/v1/shipments/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.json()))

    def test_admin_can_list_all_shipments(self):
        ShipmentFactory(owner=self.developer1, tracking_id=1)
        ShipmentFactory(owner=self.developer1, tracking_id=2)
        ShipmentFactory(owner=self.developer1, tracking_id=3)
        ShipmentFactory(driver=self.driver, tracking_id=4)

        access_token = self._get_access_token("zid", "zid")

        # create developer account
        response = self.client.get(
            '/api/v1/shipments/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals(4, len(response.json()))

    def test_admin_can_assign_diver_to_shipment(self):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token("zid", "zid")
        self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/assign_driver/{self.driver.id}/',
            data=json.dumps({"driver_id": self.driver.id}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        shipment.refresh_from_db()
        self.assertEquals(self.driver, shipment.driver)

    def test_error_if_assign_developer_to_shipment(self):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token("zid", "zid")
        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/assign_driver/{self.developer1.id}/',
            data=json.dumps({"driver_id": self.developer1.id}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(400, response.status_code)
        self.assertEquals({
            'success': False,
            'error': 'You should assign user of type `DRIVER`'
        }, response.json())

    def test_error_if_assign_wrong_id_to_shipment(self):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token("zid", "zid")
        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/assign_driver/10000/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(404, response.status_code)
        self.assertEquals({'success': False, 'error': 'Can not find driver with this id'}, response.json())

    @mock.patch("shipment.models.Event.dispatch")
    def test_driver_can_update_the_state_of_a_shipment(self, event_dispatch_mock):
        shipment = ShipmentFactory(state='SCHEDULED', driver=self.driver)
        access_token = self._get_access_token(self.driver.username, "driver")
        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/update_state/',
            data=json.dumps({"state": Shipment.PREPARED}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        shipment.refresh_from_db()
        self.assertEquals(Shipment.PREPARED, shipment.state)
        self.assertEquals(200, response.status_code)
        self.assertEquals({"success": True}, response.json())
        event_dispatch_mock.assert_called_with("SHIPMENT_STATE_CHANGED", shipment.owner_id,
                                               shipment.to_dict())

    def test_driver_can_not_update_the_state_shipments_in_PENDING_state(self):
        shipment = ShipmentFactory(driver=self.driver)
        access_token = self._get_access_token(self.driver.username, "driver")
        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/update_state/',
            data=json.dumps({"state": Shipment.PREPARED}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        shipment.refresh_from_db()
        self.assertEquals(Shipment.PENDING, shipment.state)
        self.assertEquals(400, response.status_code)
        self.assertEquals({
            'success': False,
            'error': 'Cannot change state from PENDING to PREPARED'
        }, response.json())

    def test_developer_can_not_update_the_state_shipments(self):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token(self.developer1.username, "dev")
        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/update_state/',
            data=json.dumps({"state": Shipment.PREPARED}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(403, response.status_code)

    @mock.patch("shipment.models.Shipment.estimate_delivery_date", return_value="2020-09-09")
    def test_developer_can_schedule_shipments(self, delivery_estimation_mock):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token(self.developer1.username, "dev")
        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/schedule/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        shipment.refresh_from_db()

        delivery_estimation_mock.assert_called_once()
        self.assertEquals(Shipment.SCHEDULED, shipment.state)
        self.assertEquals(str(datetime.datetime.now().date()), str(shipment.scheduled_at))
        self.assertEquals("2020-09-09", str(shipment.estimated_shipping_date))
        self.assertEquals(200, response.status_code)
        self.assertEquals({'estimated_shipping_date': '2020-09-09', 'success': True}, response.json())

    def test_developer_can_attach_documents(self):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token(self.developer1.username, "dev")
        file1 = SimpleUploadedFile("file1.jpg", b"file_content", content_type="image/jpg")
        file2 = SimpleUploadedFile("file2.jpg", b"file_content", content_type="image/jpg")
        file3 = SimpleUploadedFile("file3.jpg", b"file_content", content_type="image/jpg")

        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/attach_documents/',
            {'documents': [file1, file2, file3]},
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(201, response.status_code)
        self.assertEquals(3, shipment.documents.count())

    def test_error_when_attaching_no_documents(self):
        shipment = ShipmentFactory(owner=self.developer1)
        access_token = self._get_access_token(self.developer1.username, "dev")

        response = self.client.post(
            f'/api/v1/shipments/{shipment.tracking_id}/attach_documents/',
            format='multipart',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(400, response.status_code)
        self.assertEquals({"error": "please attach some documents"}, response.json())

    def test_developer_can_print_documents(self):
        ShipmentFactory(owner=self.developer1, tracking_id="1")
        ShipmentFactory(owner=self.developer1, tracking_id="2")
        ShipmentFactory(owner=self.developer2, tracking_id="3")

        access_token = self._get_access_token(self.developer1.username, "dev")

        response = self.client.get(
            '/api/v1/shipments/print/?tracking_id=1&tracking_id=2',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(200, response.status_code)
        file = io.BytesIO(response.content)
        zp = zipfile.ZipFile(file)

        self.assertCountEqual(['1.pdf', '2.pdf'], [x.filename for x in zp.infolist()])

    @freeze_time('2020-05-01')
    @mock.patch("shipment.models.predict", return_value=3.5)
    def test_estimate_delivery_date(self, perdiction_mock):
        ShipmentFactory(owner=self.developer1, tracking_id="1")
        access_token = self._get_access_token(self.developer1.username, "dev")

        response = self.client.get(
            '/api/v1/shipments/1/estimate_delivery_date/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEquals(200, response.status_code)
        self.assertEquals({'date': '2020-05-05T00:00:00'}, response.json())
