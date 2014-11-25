from rest_framework.generics import RetrieveAPIView

from state import serializers
from state.models import get_current_state

from beam.utils.angular_requests import get_site_by_request


class GetState(RetrieveAPIView):

    serializer_class = serializers.StateSerializer

    def get_object(self):
        site = get_site_by_request(self.request)
        return get_current_state(site)

