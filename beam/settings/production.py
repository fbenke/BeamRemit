import os

import dj_database_url

# Helpers

BASE_DIR = lambda *x: os.path.join(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)).
    replace('\\', '/'), *x)

DEBUG = bool(int(os.environ.get('DEBUG', '1')))

TEMPLATE_DEBUG = bool(int(os.environ.get('TEMPLATE_DEBUG', '1')))

SECRET_KEY = os.environ.get('SECRET_KEY')

ALLOWED_HOSTS = ['*']

# ENV names
ENV_LOCAL = 'local'
ENV_DEV = 'dev'
ENV_VIP = 'vip'
ENV_PROD = 'prod'

ENV = os.environ.get('ENV')

# Application definition
DJANGO_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
)

THIRD_PARTY_APPS = (
    'south',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'userena',
    'guardian',
    'easy_thumbnails',
)

LOCAL_APPS = (
    'beam',
    'state',
    'account',
    'pricing',
    'transaction',
    'btc_payment',
)


INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# SSL Redirects
if ENV != ENV_LOCAL:
    PROTOCOL = 'https'
    PRODUCTION_MIDDLEWARE = ('sslify.middleware.SSLifyMiddleware',)
else:
    PROTOCOL = 'http'
    # No automatic redirects on local
    PRODUCTION_MIDDLEWARE = ()

MIDDLEWARE_CLASSES = PRODUCTION_MIDDLEWARE + (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware'
)

# Site types in Env
SITE_API = 0
SITE_USER = 1
SITE_USER_SL = 2

# ENV to URL mapping
ENV_SITE_MAPPING = {
    ENV_LOCAL: {
        SITE_API: os.environ.get('LOCAL_SITE_API'),
        SITE_USER: os.environ.get('LOCAL_SITE_USER'),
        SITE_USER_SL: os.environ.get('LOCAL_SITE_USER_SL')
    },
    ENV_DEV: {
        SITE_API: 'api-dev.beamremit.com',
        SITE_USER: 'dev.beamremit.com',
        SITE_USER_SL: 'dev.bitcoinagainstebola.org'
    },
    ENV_VIP: {
        SITE_API: 'api-vip.beamremit.com',
        SITE_USER: 'vip.beamremit.com',
        SITE_USER_SL: 'bitcoinagainstebola.org'
    },
    ENV_PROD: {
        SITE_API: 'api.beamremit.com',
        SITE_USER: 'beamremit.com',
        SITE_USER_SL: 'bitcoinagainstebola.org'
    }
}

ROOT_URLCONF = 'beam.urls'

WSGI_APPLICATION = 'beam.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config()
}

# Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files
STATIC_ROOT = 'static'

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    BASE_DIR('assets'),
)

