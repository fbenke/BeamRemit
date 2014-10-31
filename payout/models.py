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


def post_processed(transaction):

    context = {
        'protocol': settings.PROTOCOL,
        'site': Site.objects.get_current(),
        'first_name': transaction.sender.first_name,
        'sent_amount': transaction.sent_amount,
        'sent_currency': transaction.sent_currency,
        'received_amount': transaction.received_amount,
        'received_currency': transaction.received_currency,
        'mobile': transaction.recipient.phone_number,
        'txn_history': settings.MAIL_TRANSACTION_HISTORY_SITE
    }

    # charities for bitcoinagainstebola project have a slightly different email
    if transaction.receiving_country == settings.SIERRA_LEONE and\
       transaction.recipient.phone_number in settings.CHARITIES.values():

        context['recipient'] = transaction.recipient.last_name

        mails.send_mail(
            subject_template_name=settings.MAIL_TRANSACTION_COMPLETE_SUBJECT,
            email_template_name=settings.SPLASH_DONATION_COMPLETE_TEXT,
            html_email_template_name=settings.SPLASH_DONATION_COMPLETE_HTML,
            context=context,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=transaction.sender.email
        )

    else:
        context['recipient'] = transaction.recipient.first_name

        mails.send_mail(
            subject_template_name=settings.MAIL_TRANSACTION_COMPLETE_SUBJECT,
            email_template_name=settings.MAIL_TRANSACTION_COMPLETE_TEXT,
            context=context,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_email=transaction.sender.email,
            html_email_template_name=settings.MAIL_TRANSACTION_COMPLETE_HTML
        )
