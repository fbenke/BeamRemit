from beam.settings.production import *

REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = ({'anon': '100/second', })
