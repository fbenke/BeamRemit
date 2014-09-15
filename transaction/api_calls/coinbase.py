import hashlib
import hmac
import urllib2
import time
import json

from django.conf import settings

from beam.utils import log_error, APIException


def make_request(url, body=None):

    opener = urllib2.build_opener()
    # The nonce is a positive integer number that must increase with every request you make.
    nonce = int(time.time() * 1e6)
    # The ACCESS_SIGNATURE header is a HMAC-SHA256 hash of the nonce concatentated with the full URL
    # and body of the HTTP request, encoded using the API secret.
    message = str(nonce) + url + ('' if body is None else body)
    signature = hmac.new(settings.COINBASE_API_SECRET, message, hashlib.sha256).hexdigest()

    headers = {
        'ACCESS_KEY': settings.COINBASE_API_KEY,
        'ACCESS_SIGNATURE': signature,
        'ACCESS_NONCE': nonce,
        'Accept': 'application/json'
    }

    # POST request is made, if data is passed.
    if body:
        headers.update({'Content-Type': 'application/json'})
        req = urllib2.Request(url, data=body, headers=headers)
    else:
        req = urllib2.Request(url, headers=headers)

    try:
        response = opener.open(req)
        return json.load(response)
    except urllib2.HTTPError as e:
        log_error('ERROR - ' + 'Coinbase: Failed to send request ({})'.format(repr(e)))
        raise APIException()


def generate_button(price, name, transaction_id, currency='GBP',):

    # TODO: go through again and see if all are needed, as well as which ones should be in settings
    # see https://coinbase.com/api/doc/1.0/buttons.html for parameter description
    data = {
        'button': {
            'name': 'your remittance to {}'.format(name),
            'callback_url': settings.COINBASE_CALLBACK_URL,
            'price_string': str(price),
            'price_currency_iso': currency,
            'subscription': False,
            # default value, opposed to 'donation'
            'type': 'buy_now',
            # description that will be added to the users transaction notes
            'description': 'Beam - the cheapest, fastest way to send money to Ghana.',
            # custom parameter to match with database record
            'custom': str(transaction_id),
            # secure custom parameter from any manipulation
            'custom_secure': True,
        }
    }

    response = make_request(settings.COINBASE_GENERATE_BUTTON, body=json.dumps(data))

    try:

        if not response['success']:
            log_error('ERROR - ' + 'Coinbase: Creating button was not successful ({})'.format(response))
            raise APIException

        return response['button']['code']

    except KeyError:
        log_error('ERROR - ' + 'Coinbase: Creating button was not successful ({})'.format(response))
        raise APIException
