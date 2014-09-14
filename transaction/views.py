from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from transaction import serializers
from transaction.models import Transaction
from transaction.api_calls import coinbase


class CreateTransaction(APIView):
    serializer_class = serializers.CreateTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        serializer = self.serializer_class(user=request.user, data=request.DATA)

        if serializer.is_valid():

            self.object = serializer.save(force_insert=True)

            return Response({'detail': 'success'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    coinbase.generate_receive_address('12345')
    return Response()
