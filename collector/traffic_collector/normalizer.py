from datetime import datetime

from sentinelapi.db.schemas import EventInput
from .sanitizer import ROUTES
from .identity import event_id


def normalize(flow, config, service_id):
    if not isinstance(flow, dict):
        return None
    if flow.get('flow') != 'RESPONSE_OUT':
        return None
    if flow.get('endpoint') not in ROUTES + ['/api/v1/orders/{order_id}', '/{unmapped}']:
        raise ValueError('Non-template endpoint')
    # Completion time distinguishes a reused activity/correlation ID. Replays
    # retain the same source timestamp and produce the same UUID across rotation.
    timestamp = datetime.fromisoformat(flow['timestamp'])
    return EventInput(api_service_id=service_id, event_id=event_id(flow, config.api_id),
                      timestamp=timestamp, http_method=flow['method'], endpoint=flow['endpoint'],
                      status_code=flow['status_code'], client_identifier=None, latency_ms=None,
                      source='wso2-gateway')
