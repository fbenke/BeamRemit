from django.conf import settings

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beam.utils.exceptions import APIException

from transaction import serializers
from transaction.models import Transaction, Pricing
from transaction.permissions import IsNoAdmin

from pricing.models import Limit, get_current_object

from state.models import get_current_state

from account.utils import AccountException

mod = __import__('btc_payment.models', fromlist=[settings.PAYMENT_PROCESSOR])
payment_class = getattr(mod, settings.PAYMENT_PROCESSOR)


class CreateTransaction(GenericAPIView):
    serializer_class = serializers.CreateTransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    def post_save(self, obj, created=False):

        self.invoice_id = payment_class.initiate(obj)

    def post(self, request):

        try:
            # check if Pricing has expired
            if get_current_object(Pricing).id != request.DATA.get('pricing_id'):
                return Response({'detail': '0'}, status=status.HTTP_400_BAD_REQUEST)

            # basic profile information incomplete
            if not request.user.profile.information_complete:
                return Response({'detail': '1'}, status=status.HTTP_400_BAD_REQUEST)

            # calculate today's transaction volume for the user
            todays_vol = request.user.profile.todays_transaction_volume(request.DATA.get('amount_gbp'))

            # sender has exceeded basic transaction limit
            if todays_vol > get_current_object(Limit).daily_limit_gbp_basic:

                # sender has exceeded maximum daily transaction limit
                if todays_vol > get_current_object(Limit).daily_limit_gbp_complete:
                    return Response({'detail': '4'}, status=status.HTTP_400_BAD_REQUEST)

                #  sender has not provided additional document
                if not request.user.profile.documents_provided:
                    return Response({'detail': '2'}, status=status.HTTP_400_BAD_REQUEST)

                #  documents still await verification
                if not request.user.profile.documents_verified:
                    return Response({'detail': '3'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.serializer_class(user=request.user, data=request.DATA)

            if serializer.is_valid():

                self.object = serializer.save(force_insert=True)

                self.post_save(self.object, created=True)

                return Response(
                    {'invoice_id': self.invoice_id,
                     'amount_ghs': self.object.amount_ghs,
                     'operationMode': get_current_state()},
                    status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except APIException:
            self.object.set_invalid()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except AccountException:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ViewTransactions(ListAPIView):
    serializer_class = serializers.TransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        states = list(set(Transaction.TRANSACTION_STATES) - set(Transaction.INIT))
        queryset = Transaction.objects.filter(sender__id=user.id, state__in=states)
        return queryset


class GetTransaction(RetrieveAPIView):
    serializer_class = serializers.TransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(sender__id=user.id)
        return queryset
