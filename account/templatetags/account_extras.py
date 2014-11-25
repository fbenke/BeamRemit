from django import template

from account.utils import generate_aws_url

register = template.Library()


def aws_document_link(document_type, user_id):

    return generate_aws_url(
        method='GET',
        key='{}_{}'.format(document_type, user_id)
    )

register.simple_tag(aws_document_link)
