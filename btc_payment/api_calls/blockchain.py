import requests


def generate_receiving_address():

    # TODO: move to settings later
    TIMEOUT = 15
    resource = 'https://blockchain.info/api/receive'
    destination_address = '1ENNEzMRVdNoC1ZdbPrTdU4z72UNuus1Uj'
    callback_url = 'https://dev.beamremit.com/api/v1/btc_payment/blockchain/'

    try:
        payload = {
            'method': 'create',
            'address': destination_address,
            'callback': callback_url
        }

        # response = requests.options(resource)
        # print response.text
        # print response.status_code

        response = requests.get(resource, params=payload, timeout=TIMEOUT)
        print response.url
        print response.text
        print response.status_code
        # return response.json()


        # {"callback_url":"https:\/\/dev.beamremit.com\/api\/v1\/btc_payment\/blockchain\/","input_address":"1GDLdmuYpCmiKyrd34yd7Qb75yWZfYDPPj","destination":"1ENNEzMRVdNoC1ZdbPrTdU4z72UNuus1Uj","fee_percent":0}

    except requests.RequestException as e:
        message = 'ERROR - ACCEPT (btc transfer request to blockchain): {}'.format(repr(e))
        print message
