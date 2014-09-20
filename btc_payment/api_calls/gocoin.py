import json
import urllib2

from django.conf import settings

from beam.utils.general import log_error
from beam.utils.exceptions import APIException


# TODO: maybe merge with coinbase.make_request
def make_request(url, body=None):

    opener = urllib2.build_opener()

    headers = {
        'Authorization': 'Bearer ' + settings.GOCOIN_API_KEY
    }

    if body:
        headers.update({'Content-Type': 'application/json'})
        req = urllib2.Request(url, data=body, headers=headers)
    else:
        req = urllib2.Request(url, headers=headers)

    try:
        return opener.open(req)
    except urllib2.HTTPError as e:
        log_error('ERROR - ' + 'GoCoin: Failed to send request ({}: {})'.format(e.code, e.reason))
        raise APIException


def generate_invoice(price, reference_number, transaction_id, signature, currency='GBP'):

    # see http://help.gocoin.com/kb/api-invoices/creating-an-invoice
    data = {
        'price_currency': 'BTC',
        'base_price': price,
        'base_price_currency': currency,
        'callback_url': settings.GOCOIN_INVOICE_CALLBACK_URL,
        'redirect_url': settings.GOCOIN_INVOICE_REDIRECT_URL,
        'user_defined_1': transaction_id,
        'user_defined_2': signature,
    }

    response = make_request(settings.GOCOIN_CREATE_INVOICE_URL, body=json.dumps(data))

    data = json.load(response)

    try:

        result = {}
        result['invoice_id'] = data['id']
        result['amount_btc'] = data['price']
        result['btc_address'] = data['payment_address']

        return result

    except KeyError:
        log_error('ERROR - ' + 'Coinbase: Creating button was not successful ({})'.format(response))
        raise APIException
