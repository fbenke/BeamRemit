from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pricing.models import Pricing, Comparison, get_current_object


class PricingCurrent(APIView):

    def _serialize(self):

        response_dict = {}

        response_dict['pricing_id'] = self.pricing.id
        response_dict['beam_rate'] = self.pricing.calculate_exchange_rate()
        response_dict['beam_fee'] = self.pricing.fee
        response_dict['comparison'] = self.comparison.price_comparison
        response_dict['comparison_retrieved'] = self.comparison.start

        return response_dict

    def get(self, request, *args, **kwargs):

        try:
            self.pricing = get_current_object(Pricing)
            self.comparison = get_current_object(Comparison)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self._serialize())

