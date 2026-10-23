"""Allowlisted route templates. Never retain addresses, query values or payloads."""
import re
from urllib.parse import urlsplit

ROUTES = ['/health', '/api/v1/users/me', '/api/v1/orders', '/api/v1/payments/simulate']


def endpoint(value, context, version):
    if not isinstance(value, str) or len(value) > 4096:
        raise ValueError('Invalid target')
    path = urlsplit(value).path
    prefix = context + '/' + version
    if not path.startswith(prefix + '/'):
        raise ValueError('Different API context')
    path = path[len(prefix):]
    if path in ROUTES:
        return path
    if re.fullmatch(r'/api/v1/orders/[0-9]+', path):
        return '/api/v1/orders/{order_id}'
    return '/{unmapped}'
