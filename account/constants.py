# Error Status Codes
INVALID_PARAMETERS = '0'
PASSWORD_FORMAT = '1'
PASSWORD_MISMATCH = '2'
PASSWORD_OLD_INCORRECT = '3'
EMAIL_IN_USE = '4'
EMAIL_IN_USE_UNCONFIRMED = '5'
EMAIL_UNKNOWN = '5'
EMAIL_NOT_CHANGED = '6'
USER_NOT_FOUND = '7'
USER_ACCOUNT_DISABLED = '8'
ACTIVATION_KEY_INVALID = '9'
ACTIVATION_KEY_EXPIRED = '10'
ACTIVATION_KEY_NOT_EXPIRED = '11'
SIGNIN_WRONG_CREDENTIALS = '12'
SIGNIN_MISSING_CREDENTIALS = '13'
USER_ACCOUNT_ALREADY_ACTIVATED = '14'
DOCUMENT_ALREADY_UPLOADED = '15'
USER_PROFILE_INCOMPLETE = '16'

# Verbal Description of Error Status Codes
ERROR_MESSAGES = {
    INVALID_PARAMETERS: 'Invalid Parameters',
    PASSWORD_FORMAT: 'Password must be at least 8 characters long and contain at least one numeric character',
    PASSWORD_MISMATCH: 'The two password fields didn\'t match.',
    PASSWORD_OLD_INCORRECT: 'Old Password is incorrect',
    EMAIL_IN_USE: 'This email is already in use.',
    EMAIL_IN_USE_UNCONFIRMED: 'This email is already in use but not confirmed. Please check your email for verification steps.',
    EMAIL_UNKNOWN: 'Email unknown',
    EMAIL_NOT_CHANGED: 'Email has not been changed.',
    USER_NOT_FOUND: 'User not found.',
    USER_ACCOUNT_DISABLED: 'User account is disabled.',
    ACTIVATION_KEY_EXPIRED: 'Activation Key has expired',
    ACTIVATION_KEY_INVALID: 'Invalid Activation Key',
    ACTIVATION_KEY_NOT_EXPIRED: 'ActivationKey is not expired',
    SIGNIN_WRONG_CREDENTIALS: 'Unable to login with provided credentials.',
    SIGNIN_MISSING_CREDENTIALS: 'Must include "email" and "password"',
    USER_ACCOUNT_ALREADY_ACTIVATED: 'This account is is already activated.',
    DOCUMENT_ALREADY_UPLOADED: 'This document has already been uploaded.'
}

from account.models import DocumentStatusChange as d

REASON_VERBAL = {
    d.INVALID_PASSPORT: 'The document did not depict a password issued by your country.',
    d.CONTRADICTION: 'The profile information and documents were contradicting.',
    d.CREDIT_NOT_ACCEPTED: 'We cannot accept credit card statements as proof of residence.',
    d.MOBILE_NOT_ACCEPTED: 'We cannot accept mobile phone bills as proof of residence.',
    d.INVALID_FORMAT: 'The document has an invalid format.',
    d.LOW_RESOLUTION: 'The resolution is too low.',
    d.MISC: 'Something was wrong with the document. A member of the support team will contact you via email'
}
