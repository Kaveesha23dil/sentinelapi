from unittest.mock import Mock
import pytest
from simulate_threat_traffic import run


@pytest.mark.parametrize('url', ['https://example.com:8243/democommerceapi/1.0.0',
    'http://localhost:8243/democommerceapi/1.0.0', 'https://localhost:8243/other',
    'https://user@localhost:8243/democommerceapi/1.0.0'])
def test_local_only(url):
    client = Mock()
    with pytest.raises(ValueError):
        run(client, url, 'fixture', 'normal', lambda _: None)
    client.request.assert_not_called()


def test_bounded_requests_and_quota_stop():
    client = Mock()
    client.request.return_value = (200, None)
    result = run(client, 'https://localhost:8243/democommerceapi/1.0.0', 'fixture', 'normal', lambda _: None)
    assert len(result['requests']) == 24 and 'fixture' not in str(result)
    client.request.return_value = (429, None)
    assert len(run(client, 'https://localhost:8243/democommerceapi/1.0.0', 'fixture', 'error-rate', lambda _: None)['requests']) == 1
