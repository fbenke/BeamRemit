from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pricing.models import Pricing, Comparison, get_current_object


class PricingCurrent(APIView):

    def _serialize(self):

        return self.comparison.price_comparison

    def get(self, request, *args, **kwargs):

        try:
            self.pricing = get_current_object(Pricing)
            self.comparison = get_current_object(Comparison)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self._serialize())


