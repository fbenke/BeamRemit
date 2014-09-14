import hashlib
import hmac
import urllib2
import time
import json

from django.conf import settings

from beam.utils import log_error


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
        log_error('ERROR - Coinbase: Failed to send request ({})'.format(repr(e)))
        return None


def generate_receive_address(reference_no=None):

    data = {
        'address': {
            'callback_url': settings.COINBASE_GENERATE_ADDRESS_CALLBACK_URL,
            'label': reference_no
        }
    }

    # POST /api/v1/buttons
    print make_request(settings.COINBASE_GENERATE_ADDRESS, body=json.dumps(data))
