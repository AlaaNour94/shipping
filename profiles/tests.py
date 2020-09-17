import json

from django.test import TestCase

from profiles.models import DeveloperProfile
from profiles.fixtures_factory import UserFactory


class UserCreationTests(TestCase):
    fixtures = ['auth.json']

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

    def test_admin_can_create_developer_user(self):

        # get admin access token
        access_token = self._get_access_token("zid", "zid")

        # create developer account
        response = self.client.post(
            '/api/v1/users/',
            data=json.dumps({
                "username": "developer1",
                "password": "pass",
                "role": "DEVELOPER",
                "first_name": "d",
                "last_name": "e",
                "email": "test@test.com"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(201, response.status_code)
        response = response.json()
        del response['id']
        self.assertEquals(
            {
                "username": "developer1",
                "role": "DEVELOPER",
                "first_name": "d",
                "last_name": "e",
                "email": "test@test.com"
            }, response)

        self.assertEquals(1, DeveloperProfile.objects.count())

    def test_non_admin_accounts_can_not_create_account(self):
        dev_user = UserFactory(username="dev", role="DEVEOPER")
        dev_user.set_password('dev')
        dev_user.save()

        # get access token
        access_token = self._get_access_token("dev", "dev")

        response = self.client.post(
            '/api/v1/users/',
            data=json.dumps({
                "username": "developer1",
                "password": "pass",
                "role": "DEVELOPER",
                "first_name": "d",
                "last_name": "e",
                "email": "test@test.com"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(403, response.status_code)

    def test_me_endpoint_return_my_profile(self):
        dev_user = UserFactory(username="driv", role="DRIVER")
        dev_user.set_password('driv')
        dev_user.save()

        # get access token
        access_token = self._get_access_token("driv", "driv")

        response = self.client.get(
            '/api/v1/users/me/',
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(dev_user.username, response.json()['username'])
        self.assertEquals(dev_user.role, response.json()['role'])
        self.assertEquals(dev_user.id, response.json()['id'])
