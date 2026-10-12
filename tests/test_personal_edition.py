"""Regression coverage for local access, protected mutations and durable data."""
import io
import re
import sqlite3
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from flask import abort
from sqlalchemy import inspect, text

from app import create_app, db
from app.models import Activity, Update
from app.utils import backup_database, initialize_database


@pytest.mark.parametrize('path', ['/', '/export/all', '/export/csv', '/health'])
def test_remote_requests_rejected(client, path):
    assert client.get(path, environ_overrides={'REMOTE_ADDR': '192.168.1.5'}).status_code == 403
    assert client.get(path, headers={'Host': 'attacker.example'}).status_code == 403
    assert client.get(path, headers={'Origin': 'https://attacker.example'}).status_code == 403
    assert client.get(path, headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403


def test_get_cannot_mutate(client, sample_activity, sample_goal, db_session):
    assert client.get(f'/delete/{sample_activity.id}').status_code == 405
    assert client.get(f'/goal/toggle/{sample_goal.id}').status_code == 405
    db_session.refresh(sample_goal)
    assert sample_goal.is_complete is False
    assert db_session.get(Activity, sample_activity.id) is not None


def test_real_csrf_required(app, client, sample_activity):
    with patch.dict(app.config, WTF_CSRF_ENABLED=True):
        assert client.post(f'/delete/{sample_activity.id}').status_code == 400
        assert client.post('/activities/bulk/priority', json={'activity_ids': [sample_activity.id], 'priority': 'Low'}).status_code == 400
        page = client.get('/').get_data(as_text=True)
        token = re.search(r'<meta name="csrf-token" content="([^"]+)"', page).group(1)
        response = client.post('/activities/bulk/priority', json={'activity_ids': [sample_activity.id], 'priority': 'Low'}, headers={'X-CSRFToken': token})
        assert response.status_code == 200


def test_bulk_close_atomic_and_validated(client, sample_activity, db_session):
    ids = [sample_activity.id]
    assert client.post('/activities/bulk/close', json={'activity_ids': ids}).status_code == 400
    assert client.post('/activities/bulk/close', json={'activity_ids': ids + [999999], 'closing_note': 'Done'}).status_code == 404
    db_session.refresh(sample_activity)
    assert sample_activity.status == 'Ongoing'
    response = client.post('/activities/bulk/close', json={'activity_ids': ids + ids, 'closing_note': 'Done'})
    assert response.get_json()['updated_count'] == 1
    db_session.refresh(sample_activity)
    assert sample_activity.status == 'Closed'
    assert sample_activity.end_date == date.today()
    assert db_session.query(Update).filter_by(activity_id=sample_activity.id).one().text == '[CLOSED] Done'
    assert client.post('/activities/bulk/close', json={'activity_ids': ids, 'closing_note': 'Again'}).get_json()['updated_count'] == 0


@pytest.mark.parametrize('ids', [[], [True], ['1'], [-1], [1.5]])
def test_bulk_ids_validated(client, ids):
    assert client.post('/activities/bulk/priority', json={'activity_ids': ids, 'priority': 'Low'}).status_code == 400


def test_export_contains_current_database(client, sample_activity, tmp_path):
    response = client.get('/export/all')
    with zipfile.ZipFile(io.BytesIO(response.data)) as bundle:
        snapshot = tmp_path / 'export.db'
        snapshot.write_bytes(bundle.read('activity_tracker.db'))
        with sqlite3.connect(snapshot) as conn:
            assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
            assert conn.execute('SELECT activity_desc FROM activities WHERE id=?', (sample_activity.id,)).fetchone()[0] == sample_activity.activity_desc


def test_fresh_migrations_and_wal_backup(monkeypatch, tmp_path):
    monkeypatch.setenv('ACTIVITY_TRACKER_DATA_DIR', str(tmp_path))
    application = create_app('production')
    with application.app_context():
        initialize_database(application, db)
        initialize_database(application, db)  # Restart is idempotent.
        assert {'activities', 'updates', 'goals', 'alembic_version'} <= set(inspect(db.engine).get_table_names())
        db.session.execute(text('PRAGMA journal_mode=WAL'))
        activity = Activity(activity_desc='Persisted in WAL', start_date=date.today())
        db.session.add(activity)
        db.session.commit()
        backup = backup_database(application, db)
        with sqlite3.connect(backup) as conn:
            assert conn.execute('SELECT activity_desc FROM activities').fetchone()[0] == 'Persisted in WAL'
        assert Path(application.instance_path).parent == tmp_path
    assert application.test_client().get('/').status_code == 200


def test_browser_500_page(monkeypatch, tmp_path):
    monkeypatch.setenv('ACTIVITY_TRACKER_DATA_DIR', str(tmp_path))
    application = create_app('production')
    @application.route('/forced-error')
    def forced_error():
        abort(500)
    response = application.test_client().get('/forced-error', headers={'Accept': 'text/html'})
    assert response.status_code == 500
    assert response.content_type.startswith('text/html')


def test_analytics_empty_and_calendar_months(client, db_session):
    with patch('app.routes.analytics.render_template', side_effect=lambda template, **kw: kw['stats']):
        stats = client.get('/analytics').get_json()
    assert stats['priority_low'] == 0
    assert len(set(stats['completion_months'])) == 6
    activity = Activity(activity_desc='Newly added', start_date=date.today())
    db_session.add(activity)
    db_session.commit()
    with patch('app.routes.analytics.render_template', side_effect=lambda template, **kw: kw['stats']):
        updated = client.get('/analytics').get_json()
    assert updated['total_activities'] == stats['total_activities'] + 1


def test_pwa_assets_and_sensitive_no_cache(client):
    assert client.get('/sw.js').status_code == 200
    for size in (192, 512):
        assert client.get(f'/static/icon-{size}.png').status_code == 200
    assert client.get('/health').headers['Cache-Control'] == 'no-store'
    assert 'db_uri' not in client.get('/health').get_json()

