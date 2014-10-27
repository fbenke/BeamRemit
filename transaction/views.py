from django.conf import settings

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from beam.utils.exceptions import APIException
from beam.utils.ip_blocking import country_blocked, is_tor_node,\
    get_client_ip, HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS

from transaction import constants
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

        # initiate payment with external payment processor
        self.invoice_id = payment_class.initiate(obj)

    def post(self, request):

        # block countries we are not licensed to operate in and tor clients
        client_ip = get_client_ip(request)

        if country_blocked(client_ip) or is_tor_node(client_ip):
            return Response(status=HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS)

        try:

            serializer = self.serializer_class(user=request.user, data=request.DATA)

            if serializer.is_valid():

                # check if Pricing has expired
                if get_current_object(Pricing).id != request.DATA.get('pricing_id'):
                    return Response({'detail': constants.PRICING_EXPIRED}, status=status.HTTP_400_BAD_REQUEST)

                # basic profile information incomplete
                if not request.user.profile.information_complete:
                    return Response({'detail': constants.PROFILE_INCOMPLETE}, status=status.HTTP_400_BAD_REQUEST)

                # calculate today's transaction volume for the user
                todays_vol = request.user.profile.todays_transaction_volume(
                    request.DATA.get('sent_amount'), request.DATA.get('sent_currency'))

                # sender has exceeded basic transaction limit
                if todays_vol > get_current_object(Limit).user_limit_basic_gbp:

                    # sender has exceeded maximum daily transaction limit
                    if todays_vol > get_current_object(Limit).user_limit_complete_gbp:
                        return Response({'detail': constants.TRANSACTION_LIMIT_EXCEEDED}, status=status.HTTP_400_BAD_REQUEST)

                    #  sender has not provided additional document
                    if not request.user.profile.documents_provided:
                        return Response({'detail': constants.ADDITIONAL_DOCUMENTS_MISSING}, status=status.HTTP_400_BAD_REQUEST)

                    #  documents still await verification
                    if not request.user.profile.documents_verified:
                        return Response({'detail': constants.DOCUMENTS_NOT_VERIFIED}, status=status.HTTP_400_BAD_REQUEST)

                self.object = serializer.save(force_insert=True)

                self.post_save(self.object, created=True)

                return Response(
                    {'invoice_id': self.invoice_id,
                     'received_amount': self.object.received_amount,
                     'received_currency': self.object.received_currency,
                     'operation_mode': get_current_state()},
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
        queryset = Transaction.objects.filter(
            sender__id=user.id,
            state__in=(
                Transaction.PAID, Transaction.INVALID,
                Transaction.PROCESSED, Transaction.CANCELLED
            )
        )
        return queryset


class GetTransaction(RetrieveAPIView):
    serializer_class = serializers.TransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(sender__id=user.id)
        return queryset
