from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from beam.tests import TestUtils

from state.models import State, get_current_state


class StatusAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_limit(self):

        self.assertEqual(State.objects.all().count(), 0)
        response = self.client.post(
            reverse('admin:state_state_add'),
            data={'state': State.RUNNING}
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(State.objects.all().count(), 1)

        self.assertEqual(get_current_state(), State.RUNNING)


class StatusAPITests(APITestCase, TestUtils):

    def test_get_status(self):
        app_states = (State.RUNNING, State.OUT_OF_CASH, State.OUTSIDE_BIZ_HOURS)
        for s in app_states:
            self._create_state(s)
            response = self.client.get(reverse('state:current'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['state'], s)
