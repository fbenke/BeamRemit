from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction import serializers
from transaction.models import Transaction
from transaction.api_calls import coinbase

from beam.utils import APIException


class CreateTransaction(GenericAPIView):
    serializer_class = serializers.CreateTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def post_save(self, obj, created=True):
        obj.generate_coinbase_button()

    def post(self, request):

        serializer = self.serializer_class(user=request.user, data=request.DATA)

        try:
            if serializer.is_valid():

                self.object = serializer.save(force_insert=True)

                self.post_save(self.object, created=True)

                return Response(
                    {'detail': 'success',
                     'button_code': self.object.coinbase_button_code},
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


class ConfirmPayment(APIView):

    def post(self, request):
        print request.DATA

        # wallet_address = request.DATA.get('address')
        # amount = request.DATA.get('amount')
        # transaction_hash = request.DATA.get('transaction').get('hash')

        return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def test(request):

    coinbase.generate_button(2.00, 'Falk', 1)
    return Response()
