from datetime import datetime
from uuid import UUID, uuid5


def event_id(flow, api_id):
    identity = '|'.join([str(UUID(flow['correlation_id'])),
                         datetime.fromisoformat(flow['timestamp']).isoformat(),
                         flow['method'], flow['endpoint']])
    return uuid5(UUID(api_id), identity)
