import re

from app import create_app


def test_testing_config_uses_memory_db():
    """Ensure the testing config keeps an in-memory SQLite DB and is not rewritten to a file.

    This protects the CI/test environment from the desktop relocation logic which should
    only affect file-based SQLite URIs.
    """
    app = create_app('testing')
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    # Allow either plain sqlite or sqlalchemy+pysqlite style prefixes that end in :memory:
    assert re.search(r":memory:", uri), f"Expected in-memory sqlite URI for testing, got: {uri}"


def test_health_endpoint_returns_ok(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data is not None
    # The health endpoint returns a small status payload; current key is 'ok' (boolean)
    assert json_data.get('ok') is True
