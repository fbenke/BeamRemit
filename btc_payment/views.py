# from django.conf import settings
# from django.contrib.sites.models import Site

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# from userena.utils import get_protocol

# from beam.utils import APIException, log_error, send_sendgrid_mail

# from transaction.models import Transaction


class ConfirmGoCoinPayment(APIView):
    def post(self, request):
        print request

        return Response(status=status.HTTP_200_OK)

# class ConfirmPayment(APIView):

#     def post(self, request):
#         '''
#         Payment callback from Coinbase, as described in
#         https://coinbase.com/docs/merchant_tools/callbacks
#         '''

#         try:

#             # mispayment received or no payment received within 10 min
#             if request.DATA.get('order')['status'] == 'expired' or\
#                     request.DATA.get('order')['event']['type'] == 'mispayment':
#                 # invalidate transaction, if it is still in init state
#                 try:
#                     transaction = Transaction.objects.get(
#                         id=int(request.DATA.get('order')['custom']),
#                         state=Transaction.INIT
#                     )
#                     transaction.set_invalid(commit=False)
#                 except Transaction.DoesNotExist:
#                     pass
#                 print 'expired'

#             # received valid payment, i.e. right amount within timeframe
#             # request is validated and set paid (even if it was in invalid state before)
#             if request.DATA.get('order')['event']['type'] == 'completed':

#                 transaction = Transaction.objects.get(
#                     id=int(request.DATA.get('order')['custom'])
#                 )

#                 if not transaction.coinbase_button_code == request.DATA.get('order')['button']['id']:
#                     message = 'ERROR - Coinbase Callback: button code mismatch {}'
#                     raise APIException

#                 if not transaction.amount_gbp * 100 == request.DATA.get('order')['total_native']['cents']:
#                     message = 'ERROR - Coinbase Callback: native amount mismatch {}'
#                     raise APIException

#                 transaction.coinbase_order_reference = request.DATA.get('order')['id']
#                 transaction.amount_btc = request.DATA.get('order')['total_btc']['cents']
#                 transaction.set_paid(commit=False)

#                 send_sendgrid_mail(
#                     subject_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_SUBJECT,
#                     email_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_TEXT,
#                     context={
#                         'site': Site.objects.get_current(),
#                         'protocol': get_protocol()
#                     }
#                 )
#                 print 'yayy'

#             # received a mispayment, i.e. incorrect amount or too late
#             # in this case, a mispayment case mapped to a transaction must be created
#             elif request.DATA.get('order')['event']['type'] == 'mispayment':
#                 # TODO
#                 pass

#         except Transaction.DoesNotExist:
#             message = 'ERROR - Coinbase Callback: no transaction found for transaction id. {}'
#             log_error(message.format(request.DATA))
#         except (KeyError, TypeError, ValueError) as e:
#             message = 'ERROR - Coinbase Callback: received invalid payment notification, {}, {}'
#             log_error(message.format(e, request.DATA))
#         except APIException:
#             log_error(message.format(request.DATA))

#         # send status 200 in any case to stop coinbase from resending the request
#         return Response(status=status.HTTP_200_OK)
