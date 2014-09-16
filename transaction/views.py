from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from userena.utils import get_protocol

from beam.utils import APIException, log_error, send_sendgrid_mail

from transaction import serializers
from transaction.models import Transaction
from transaction.api_calls import coinbase
from transaction.permissions import IsNoAdmin


class CreateTransaction(GenericAPIView):
    serializer_class = serializers.CreateTransactionSerializer
    permission_classes = (IsAuthenticated, IsNoAdmin)

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
        '''
        Payment callback from Coinbase, as described in
        https://coinbase.com/docs/merchant_tools/callbacks
        '''

        try:
            if request.DATA.get('order')['status'] == 'completed':

                transaction = Transaction.objects.get(
                    id=int(request.DATA.get('order')['custom']),
                    state=Transaction.INIT
                )

                if not transaction.coinbase_button_code == request.DATA.get('order')['button']['id']:
                    message = 'ERROR - Coinbase Callback: button code mismatch {}'
                    raise APIException

                if not transaction.amount_gbp * 100 == request.DATA.get('order')['total_native']['cents']:
                    message = 'ERROR - Coinbase Callback: native amount mismatch {}'
                    raise APIException

                transaction.coinbase_order_reference = request.DATA.get('order')['id']
                transaction.amount_btc = request.DATA.get('order')['total_btc']['cents']
                transaction.state = Transaction.PAID
                transaction.paid_at = timezone.now()
                # transaction.save()

            # no payment received withing 10 min
            elif request.DATA.get('order')['status'] == 'expired':
                # TODO
                pass
            # either payment with incorrect amount or received after 10 min time window
            elif request.DATA.get('order')['status'] == 'mispaid':
                # TODO
                pass

            send_sendgrid_mail(
                subject_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_SUBJECT,
                email_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_TEXT,
                context={
                    'site': Site.objects.get_current(),
                    'protocol': get_protocol()
                }
            )

            return Response(status=status.HTTP_200_OK)

        except Transaction.DoesNotExist:
            message = 'ERROR - Coinbase Callback: no transaction found for transaction id. {}'
            log_error(message.format(request.DATA))
        except (KeyError, TypeError, ValueError) as e:
            message = 'ERROR - Coinbase Callback: received invalid payment notification, {}, {}'
            log_error(message.format(e, request.DATA))
        except APIException:
            log_error(message.format(request.DATA))

        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def test(request):

    coinbase.generate_button(2.00, 'Falk', 1)
    return Response()
