from django import template
from django.conf import settings

from account.utils import generate_aws_url

register = template.Library()


def activation_link(activation_key):
    return settings.MAIL_ACTIVATION_URL.format(activation_key)

register.simple_tag(activation_link)


def email_change_link(confirmation_key):
    return settings.MAIL_EMAIL_CHANGE_CONFIRM_URL.format(confirmation_key)

register.simple_tag(email_change_link)


def password_reset_link(uid, token):
    return settings.MAIL_PASSWORD_RESET_URL.format(uid, token)

register.simple_tag(password_reset_link)


def aws_document_link(document_type, user_id):

    return generate_aws_url(
        method='GET',
        key='{}_{}'.format(document_type, user_id)
    )

register.simple_tag(aws_document_link)
