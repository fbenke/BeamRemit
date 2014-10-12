from django.conf import settings

from boto.s3.connection import S3Connection


def generate_aws_url(method, key):

    conn = S3Connection(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY
    )

    url = conn.generate_url(
        settings.AWS_PRESIGNED_URL_VIEW_EXPIRATION,
        method,
        bucket=settings.AWS_BUCKET,
        key=key
    )

    return url


def generate_aws_upload(key, content_type):

    conn = S3Connection(
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY
    )

    conditions = '{"Content-Type": "%s"}' % content_type

    args = conn.build_post_form_args(
        settings.AWS_BUCKET,
        key,
        expires_in=settings.AWS_PRESIGNED_URL_UPLOAD_EXPIRATION,
        acl='private',
        max_content_length=settings.AWS_MAX_UPLOAD_SIZE,
        http_method=settings.PROTOCOL,
        conditions=[conditions]
    )

    upload_params = {'url': args['action']}

    for v in args['fields']:
        upload_params[v['name']] = v['value']

    del upload_params['x-amz-storage-class']
    del upload_params['acl']

    return upload_params


class AccountException(Exception):
    pass
