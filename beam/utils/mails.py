from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template import loader


def send_mail(subject_template_name, email_template_name, context, to_email,
              html_email_template_name=None, from_email=settings.BEAM_MAIL_ADDRESS):

    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    if not isinstance(to_email, list):
        to_email = [to_email]

    print from_email
    email_message = EmailMultiAlternatives(subject, body, from_email, to_email)
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')

    email_message.send()


def get_admin_mail_addresses():
    recipients = User.objects.filter(is_staff=True)
    return [m.email for m in recipients]
