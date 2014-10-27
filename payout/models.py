from django.conf import settings
from django.contrib.sites.models import Site
from django.utils import timezone

from beam.utils import mails


def post_paid(transaction):

    mails.send_mail(
        subject_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_SUBJECT,
        email_template_name=settings.MAIL_NOTIFY_ADMIN_PAID_TEXT,
        context={
            'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
            'protocol': settings.PROTOCOL,
            'id': transaction.id,
            'site_name': Site.objects.get_current().name
        },
        to_email=mails.get_admin_mail_addresses()
    )

    # Bitcoin Against Ebola Project Specifics
    if transaction.receiving_country == settings.SIERRA_LEONE and\
       transaction.recipient.phone_number not in settings.CHARITIES.values():

        mails.send_mail(
            subject_template_name=settings.SPLASH_ONBOARD_RECIPIENT_SUBJECT,
            email_template_name=settings.SPLASH_ONBOARD_RECIPIENT_TEXT,
            context={
                'txn_id': transaction.id,
                'timestamp': timezone.now(),
                'amount_sll': transaction.received_amount,
                'sender_first_name': transaction.sender.first_name,
                'sender_last_name': transaction.sender.last_name,
                'city': transaction.sender.profile.city,
                'country': transaction.sender.profile.country,
                'recipient_first_name': transaction.recipient.first_name,
                'recipient_last_name': transaction.recipient.last_name,
                'phone_number': transaction.recipient.phone_number,
            },
            to_email=settings.SPLASH_EMAIL
        )


def post_paid_problem(transaction):

    mails.send_mail(
        subject_template_name=settings.MAIL_NOTIFY_ADMIN_PROBLEM_SUBJECT,
        email_template_name=settings.MAIL_NOTIFY_ADMIN_PROBLEM_TEXT,
        context={
            'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
            'protocol': settings.PROTOCOL,
            'id': transaction.id,
            # TODO: decouple from specific payment provider
            'invoice_state': transaction.gocoin_invoice.state,
            'site_name': Site.objects.get_current().name
        },
        to_email=mails.get_admin_mail_addresses()
    )
