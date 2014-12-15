import base64
import json
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils.timezone import utc

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from beam.utils.angular_requests import get_site_by_request
from beam.utils.exceptions import APIException
from beam.utils.log import log_error
from beam.utils.security import generate_signature

from transaction.models import Transaction

from btc_payment.api_calls import blockchain
from btc_payment.api_calls.coinapult import CoinapultClient, CoinapultError
from btc_payment.models import GoCoinInvoice, BlockchainPayment, BlockchainInvoice, CoinapultInvoice


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

            if request.QUERY_PARAMS['destination_address'] != settings.BLOCKCHAIN_DESTINATION_ADDRESS:

                message = 'ERROR - Blockchain Callback: destination addres does not match, {}'
                log_error(message.format(json.dumps(request.QUERY_PARAMS)))
                raise APIException

            message = request.QUERY_PARAMS['destination_address'] + request.QUERY_PARAMS['invoice_id'] +\
                request.QUERY_PARAMS['txn_id']

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

                    invoice = BlockchainInvoice.objects.get(btc_address=input_address, invoice_id=invoice_id)

                    payment = BlockchainPayment(
                        input_transaction_hash=input_transaction_hash,
                        forward_transaction_hash=forward_transaction_hash,
                        amount=amount
                    )

                    payment.invoice = invoice
                    payment.save()

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


class BlockchainPricing(APIView):

    def get(self, request):

        site = get_site_by_request(self.request)
        sending_currency = settings.SITE_SENDING_CURRENCY[site.id]
        btc_currency = blockchain.get_btc_exchange_rate(currency=sending_currency)
        return Response(data={'btc_currency': btc_currency, 'currency': sending_currency})


class ConfirmCoinapultPayment(APIView):

    def post(self, request):

        try:

            client = CoinapultClient(
                credentials={'key': settings.COINAPULT_API_KEY, 'secret': settings.COINAPULT_API_SECRET},
                authmethod='cred'
            )

            client.authenticateCallback(
                recvKey=request.META.get('HTTP_CPT_KEY'),
                recvSign=request.META.get('HTTP_CPT_HMAC'),
                recvData=request.DATA['data']
            )

            data = json.loads(base64.b64decode(request.DATA['data']))

            print data

            invoice = CoinapultInvoice.objects.get(
                invoice_id=data['transaction_id'],
                btc_address=data['address']
            )

            # sanity check
            if data['type'] != 'lock':
                raise APIException('Transaction is not of type \"lock\"')

            if data['state'] == 'confirming':

                invoice.state = CoinapultInvoice.PAID
                invoice.balance_due = float(data['in']['expected']) - float(data['in']['amount'])

                with db_transaction.atomic():
                    invoice.save()
                    invoice.transaction.set_paid()
                    invoice.transaction.post_paid()

            elif data['state'] == 'complete':

                invoice.state = CoinapultInvoice.READY_TO_SHIP
                invoice.completed_at = datetime.fromtimestamp((data['complete_time'])).replace(tzinfo=utc)
                invoice.save()

            elif data['state'] == 'canceled':

                invoice.balance_due = float(data['in']['expected']) - float(data['in']['amount'])

                # handle payment errors
                try:
                    errors = data['errors']
                    invoice.transaction.comments = invoice.transaction.comments + '\n' + errors
                    invoice.state = CoinapultInvoice.MERCHANT_REVIEW
                    with db_transaction.atomic():
                        invoice.save()
                        invoice.transaction.set_invalid()
                        invoice.transaction.post_paid_problem()

                # handle expired invoices
                except KeyError:
                    invoice.state = CoinapultInvoice.EXPIRED
                    invoice.save()

        except CoinapultError:
            message = 'ERROR - Coinapult Callback: Callback could not be authenticated, {}, {}, {}'
            log_error(message.format(request.META.get('HTTP_CPT_HMAC'), request.META.get('HTTP_CPT_KEY'), request.DATA['data']))

        except ObjectDoesNotExist:
            message = 'ERROR - Coinapult Callback: invoice not found, {}'
            log_error(message.format(data))

        except (KeyError, APIException) as e:
            message = 'ERROR - Coinapult Callback: received invalid payment notification, {}, {}'
            log_error(message.format(e, request.DATA))

        return Response()


class CoinapultPricing(APIView):

    def get(self, request):

        try:
            site = get_site_by_request(self.request)
            sending_currency = settings.SITE_SENDING_CURRENCY[site.id]
            market = '{}_BTC'.format(sending_currency)
            client = CoinapultClient()
            response = client.getTicker(filter="small,medium,large", market=market)
            data = {}
            data['small'] = response['small']['bid']
            data['medium'] = response['medium']['bid']
            data['large'] = response['large']['bid']
            data['market'] = response['market']
            return Response(data=data)

        except CoinapultError as e:

            message = 'ERROR - Coinapult Live Ticker: {}'
            log_error(message.format(e))

        except KeyError as e:

            message = 'ERROR - Coinapult Live Ticker: received invalid response, {}, {}'
            log_error(message.format(e, response))

        except APIException as e:

            message = 'ERROR - Coinapult Pricing failed to send request, {}'
            log_error(message.format(e))

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
