from django.db import transaction as dbtransaction
from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.admin import TokenAdmin

from userena.admin import UserenaAdmin
from userena.utils import get_user_model, get_protocol

from beam.utils.mails import send_mail

from account import constants
from account import forms
from account.models import BeamProfile as Profile
from account.models import DocumentStatusChange


class DocumentStatusChangeInline(admin.TabularInline):
    model = DocumentStatusChange
    readonly_fields = ('changed_by', 'document_type', 'changed_at', 'changed_to', 'reason')
    extra = 0
    max_num = 10
    can_delete = False


class BeamProfileAdmin(admin.ModelAdmin):

    form = forms.ProfileModelForm

    def user_url(self, obj):
        path = settings.API_BASE_URL + '/admin/auth/user'
        return '<a href="{}/{}/">{}</a>'.format(path, obj.user.id, obj.user.id)
    user_url.allow_tags = True
    user_url.short_description = 'user'

    def user_email(self, obj):
        return obj.user.email

    def user_id(self, obj):
        return obj.user.id

    def user_name(self, obj):
        return '{} {}'.format(obj.user.first_name, obj.user.last_name)

    readonly_fields = (
        'user_url', 'user_email', 'user_name', 'date_of_birth',
        'street', 'post_code', 'city', 'country'
    )

    read_and_write_fields = (
        ('passport_state', 'passport_reason', 'send_passport_mail'),
        ('proof_of_residence_state', 'proof_of_residence_reason', 'send_proof_of_residence_mail')
    )

    fields = readonly_fields + read_and_write_fields

    list_display = ('user_email', 'country', 'city')

    list_display_links = ('user_email', )

    inlines = (DocumentStatusChangeInline, )

    def save_model(self, request, obj, form, change):

        with dbtransaction.atomic():

            changed_fields = list(set(Profile.DOCUMENT_FIELDS) & set(form.changed_data))

            for field in changed_fields:

                # create a record documenting the file change
                if getattr(obj, field) == Profile.FAILED:
                    reason = form.cleaned_data.get(form.DOCUMENT_FIELD[field][1])
                else:
                    reason = ''

                obj.update_document_state(
                    document=Profile.FIELD_DOCUMENT_MAPPING[field],
                    state=getattr(obj, field),
                    user=request.user.username,
                    reason=reason
                )

                # document was approved and user shall be notified
                if getattr(obj, field) == Profile.VERIFIED and\
                        form.cleaned_data.get(form.DOCUMENT_FIELD[field][0], None):

                    send_mail(
                        subject_template_name=settings.MAIL_VERIFICATION_SUCCESSFUL_SUBJECT,
                        email_template_name=settings.MAIL_VERIFICATION_SUCCESSFUL_TEXT,
                        context={
                            'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                            'protocol': get_protocol(),
                            'document': Profile.DOCUMENT_VERBAL[Profile.FIELD_DOCUMENT_MAPPING[field]],
                            'site': Site.objects.get_current(),
                            'support': settings.SENDGRID_EMAIL_FROM
                        },
                        from_email=settings.SENDGRID_EMAIL_FROM,
                        to_email=obj.user.email
                    )

                # document was rejected and user shall be notified
                elif getattr(obj, field) == Profile.FAILED and\
                        form.cleaned_data.get(form.DOCUMENT_FIELD[field][0], None):

                    send_mail(
                        subject_template_name=settings.MAIL_VERIFICATION_FAILED_SUBJECT,
                        email_template_name=settings.MAIL_VERIFICATION_FAILED_TEXT,
                        context={
                            'domain': settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_API],
                            'protocol': get_protocol(),
                            'document': Profile.DOCUMENT_VERBAL[Profile.FIELD_DOCUMENT_MAPPING[field]],
                            'site': Site.objects.get_current(),
                            'verification': settings.MAIL_VERIFICATION_SITE,
                            'support': settings.SENDGRID_EMAIL_FROM,
                            'reason': constants.REASON_VERBAL[reason]
                        },
                        from_email=settings.SENDGRID_EMAIL_FROM,
                        to_email=obj.user.email
                    )


admin.site.register(Profile, BeamProfileAdmin)


class DocumentStatusChangeAdmin(admin.ModelAdmin):

    def user(self, obj):
        return obj.profile.user.email

    readonly_fields = ('user', 'changed_by', 'document_type', 'changed_at', 'changed_to', 'reason')
    fields = readonly_fields
    list_display = ('user', 'changed_by', 'document_type', 'changed_at', 'changed_to', 'reason')
    list_filter = ('document_type', 'changed_at', 'changed_to', 'reason')

admin.site.register(DocumentStatusChange, DocumentStatusChangeAdmin)


class CustomUserenaAdmin(UserenaAdmin):

    list_display = ('id', 'email', 'is_staff', 'is_active', 'date_joined')
    list_display_links = ('id', 'email')


class CustomTokenAdmin(TokenAdmin):

    def user_email(self, obj):
        return obj.user.email

    def user_id(self, obj):
        return obj.user.id

    list_display = ('user_email', 'key', 'created')

    readonly_fields = ('user_id', 'user_email', 'key')
    fields = readonly_fields

try:
    admin.site.unregister(get_user_model())
except admin.sites.NotRegistered:
    pass
admin.site.register(get_user_model(), CustomUserenaAdmin)

try:
    admin.site.unregister(Token)
except admin.sites.NotRegistered:
    pass
admin.site.register(Token, CustomTokenAdmin)
