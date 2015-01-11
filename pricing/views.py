from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from beam.utils.angular_requests import get_site_by_request
from beam.utils.ip_analysis import get_default_currency

from pricing import serializers

from state.models import get_current_state
from pricing.models import get_current_pricing, get_current_exchange_rate,\
    get_current_comparison, get_current_limits, get_current_fees


class PricingCurrent(APIView):

    def get(self, request, *args, **kwargs):

        try:

            response_dict = {}
            site = get_site_by_request(request)
            pricing = get_current_pricing(site)
            comparison = get_current_comparison()
            default_currency = get_default_currency(request)
            currencies = settings.SITE_SENDING_CURRENCY[site.id]

            response_dict['pricing_id'] = pricing.id
            response_dict['exchange_rate_id'] = get_current_exchange_rate().id
            response_dict['fees'] = {f.currency: {'rate': f.amount, 'id': f.id} for f in get_current_fees(site)}
            response_dict['rates'] = pricing.exchange_rates
            response_dict['operation_mode'] = get_current_state(site).state
            response_dict['default_currency'] = default_currency if default_currency in currencies else currencies[0]

            if comparison:
                response_dict['comparison'] = comparison.price_comparison
                response_dict['comparison_retrieved'] = comparison.start

        except ObjectDoesNotExist:

            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(response_dict)


class LimitCurrent(ListAPIView):

    serializer_class = serializers.LimitSerializer

    def get_queryset(self, queryset=None):
        site = get_site_by_request(self.request)
        return get_current_limits(site)

    def get(self, request, *args, **kwargs):
        response = super(LimitCurrent, self).get(request, *args, **kwargs)
        new_response = {}
        for i in range(len(response.data)):
            new_response['{}{}'.format(
                response.data[i]['sending_currency'],
                response.data[i]['receiving_currency'])
            ] = response.data[i]

        response.data= new_response

        return response
