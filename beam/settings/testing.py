from beam.settings.production import *

import logging

# higher throttling rates for unit tests
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'anon': '100/second', }

# store mails in memory to access them in unit tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

logging.disable(logging.CRITICAL)
