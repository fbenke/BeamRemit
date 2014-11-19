from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APITestCase

from beam.tests import TestUtils

from state.models import State, get_current_state

# from unittest import skip


class StatusAdminTests(TestCase, TestUtils):

    def setUp(self):
        admin = self._create_admin_user()
        self.client.login(username=admin.username, password=self.default_password)

    def tearDown(self):
        self.client.logout()

    def test_add_status(self):

        no_states = State.objects.all().count()
        response = self.client.post(
            reverse('admin:state_state_add'),
            data={
                'state': State.RUNNING,
                'site': '0'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(State.objects.all().count(), no_states + 1)

        response = self.client.post(
            reverse('admin:state_state_add'),
            data={
                'state': State.OUT_OF_CASH,
                'site': '1'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(State.objects.all().count(), no_states + 2)

        self.assertEqual(get_current_state(Site.objects.get(id=0)).state, State.RUNNING)
        self.assertEqual(get_current_state(Site.objects.get(id=1)).state, State.OUT_OF_CASH)


class StatusAPITests(APITestCase, TestUtils):

    def test_get_status(self):
        app_states = (State.RUNNING, State.OUT_OF_CASH, State.OUTSIDE_BIZ_HOURS)
        for s in app_states:
            self._create_state(s)
            response = self.client.get(reverse('state:current'))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['state'], s)
