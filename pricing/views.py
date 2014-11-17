from django.core.exceptions import ObjectDoesNotExist

from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from beam.utils.angular_requests import get_site_by_request

from pricing.models import Pricing, ExchangeRate, Comparison, Limit,\
    get_current_object, get_current_object_by_site
from pricing import serializers

from state.models import get_current_state


class PricingCurrent(APIView):

    def _serialize(self):

        response_dict = {}

        response_dict['pricing_id'] = self.pricing.id
        response_dict['exchange_rate_id'] = self.exchange_rate.id
        response_dict['beam_rate_ghs'] = self.pricing.exchange_rate_ghs
        response_dict['beam_rate_sll'] = self.pricing.exchange_rate_sll
        response_dict['beam_rate_usd'] = self.exchange_rate.gbp_usd
        response_dict['beam_fee'] = self.pricing.fee
        response_dict['beam_fee_currency'] = self.pricing.fee_currency
        response_dict['comparison'] = self.comparison.price_comparison
        response_dict['comparison_retrieved'] = self.comparison.start
        response_dict['operation_mode'] = self.state

        return response_dict

    def get(self, request, *args, **kwargs):

        try:
            site = get_site_by_request(request)
            self.pricing = get_current_object_by_site(Pricing, site)
            self.exchange_rate = get_current_object(ExchangeRate)
            self.comparison = get_current_object(Comparison)
            self.state = get_current_state()
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self._serialize())


class LimitCurrent(RetrieveAPIView):

    serializer_class = serializers.LimitSerializer

    def get_object(self, queryset=None):
        try:
            site = get_site_by_request(self.request)
            return get_current_object_by_site(Limit, site)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
