from django.core.exceptions import ObjectDoesNotExist

from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status

from pricing.models import Pricing, Comparison
from pricing import serializers

from beam.utils.general import log_error


class PricingCurrent(RetrieveAPIView):
    serializer_class = serializers.PricingSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            self.object = Pricing.objects.get(end__isnull=True)
        except ObjectDoesNotExist:
            log_error('ERROR Pricing - No pricing object found.')
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = self.get_serializer(self.object)

        return Response(serializer.data)


# class PriceComparison(RetrieveAPIView):
#     serializer_class = serializers.PriceComparisonSerializer

#     def retrieve(self, request, *args, **kwargs):
#         try:
#             self.object = Comparison.objects.get(end__isnull=True)
#         except ObjectDoesNotExist:
#             log_error('ERROR Pricing - No price comparison object found.')
#             return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#         serializer = self.get_serializer(self.object)

#         return Response(serializer.data)
