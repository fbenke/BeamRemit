from beam.settings.production import *

# higher throttling rates for unit tests
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'anon': '100/second', }

# store mails in memory to access them ain unit tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
