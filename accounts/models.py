from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

from userena.models import UserenaBaseProfile


class BeamProfile(UserenaBaseProfile):
    user = models.OneToOneField(
        User,
        unique=True,
        related_name='beam'
    )
    favourite_snack = models.CharField(
        _('favourite snack'),
        max_length=5
    )


# class BeamSignup(UserenaSignup):

#     def send_activation_email(self):
#         '''
#         Sends a activation email to the user using sendgrid.
#         Basically modifies the userna method using sendgrid and a customizd message
#         '''
#         context = {
#             'user': self.user,
#             'without_usernames': userena_settings.USERENA_WITHOUT_USERNAMES,
#             'protocol': get_protocol(),
#             'activation_days': userena_settings.USERENA_ACTIVATION_DAYS,
#             'activation_key': self.activation_key,
#             'site': Site.objects.get_current()
#         }

#         # uses the default userena subject
#         subject = render_to_string(
#             'userena/emails/activation_email_subject.txt',
#             context
#         )
#         subject = ''.join(subject.splitlines())

#         message_html = render_to_string(
#             'userena/emails/activation_email_message.html',
#             context
#         )

#         message = None

#         send_mail(subject,
#                   message,
#                   message_html,
#                   settings.DEFAULT_FROM_EMAIL,
#                   [self.user.email, ])

# def send_mail_to_admins(subject, body):

#     sg = sendgrid.SendGridClient(SENDGRID_USERNAME, SENDGRID_PASSWORD)

#     recipients = User.objects.filter(is_staff=True)
#     mails = [m.email for m in recipients]

#     message = sendgrid.Mail()
#     message.add_to(mails)
#     message.set_from(SENDGRID_EMAIL_FROM)
#     message.set_subject(subject)
#     message.set_text(body)

#     try:
#         sg.send(message)
#     except sendgrid.SendGridError as e:
#         log_error('ERROR - Sendgrid: Failed to send mail to admins ({})'.format(e))
#         pass
