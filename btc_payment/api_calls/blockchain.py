import requests

from django.conf import settings

from beam.utils.exceptions import APIException
from beam.utils.log import log_error
from beam.utils.security import generate_signature


def generate_receiving_address(invoice_id):

    try:

        message = (settings.BLOCKCHAIN_DESTINATION_ADDRESS + str(invoice_id))

        signature = generate_signature(message, settings.BLOCKCHAIN_API_KEY)

        callback_url = settings.BLOCKCHAIN_INVOICE_CALLBACK_URL.format(invoice_id, signature)

        payload = {
            'method': 'create',
            'address': settings.BLOCKCHAIN_DESTINATION_ADDRESS,
            'callback': callback_url,
            'api_code': settings.BLOCKCHAIN_API_KEY
        }

        response = requests.get(
            settings.BLOCKCHAIN_CREATE_BTC_ADDRESS_URL,
            params=payload,
            timeout=settings.BLOCKCHAIN_TIMEOUT
        )
        response = response.json()

        # sanity checks
        if response['callback_url'].replace('\\', '') != callback_url:
            log_error('ERROR - Blockchain Generate Receive Address: Unexpected Callback URL {}, {}'.format(response['callback_url'], callback_url))

        if response['destination'] != settings.BLOCKCHAIN_DESTINATION_ADDRESS:
            log_error('ERROR - Blockchain Generate Receive Address: Unexpected Destination Address {}'.format(response['destination']))

        return response['input_address']

    except requests.RequestException as e:
        log_error('ERROR - Blockchain Generate Receive Address: Failed to send request {}'.format(repr(e)))

        raise APIException


def convert_to_btc(amount, currency):
    try:

        payload = {
            'value': amount,
            'currency': currency
        }

        response = requests.get(
            settings.BLOCKCHAIN_CONVERT_TO_BTC_URL,
            params=payload,
            timeout=settings.BLOCKCHAIN_TIMEOUT
        )

        return float(response.text)
    except requests.RequestException as e:
        log_error('ERROR - Blockchain Convert to Bitcoin: Failed to send request {}'.format(repr(e)))
        raise APIException

    except TypeError as e:
        log_error('ERROR - Blockchain Convert to Bitcoin: Unexpected Response {}'.format(repr(e)))
        raise APIException


