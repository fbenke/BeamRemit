import json

from django.db import transaction as db_transaction
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from userena.utils import get_protocol

from beam.utils.general import log_error
from beam.utils.exceptions import APIException
from beam.utils.mails import send_sendgrid_mail
from beam.utils.security import generate_signature

from transaction.models import Transaction

from btc_payment.models import GoCoinInvoice


class ConfirmGoCoinPayment(APIView):

    def post(self, request):
        '''
        Payment callback from GoCoin, as described invoice_id
        see http://help.gocoin.com/kb/api-notifications/invoice-event-webhooks and
        http://help.gocoin.com/kb/api-invoices/invoice-states
        '''

        # retrieve transaction associated with this callback
        try:
            transaction = Transaction.objects.get(
                id=int(request.DATA.get('payload')['user_defined_1']),
                gocoin_invoice__invoice_id=request.DATA.get('payload')['id']
            )

            # check signature in webhook
            # see http://help.gocoin.com/kb/setup-integration/verify-webhook-authenticity-create-a-signature
            message = str(request.DATA.get('payload')['user_defined_1']) +\
                request.DATA.get('payload')['base_price'] + request.DATA.get('payload')['callback_url']
            signature = generate_signature(message, settings.GOCOIN_API_KEY)

            if request.DATA.get('payload')['user_defined_2'] != signature:
                raise APIException

            if request.DATA.get('event') == 'invoice_created':
                pass
            elif request.DATA.get('event') == 'invoice_payment_received':
                # full payment received, this includes overpaid
                if request.DATA.get('payload')['status'] == 'paid':

                    transaction.gocoin_invoice.btc_usd = request.DATA.get('payload')['inverse_spot_rate']
                    transaction.gocoin_invoice.sender_usd = request.DATA.get('payload')['usd_spot_rate']
                    transaction.gocoin_invoice.state = GoCoinInvoice.PAID

                    with db_transaction.atomic():
                        transaction.gocoin_invoice.save()
                        transaction.set_paid()

                    send_sendgrid_mail(
                        subject_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_SUBJECT,
                        email_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_TEXT,
                        context={
                            'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                            'protocol': get_protocol()
                        }
                    )
                # payment received, but does not fulfill the required amount
                elif request.DATA.get('payload')['status'] == 'underpaid':
                    transaction.gocoin_invoice.state = GoCoinInvoice.UNDERPAID
                    transaction.gocoin_invoice.save()
                else:
                    raise APIException

            # transaction has been confirmed
            elif request.DATA.get('event') == 'invoice_ready_to_ship'\
                    and request.DATA.get('payload')['status'] == 'ready_to_ship':
                transaction.gocoin_invoice.state = GoCoinInvoice.READY_TO_SHIP
                transaction.gocoin_invoice.save()

            # transaction requires manual intervention
            elif request.DATA.get('event') == 'invoice_merchant_review' or\
                    request.DATA.get('event') == 'invoice_invalid':

                if request.DATA.get('payload')['status'] == 'invalid':
                    transaction.gocoin_invoice.state = GoCoinInvoice.INVALID
                elif request.DATA.get('payload')['status'] == 'merchant_review':
                    transaction.gocoin_invoice.state = GoCoinInvoice.MERCHANT_REVIEW
                else:
                    raise APIException

                transaction.state = Transaction.INVALID

                with db_transaction.atomic():
                    transaction.gocoin_invoice.save()
                    transaction.set_invalid()

                send_sendgrid_mail(
                    subject_template_name=settings.MAIL_NOTIFY_ADMIN_PROBLEM_SUBJECT,
                    email_template_name=settings.MAIL_NOTIFY_ADMIN_PROBLEM_TEXT,
                    context={
                        'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                        'protocol': get_protocol(),
                        'id': transaction.id,
                        'invoice_state': transaction.gocoin_invoice.state
                    }
                )
            else:
                raise APIException

        except Transaction.DoesNotExist:
            message = 'ERROR - GoCoin Callback: no transaction found for transaction id. {}'
            log_error(message.format(json.dumps(request.DATA)))
        except (KeyError, TypeError, ValueError) as e:
            message = 'ERROR - GoCoin Callback: received invalid payment notification, {}, {}'
            log_error(message.format(e, json.dumps(request.DATA)))
        except APIException:
            message = 'ERROR - GoCoin Callback: received unexpected payment notification, {}'
            log_error(message.format(json.dumps(request.DATA)))
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
