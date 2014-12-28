from django.core.exceptions import ObjectDoesNotExist

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from beam.utils.angular_requests import get_site_by_request

from pricing import serializers

from state.models import get_current_state
from pricing.models import get_current_pricing, get_current_exchange_rate,\
    get_current_comparison, get_current_limits, get_current_fees


class PricingCurrent(APIView):

    def _serialize(self):

        response_dict = {}

        response_dict['pricing_id'] = self.pricing.id
        response_dict['exchange_rate_id'] = self.exchange_rate.id
        response_dict['rates'] = self.pricing.exchange_rates
        response_dict['fees'] = {str(f.id): {f.currency: f.fee} for f in self.fees}
        response_dict['comparison'] = self.comparison.price_comparison
        response_dict['comparison_retrieved'] = self.comparison.start
        response_dict['operation_mode'] = self.state
        return response_dict

    def get(self, request, *args, **kwargs):

        try:
            site = get_site_by_request(request)
            self.pricing = get_current_pricing(site)
            self.fees = get_current_fees(site)
            self.exchange_rate = get_current_exchange_rate()
            self.comparison = get_current_comparison()
            self.state = get_current_state(site).state
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(self._serialize())


class LimitCurrent(ListAPIView):

    serializer_class = serializers.LimitSerializer

    def get_queryset(self, queryset=None):
        site = get_site_by_request(self.request)
        return get_current_limits(site)
