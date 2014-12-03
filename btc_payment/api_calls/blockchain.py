import requests

from django.conf import settings

from beam.utils.exceptions import APIException
from beam.utils.log import log_error


def generate_receiving_address(invoice_id):

    try:
        callback_url = settings.BLOCKCHAIN_INVOICE_CALLBACK_URL.format(invoice_id)

        payload = {
            'method': 'create',
            'address': settings.BLOCKCHAIN_DESTINATION_ADDRESS,
            'callback': callback_url
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
