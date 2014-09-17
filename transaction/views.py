from django.db import transaction as dbtransaction

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from beam.utils import APIException

from transaction import serializers
from transaction.models import Transaction
from transaction.permissions import IsNoAdmin

from btc_payment.api_calls import gocoin
from btc_payment.models import GoCoinInvoice


class CreateTransaction(GenericAPIView):
    serializer_class = serializers.CreateTransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    def post_save(self, obj, created=False):

        # TOD: remove code specific to a certain payment processor
        result = gocoin.generate_invoice(
            price=obj.amount_gbp,
            reference_number=obj.reference_number,
            transaction_id=obj.id,
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

        try:
            if serializer.is_valid():

                self.object = serializer.save(force_insert=True)

                self.post_save(self.object, created=True)

                 # TOD: remove code specific to a certain payment processor
                return Response({
                    'detail': 'success',
                    'invoice_id': self.object.gocoin_invoice.invoice_id},
                    status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except APIException:
            self.object.set_invalid()

            return Response({'detail': 'API Exception'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ViewTransactions(ListAPIView):
    serializer_class = serializers.TransactionSerializer
    permission_classes = (IsAdminUser,)
    paginate_by = 20

    def get_queryset(self):
        queryset = Transaction.objects.all()
        state = self.request.QUERY_PARAMS.get('state', None)
        if state is not None:
            queryset = queryset.filter(state=state)
        return queryset


@api_view(['GET'])
def test(request):
    gocoin.generate_invoice(
        price=0.1,
        reference_number='34253',
        transaction_id=1,
        currency='GBP'
    )
    return Response()
