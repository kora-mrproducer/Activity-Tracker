import json
import zipfile
from io import BytesIO


def test_export_all_zip(client, sample_activity, sample_goal, sample_update):
    """Ensure /export/all returns a valid ZIP with expected files and manifest counts."""
    resp = client.get('/export/all')
    assert resp.status_code == 200
    assert resp.content_type.startswith('application/zip')

    zf = zipfile.ZipFile(BytesIO(resp.data))
    names = set(zf.namelist())
    expected = {
        'activity_tracker.db',
        'activities.csv','activities.json',
        'goals.csv','goals.json',
        'updates.csv','updates.json',
        'manifest.json'
    }
    for name in expected:
        assert name in names, f"Missing {name} in export ZIP"

    manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
    assert 'counts' in manifest
    assert manifest['counts']['activities'] >= 1
    assert manifest['counts']['goals'] >= 1
    assert manifest['counts']['updates'] >= 1

    # Basic sanity: CSV files have headers
    for csv_name in ['activities.csv','goals.csv','updates.csv']:
        content = zf.read(csv_name).decode('utf-8').splitlines()
        assert len(content) >= 1, f"{csv_name} unexpectedly empty"
