"""Actual local WSO2 PatternLayout + inline BASIC JSON, with strict limits."""
import json
import re
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from .sanitizer import endpoint

PATTERN = re.compile(r'^\[([^]]+)\]\s+INFO \{API_LOG\} ([A-Za-z0-9_.-]+) - (\{.*\})$')
FLOWS = {'REQUEST_IN', 'REQUEST_OUT', 'RESPONSE_IN', 'RESPONSE_OUT'}
METHODS = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'}


def parse(line, config):
    if len(line) > 16384:
        return None
    try:
        match = PATTERN.fullmatch(line.rstrip('\r\n'))
        if not match or match[2] != config.api_name:
            return None
        data = json.loads(match[3])
        if not isinstance(data, dict) or data.get('flow') not in FLOWS or data.get('verb') not in METHODS:
            return None
        correlation = str(UUID(data['correlationId']))
        timestamp = datetime.strptime(match[1], '%Y-%m-%d %H:%M:%S,%f').replace(
            tzinfo=ZoneInfo(config.timezone)).isoformat()
        status = data.get('statusCode')
        if data['flow'].startswith('RESPONSE') and (type(status) is not int or not 100 <= status <= 599):
            return None
        # Drop every unknown field, including sourceIP, headers, cookies and bodies.
        return {'timestamp': timestamp, 'flow': data['flow'], 'correlation_id': correlation,
                'method': data['verb'], 'endpoint': endpoint(data['apiTo'], config.context, config.version),
                'status_code': status if data['flow'].startswith('RESPONSE') else None}
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return None
