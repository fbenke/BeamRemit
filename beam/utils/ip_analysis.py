import DNS

from django.conf import settings
from django.contrib.gis.geoip import GeoIP

from beam.utils.log import log_error
from beam.utils.angular_requests import get_country_blacklist_by_request

HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS = 451


def get_client_ip(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_default_currency(request):

    if settings.ENV == settings.ENV_LOCAL:
        return None

    ip_address = get_client_ip(request)

    g = GeoIP()

    country = g.country(ip_address)['country_code']

    try:
        return settings.COUNTRY_CURRENCY[country]

    except KeyError:
        return None


def country_blocked(request):

    if settings.ENV == settings.ENV_LOCAL:
        return False

    ip_address = get_client_ip(request)

    blocked_countries = get_country_blacklist_by_request(request)

    g = GeoIP()

    return g.country(ip_address)['country_code'] in blocked_countries


def is_tor_node(request):

    if settings.ENV == settings.ENV_LOCAL or not settings.TOR_BLOCKING:
        return False

    ip_address = get_client_ip(request)

    return is_using_tor(ip_address)


def is_using_tor(clientIp, ELPort='80'):
    '''
    Find out if clientIp is a tor exit node following query type one.
    Inspired by https://svn.torproject.org/svn/check/trunk/cgi-bin/TorCheck.py
    Query Specification under https://gitweb.torproject.org/tordnsel.git/blob/HEAD:/doc/torel-design.txt
    See also https://check.torproject.org/
    '''

    DNS.DiscoverNameServers()

    # Put user ip in right format
    splitIp = clientIp.split('.')
    splitIp.reverse()
    ELExitNode = '.'.join(splitIp)

    # get beam's current ip address
    name = settings.ENV_SITE_MAPPING[settings.ENV][settings.SITE_USER]
    ElTarget = DNS.dnslookup(name, 'A')

    # ExitList DNS server we want to query
    ELHost = 'ip-port.exitlist.torproject.org'

    # Prepare the question as an A record (i.e. a 32-bit IPv4 address) request
    ELQuestion = ELExitNode + "." + ELPort + "." + ElTarget[1] + "." + ELHost
    request = DNS.DnsRequest(name=ELQuestion, qtype='A', timeout=settings.TOR_TIMEOUT)

    # Ask the question and load the data into our answer
    try:
        answer = request.req()
    except DNS.DNSError as e:
        log_error('ERROR Tor - Failed to query ip address: {}'.format(e[0]))
        return False

    # Parse the answer and decide if it's allowing exits
    # 127.0.0.2 is an exit and NXDOMAIN is not
    if answer.header['status'] == 'NXDOMAIN':
        return False
    else:
        # unexpected response
        if not answer.answers:
            log_error('ERROR Tor - Query returned unexpected response')
            return False
        for a in answer.answers:
            if a['data'] != '127.0.0.2':
                return False
        return True
