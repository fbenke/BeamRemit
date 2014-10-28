from django.core.exceptions import ObjectDoesNotExist

from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from pricing.models import Pricing, Comparison, Limit, get_current_object
from pricing import serializers

from state.models import get_current_state


class PricingCurrent(APIView):

    def _serialize(self):

        response_dict = {}

        response_dict['pricing_id'] = self.pricing.id
        response_dict['beam_rate_ghs'] = self.pricing.exchange_rate_ghs
        response_dict['beam_rate_sll'] = self.pricing.exchange_rate_sll
        response_dict['beam_rate_usd'] = self.pricing.gbp_usd
        response_dict['beam_fee_gbp'] = self.pricing.fee_gbp
        response_dict['beam_fee_usd'] = self.pricing.fee_usd
        response_dict['comparison'] = self.comparison.price_comparison
        response_dict['comparison_retrieved'] = self.comparison.start
        response_dict['operationMode'] = get_current_state()

        return response_dict

    def get(self, request, *args, **kwargs):

        try:
            self.pricing = get_current_object(Pricing)
            self.comparison = get_current_object(Comparison)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self._serialize())


class LimitCurrent(RetrieveAPIView):

    serializer_class = serializers.LimitSerializer

    def get_object(self, queryset=None):
        try:
            return get_current_object(Limit)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
