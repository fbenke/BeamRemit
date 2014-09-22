from django.conf import settings
from django.db import transaction as dbtransaction

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beam.utils.exceptions import APIException
from beam.utils.security import generate_signature

from transaction import serializers
from transaction.models import Transaction, Pricing
from transaction.permissions import IsNoAdmin

from btc_payment.api_calls import gocoin
from btc_payment.models import GoCoinInvoice

from pricing.models import get_current_object


class CreateTransaction(GenericAPIView):
    serializer_class = serializers.CreateTransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    def post_save(self, obj, created=False):

        # TOD: remove code specific to a certain payment processor

        message = (str(obj.id) + str(obj.amount_gbp + obj.pricing.fee) + settings.GOCOIN_INVOICE_CALLBACK_URL)
        signature = generate_signature(message, settings.GOCOIN_API_KEY)

        result = gocoin.generate_invoice(
            price=obj.amount_gbp + obj.pricing.fee,
            reference_number=obj.reference_number,
            transaction_id=obj.id,
            signature=signature
        )

        gocoin_invoice = GoCoinInvoice(
            transaction=obj,
            invoice_id=result['invoice_id'],
            btc_address=result['btc_address']
        )

        obj.amount_btc = result['amount_btc']

        with dbtransaction.atomic():
            gocoin_invoice.save()
            obj.gocoin_invoice = GoCoinInvoice.objects.get(id=gocoin_invoice.id)
            obj.save()

    def post(self, request):

        serializer = self.serializer_class(user=request.user, data=request.DATA)

        if get_current_object(Pricing).id != request.DATA.get('pricing_id'):
            # Pricing expired
            return Response({'detail': '0'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.profile.is_complete:
            # Sender Profile is incomplete
            return Response({'detail': '1'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if serializer.is_valid():

                self.object = serializer.save(force_insert=True)

                self.post_save(self.object, created=True)

                # TODO: remove code specific to a certain payment processor
                return Response({
                    'invoice_id': self.object.gocoin_invoice.invoice_id},
                    status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except APIException:
            self.object.set_invalid()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ViewTransactions(ListAPIView):
    serializer_class = serializers.TransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(sender__id=user.id)
        return queryset


class GetTransaction(RetrieveAPIView):
    serializer_class = serializers.TransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(sender__id=user.id)
        return queryset
