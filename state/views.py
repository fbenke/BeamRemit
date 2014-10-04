from rest_framework.generics import RetrieveAPIView

from state import serializers
from state.models import State


class GetState(RetrieveAPIView):
    serializer_class = serializers.StateSerializer

    def get_object(self):
        queryset = State.objects.get(end__isnull=True)
        return queryset