# Templates
TEMPLATE_DIRS = (
    BASE_DIR('templates'),
)

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
        }
    }
}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Django Rest Framework
REST_FRAMEWORK = {
    # if not specified otherwise, anyone can acess a view (this is the default)
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    # if required, which authentication is eligible?
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    # input formats the API can handle
    'DEFAULT_PARSER_CLASSES': (
        'beam.utils.parsers.CamelCaseJSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ),
    #  output formate supported by the API
    'DEFAULT_RENDERER_CLASSES': (
        'beam.utils.renderers.CamelCaseJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer'
    ),
    # throttling of requests
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '2/second'
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'TEST_REQUEST_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}


# Django CORS headers
if ENV == ENV_LOCAL:
    CORS_ORIGIN_ALLOW_ALL = True
else:
    CORS_ORIGIN_WHITELIST = (
        ENV_SITE_MAPPING[ENV][SITE_USER],
        ENV_SITE_MAPPING[ENV][SITE_USER_SL]
    )

# Base URLS for the apps
API_BASE_URL = PROTOCOL + '://' + ENV_SITE_MAPPING[ENV][SITE_API]
USER_BASE_URL = PROTOCOL + '://' + ENV_SITE_MAPPING[ENV][SITE_USER]
USER_BASE_URL_SL = PROTOCOL + '://' + ENV_SITE_MAPPING[ENV][SITE_USER_SL]

# Userena Settings
AUTHENTICATION_BACKENDS = (
    'userena.backends.UserenaAuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = 'account.BeamProfile'
USERENA_WITHOUT_USERNAMES = True
USERENA_ACTIVATION_DAYS = 1
USERENA_USE_HTTPS = (ENV != ENV_LOCAL)
# disable userena admin customizations to allow our own ones
USERENA_REGISTER_USER = False
USERENA_REGISTER_PROFILE = False
USERENA_HTML_EMAIL = True
ANONYMOUS_USER_ID = -1
# used whenever domain of frontend app does not matter
SITE_ID = 0

BEAM_MAIL_ADDRESS = 'Beam <hello@beamremit.com>'
DEFAULT_FROM_EMAIL = BEAM_MAIL_ADDRESS
BEAM_SUPPORT = 'hello@beamremit.com'

# Email Settings
if ENV in (ENV_LOCAL,):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'beam.utils.sendgrid_django.SendGridBackend'
    SENDGRID_USER = os.environ.get('SENDGRID_USER')
    SENDGRID_PASSWORD = os.environ.get('SENDGRID_PASSWORD')

# Email templates

# User Email templates
MAIL_ACTIVATION_SUBJECT = 'userena/emails/activation_email_subject.txt'
MAIL_ACTIVATION_TEXT = 'userena/emails/activation_email_message.txt'
MAIL_ACTIVATION_HTML = 'userena/emails/activation_email_message.html'
MAIL_PASSWORD_RESET_SUBJECT = 'userena/emails/password_reset_subject.txt'
MAIL_PASSWORD_RESET_TEXT = 'userena/emails/password_reset_message.txt'
MAIL_PASSWORD_RESET_HTML = 'userena/emails/password_reset_message.html'
MAIL_CHANGE_EMAIL_OLD_SUBJECT = 'userena/emails/confirmation_email_subject_old.txt'
MAIL_CHANGE_EMAIL_OLD_TEXT = 'userena/emails/confirmation_email_message_old.txt'
MAIL_CHANGE_EMAIL_OLD_HTML = 'userena/emails/confirmation_email_message_old.html'
MAIL_CHANGE_EMAIL_NEW_SUBJECT = 'userena/emails/confirmation_email_subject_new.txt'
MAIL_CHANGE_EMAIL_NEW_TEXT = 'userena/emails/confirmation_email_message_new.txt'
MAIL_CHANGE_EMAIL_NEW_HTML = 'userena/emails/confirmation_email_message_new.html'

MAIL_VERIFICATION_SUCCESSFUL_SUBJECT = 'email/user/verification_successful_subject.txt'
MAIL_VERIFICATION_SUCCESSFUL_TEXT = 'email/user/verification_successful_message.txt'
MAIL_VERIFICATION_SUCCESSFUL_HTML = 'email/user/verification_successful_message.html'
MAIL_VERIFICATION_FAILED_SUBJECT = 'email/user/verification_failed_subject.txt'
MAIL_VERIFICATION_FAILED_TEXT = 'email/user/verification_failed_message.txt'
MAIL_VERIFICATION_FAILED_HTML = 'email/user/verification_failed_message.html'
MAIL_TRANSACTION_COMPLETE_SUBJECT = 'email/user/transaction_complete_subject.txt'
MAIL_TRANSACTION_COMPLETE_TEXT = 'email/user/transaction_complete_message.txt'
MAIL_TRANSACTION_COMPLETE_HTML = 'email/user/transaction_complete_message.html'

# Admin Email templates
MAIL_NOTIFY_ADMIN_PAID_SUBJECT = 'email/admin/transaction_paid_subject.txt'
MAIL_NOTIFY_ADMIN_PAID_TEXT = 'email/admin/transaction_paid_message.txt'
MAIL_NOTIFY_ADMIN_PROBLEM_SUBJECT = 'email/admin/transaction_problem_subject.txt'
MAIL_NOTIFY_ADMIN_PROBLEM_TEXT = 'email/admin/transaction_problem_message.txt'
MAIL_NOTIFY_ADMIN_DOC_UPLOADED_SUBJECT = 'email/admin/doc_uploaded_subject.txt'
MAIL_NOTIFY_ADMIN_DOC_UPLOADED_TEXT = 'email/admin/doc_uploaded_message.txt'

# User-Facing URLs in Email templates
MAIL_ACTIVATION_URL = '#!/auth/activate/{}/'
MAIL_EMAIL_CHANGE_CONFIRM_URL = '#!/settings/email/{}/'
MAIL_PASSWORD_RESET_URL = '#!/auth/forgot/{}-{}/'
MAIL_VERIFICATION_SITE = '#!/verify'
MAIL_TRANSACTION_HISTORY_SITE = '#!/history'

# AWS Settings
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
AWS_PRESIGNED_URL_UPLOAD_EXPIRATION = 120
AWS_PRESIGNED_URL_VIEW_EXPIRATION = 3600
AWS_MAX_UPLOAD_SIZE = 5 * 1024 * 1024

AWS_BUCKET_DEV = 'beamverification-dev'
AWS_BUCKET_VIP = 'beamverification-vip'
AWS_BUCKET_PROD = 'beamverification'

ENV_BUCKET_MAPPING = {
    ENV_LOCAL: AWS_BUCKET_DEV,
    ENV_DEV: AWS_BUCKET_DEV,
    ENV_VIP: AWS_BUCKET_VIP,
    ENV_PROD: AWS_BUCKET_PROD,
}

AWS_BUCKET = ENV_BUCKET_MAPPING[ENV]

# Countries
GHANA = 'GH'
SIERRA_LEONE = 'SL'

# Currencies
USD = 'USD'
GBP = 'GBP'
LEONE = 'SLL'
CEDI = 'GHS'

COUNTRY_CURRENCY = {
    GHANA: CEDI,
    SIERRA_LEONE: LEONE
}

SITE_SENDING_CURRENCY = {
    0: GBP,
    1: USD
}

SITE_RECEIVING_CURRENCY = {
    0: CEDI,
    1: LEONE
}

SITE_RECEIVING_COUNTRY = {
    0: (GHANA,),
    1: (SIERRA_LEONE,)
}

# Payment Processors
PAYMENT_PROCESSOR = 'GoCoinInvoice'

# GoCoin Settings
# API Key with permission 'invoice_read_write'
GOCOIN_API_KEY = os.environ.get('GOCOIN_API_KEY')
GOCOIN_MERCHANT_ID = os.environ.get('GOCOIN_MERCHANT_ID')
GOCOIN_BASE_URL = 'https://api.gocoin.com/api/v1/'
GOCOIN_CREATE_INVOICE_URL = GOCOIN_BASE_URL + 'merchants/{}/invoices'.format(GOCOIN_MERCHANT_ID)
GOCOIN_INVOICE_CALLBACK_URL = API_BASE_URL + '/api/v1/btc_payment/gocoin/'
GOCOIN_INVOICE_REDIRECT_SUFFIX = '/#!/send/complete/{}'
GOCOIN_PAYMENT_REDIRECT = {
    GHANA: USER_BASE_URL + GOCOIN_INVOICE_REDIRECT_SUFFIX,
    SIERRA_LEONE: USER_BASE_URL_SL + GOCOIN_INVOICE_REDIRECT_SUFFIX
}

# IP-based blocking
COUNTRY_BLACKLIST = (
    'US',
    # FATF Blacklist as of June 2014, see http://en.wikipedia.org/wiki/FATF_blacklist
    'IR',  # Iran
    'KP',  # North Korea
    'DZ',  # Algeria
    'EC',  # Ecuador
    'ID',  # Indonesia
    'MM'  # Myanmar
)

TOR_TIMEOUT = 5

GEOIP_PATH = BASE_DIR('static', 'geo_data', 'GeoIP.dat')

# Bitcoin Against Ebola Specifics
CHARITIES = {'SLLG': '7554', 'LBG': '5275', 'Build on Books': '77879237'}
SPLASH_EMAIL = 'beam@splash-cash.com'
SPLASH_ONBOARD_RECIPIENT_SUBJECT = 'email/splash/oboard_recipient_subject.txt'
SPLASH_ONBOARD_RECIPIENT_TEXT = 'email/splash/oboard_recipient_message.txt'
SPLASH_DONATION_COMPLETE_TEXT = 'email/splash/donation_complete_message.txt'
SPLASH_DONATION_COMPLETE_HTML = 'email/splash/donation_complete_message.html'

