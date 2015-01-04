from beam.settings.production import *

ENV_SITE_MAPPING = {
    ENV_DEV: {
        SITE_API: 'simplepay-dev.herokuapp.com',
        SITE_USER: 'dev.simplepay.com',
    },
    ENV_PROD: {
        SITE_API: 'simplepay-prod.herokuapp.com',
        SITE_USER: 'simplepay.com',
    }
}

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

CORS_ORIGIN_ALLOW_ALL = True

BEAM_MAIL_ADDRESS = 'Simple Pay <hello@simplepay.com>'
DEFAULT_FROM_EMAIL = BEAM_MAIL_ADDRESS
BEAM_SUPPORT = 'hello@simplepay.com'

MAIL_ACTIVATION_URL = '#!/auth/activate/{}/'
MAIL_EMAIL_CHANGE_CONFIRM_URL = '#!/settings/email/{}/'
MAIL_PASSWORD_RESET_URL = '#!/auth/forgot/{}-{}/'
MAIL_VERIFICATION_SITE = '#!/verify'
MAIL_TRANSACTION_HISTORY_SITE = '#!/history'

GOCOIN_INVOICE_REDIRECT_SUFFIX = '/#!/send/complete/{}'
GOCOIN_PAYMENT_REDIRECT = {
    0: USER_BASE_URL + GOCOIN_INVOICE_REDIRECT_SUFFIX,
}
