from django.conf import settings

from boto.s3.connection import S3Connection


def generate_aws_url(method, key, headers=None):

    if method == 'GET':
        expiration = settings.AWS_PRESIGNED_URL_VIEW_EXPIRATION
    else:
        expiration = settings.AWS_PRESIGNED_URL_UPLOAD_EXPIRATION

    conn = S3Connection(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY
    )

    url = conn.generate_url(
        expiration,
        method,
        bucket=settings.AWS_BUCKET,
        key=key,
        headers=headers
    )

    return url


class AccountException(Exception):
    pass
