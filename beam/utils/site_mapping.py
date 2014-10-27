from django.contrib.sites.models import Site


def get_site_by_request(request):
    '''
    Simple Rewrite of the function models._get_site_by_request in Django 1.7
    https://github.com/django/django/blob/master/django/contrib/sites/models.py
    '''
    # TODO: After upgrade to Django 1.7 this should be solved directly byusing the Django Sites Framework
    host = request.get_host()
    return Site.objects.get(domain__iexact=host)
