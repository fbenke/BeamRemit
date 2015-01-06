from beam.settings.production import *

# TODO: get domains of frontend app
ENV_SITE_MAPPING = {
    ENV_DEV: {
        SITE_API: 'simplepay-dev.herokuapp.com',
        SITE_USER: 'dev.simplepay4u.com',
    },
    ENV_PROD: {
        SITE_API: 'simplepay-prod.herokuapp.com',
        SITE_USER: 'simplepay4u.com',
    }
}

API_BASE_URL = PROTOCOL + '://' + ENV_SITE_MAPPING[ENV][SITE_API]
USER_BASE_URL = PROTOCOL + '://' + ENV_SITE_MAPPING[ENV][SITE_USER]

SITE_SENDING_CURRENCY = {
    0: (USD, EUR, GBP)
}

SITE_RECEIVING_CURRENCY = {
    0: NAIRA
}

SITE_RECEIVING_COUNTRY = {
    0: (NIGERIA,)
}

MULTIPLE_SITE_SUPPORT = False

TIME_ZONE = 'Africa/Lagos'

AWS_BUCKET_DEV = 'simplepayverification-dev'
AWS_BUCKET_PROD = 'simplepayverification'

# TODO: create whitelist
CORS_ORIGIN_ALLOW_ALL = True

# TODO: activate once we have valid domains of frontend apps
TOR_BLOCKING = False

COUNTRY_BLACKLIST = (
    # FATF Blacklist as of June 2014, see http://en.wikipedia.org/wiki/FATF_blacklist
    'IR',  # Iran
    'KP',  # North Korea
    'DZ',  # Algeria
    'EC',  # Ecuador
    'ID',  # Indonesia
    'MM'  # Myanmar
)

# TODO: replace with information provided by SP
BEAM_MAIL_ADDRESS = 'Simple Pay <hello@simplepay4u.com>'
DEFAULT_FROM_EMAIL = BEAM_MAIL_ADDRESS
BEAM_SUPPORT = 'hello@simplepay4u.com'

# TODO: replace with information provided by SP
MAIL_ACTIVATION_URL = '#!/auth/activate/{}/'
MAIL_EMAIL_CHANGE_CONFIRM_URL = '#!/settings/email/{}/'
MAIL_PASSWORD_RESET_URL = '#!/auth/forgot/{}-{}/'
MAIL_VERIFICATION_SITE = '#!/verify'
MAIL_TRANSACTION_HISTORY_SITE = '#!/history'

# TODO: replace with information provided by SP
GOCOIN_INVOICE_REDIRECT_SUFFIX = '/#!/send/complete/{}'
GOCOIN_PAYMENT_REDIRECT = {
    0: USER_BASE_URL + GOCOIN_INVOICE_REDIRECT_SUFFIX,
}
