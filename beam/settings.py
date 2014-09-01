import os

import dj_database_url

# Helpers
BASE_DIR = lambda *x: os.path.join(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)).replace('\\', '/'), *x)

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
    'beam_user',
    'accounts',
)


INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# SSL Redirects
if ENV != ENV_LOCAL:
    PRODUCTION_MIDDLEWARE = ('sslify.middleware.SSLifyMiddleware',)
else:
    # No automatic redirects on local
    PRODUCTION_MIDDLEWARE = ()

MIDDLEWARE_CLASSES = PRODUCTION_MIDDLEWARE + (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
)

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

if ENV != ENV_LOCAL:
    throttling_rates = {'anon': '1/second', }
else:
    throttling_rates = {'anon': '100/second', }

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
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    #  output formate supported by the API
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # throttling of requests
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': (
        throttling_rates
    ),
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
        # TODO
        # ENV_SITE_MAPPING[ENV][SITE_ADMIN],
        # ENV_SITE_MAPPING[ENV][SITE_USER]
    )


# Site types in Env
SITE_API = 0
SITE_ADMIN = 1
SITE_USER = 2

# ENV to URL mapping
ENV_SITE_MAPPING = {
    ENV_LOCAL: {
        SITE_API: os.environ.get('LOCAL_SITE_API'),
        SITE_ADMIN: os.environ.get('LOCAL_SITE_ADMIN'),
        SITE_USER: os.environ.get('LOCAL_SITE_USER')
    },
    ENV_DEV: {
        SITE_API: 'api-dev.beamremit.com',
        SITE_ADMIN: 'admin-dev.beamremit.com',
        SITE_USER: 'dev.beamremit.com'
    },
    ENV_VIP: {
        SITE_API: 'api-vip.beamremit.com',
        SITE_ADMIN: 'admin-vip.beamremit.com',
        SITE_USER: 'vip.beamremit.com'
    },
    ENV_PROD: {
        SITE_API: 'api.beamremit.com',
        SITE_ADMIN: 'admin.beamremit.com',
        SITE_USER: 'beamremit.com'
    }
}


# AUTH_USER_MODEL = 'beam_user.BeamUser'

# Userena Settings
AUTHENTICATION_BACKENDS = (
    'userena.backends.UserenaAuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = 'accounts.BeamProfile'
USERENA_ACTIVATION_DAYS = 1
USERENA_USE_HTTPS = (ENV != ENV_LOCAL)

ANONYMOUS_USER_ID = -1
SITE_ID = 0

# TODO: remove soon
USERENA_SIGNIN_REDIRECT_URL = '/accounts/%(username)s/'
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'

# Email Settings
if ENV == ENV_LOCAL:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME')
    EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = 'noreply@beamremit.com'

# South Settings

# # assign migrations for third-party apps to project folders
# SOUTH_MIGRATION_MODULES = {
#     'sites': 'accounts.migrations',
# }
