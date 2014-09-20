import hmac
import hashlib


def generate_signature(message, key):
    return hmac.new(key, message, hashlib.sha256).hexdigest()
