from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import loader

from beam.utils.general import log_error

import sendgrid

# TODO: come up with unified way to send mails
# maybe custom backend?


def send_mail(subject_template_name, email_template_name,
              context, from_email, to_email, html_email_template_name=None):
    '''
    replica of the standard way of sending mail using Django required
    for rebuilding userena functionality for DRF
    '''

    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')

    email_message.send()


def send_sendgrid_mail(subject_template_name, email_template_name, context=None):
    '''
    standard way of sending mail using SendGridClient
    '''
    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    sg = sendgrid.SendGridClient(settings.SENDGRID_USERNAME, settings.SENDGRID_PASSWORD)

    recipients = User.objects.filter(is_staff=True)
    mails = [m.email for m in recipients]

    message = sendgrid.Mail()
    message.add_to(mails)
    message.set_from(settings.SENDGRID_EMAIL_FROM)
    message.set_subject(subject)
    message.set_text(body)

    try:
        sg.send(message)
    except sendgrid.SendGridError as e:
        log_error('ERROR - Sendgrid: Failed to send mail to admins ({})'.format(e))
