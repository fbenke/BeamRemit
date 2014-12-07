import json

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction as db_transaction
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from beam.utils.exceptions import APIException
from beam.utils.log import log_error
from beam.utils.security import generate_signature

from transaction.models import Transaction

from btc_payment.models import GoCoinInvoice, BlockchainPayment, BlockchainInvoice


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

                transaction.gocoin_invoice.balance_due = request.DATA.get('payload')['crypto_balance_due']

                # full payment received, this includes overpaid
                if request.DATA.get('payload')['status'] == 'paid':

                    transaction.gocoin_invoice.state = GoCoinInvoice.PAID

                    with db_transaction.atomic():
                        transaction.gocoin_invoice.save()
                        transaction.set_paid()

                    transaction.post_paid()

                # payment received, but does not fulfill the required amount
                elif request.DATA.get('payload')['status'] == 'underpaid':

                    transaction.gocoin_invoice.state = GoCoinInvoice.UNDERPAID
                    transaction.gocoin_invoice.save()

                else:
                    raise APIException

            # transaction has been confirmed
            elif request.DATA.get('event') == 'invoice_ready_to_ship'\
                    and request.DATA.get('payload')['status'] == 'ready_to_ship':

                # special case payment was received late, but is confirmed now
                if transaction.state != Transaction.INVALID:
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

                transaction.post_paid_problem()

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


class ConfirmBlockchainPayment(APIView):

    def get(self, request):

        try:

            message = (request.QUERY_PARAMS['destination_address'] + request.QUERY_PARAMS['invoice_id'])

            signature = generate_signature(message, settings.BLOCKCHAIN_API_KEY)

            if request.QUERY_PARAMS['signature'] != signature:

                message = 'ERROR - Blockchain Callback: security param does not match, {}'
                log_error(message.format(json.dumps(request.QUERY_PARAMS)))
                raise APIException

            with db_transaction.atomic():

                # transaction hashes of payment and forwarding transaction, stored for logging purposes
                input_transaction_hash = request.QUERY_PARAMS['input_transaction_hash']
                forward_transaction_hash = request.QUERY_PARAMS['transaction_hash']

                # only handle payment when NUMBER_CONFIRMATIONS_REQUIRED is reached
                no_confirmations = int(request.QUERY_PARAMS['confirmations'])

                # get or create payment
                try:

                    payment = BlockchainPayment.objects.get(
                        input_transaction_hash=input_transaction_hash,
                        forward_transaction_hash=forward_transaction_hash
                    )

                except ObjectDoesNotExist:

                    # address generated by blockchain to receive payment
                    input_address = request.QUERY_PARAMS['input_address']
                    invoice_id = request.QUERY_PARAMS['invoice_id']

                    amount = float(request.QUERY_PARAMS['value']) / settings.BTC_SATOSHI

                    print input_address
                    print invoice_id

                    invoice = BlockchainInvoice.objects.get(btc_address=input_address, invoice_id=invoice_id)

                    print 'got here'
                    payment = BlockchainPayment(
                        input_transaction_hash=input_transaction_hash,
                        forward_transaction_hash=forward_transaction_hash,
                        amount=amount
                    )

                    payment.invoice = invoice
                    payment.save()

                    print 'second one'
                    # update balance of the corresponding invoice
                    invoice.update(payment)

                # handle payments confirmed by the blockchain
                if no_confirmations >= settings.BLOCKCHAIN_MIN_CONFIRMATIONS:

                    # set payment to confirmed
                    payment.state = BlockchainPayment.CONFIRMED
                    payment.save()

                    # check if entire invoice can be marked as "ready to ship"
                    payment.invoice.confirm()

                    # no need to send this callback again
                    return Response(data='*ok*', status=status.HTTP_200_OK)

                return Response()

        except KeyError as e:
            message = 'ERROR - Blockchain Callback: received unexpected payment notification, {}, {}'
            log_error(message.format(json.dumps(request.QUERY_PARAMS), format(repr(e))))

        except ObjectDoesNotExist:
            message = 'ERROR - Blockchain Callback: invoice not found, {}'
            log_error(message.format(json.dumps(request.QUERY_PARAMS)))

        except APIException:
            pass

        return Response(data='*ok*', status=status.HTTP_200_OK)
