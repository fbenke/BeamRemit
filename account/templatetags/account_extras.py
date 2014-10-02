from django import template

from django.conf import settings

register = template.Library()


def activation_link(activation_key):
    return settings.MAIL_ACTIVATION_URL.format(activation_key)

register.simple_tag(activation_link)


def password_reset_link(confirmation_key):
    return settings.MAIL_EMAIL_CHANGE_CONFIRM.format(confirmation_key)

register.simple_tag(password_reset_link)
