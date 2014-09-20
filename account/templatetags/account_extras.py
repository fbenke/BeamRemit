from django import template

from django.conf import settings

register = template.Library()


def activation_link(activation_key):
    return settings.MAIL_ACTIVATION_URL.format(activation_key)

register.simple_tag(activation_link)
