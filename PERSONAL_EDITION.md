# Activity Tracker Personal Edition

Activity Tracker is a single-user local application. Launch `python desktop_app.py`
from a Python 3.12 environment after installing `requirements.txt`. The server listens
only on 127.0.0.1. No account or hosting subscription is required.

## Windows package

The GitHub Actions workflow tests Linux and Windows, builds `ActivityTracker.spec`,
then checks startup and ZIP export from the actual executable. Download its Windows
artifact, extract the complete folder, and launch `ActivityTracker.exe`.
A successful build is required before treating the package as verified.

Bundled apps save the SQLite database, backups, logs and session key under
`%LOCALAPPDATA%/ActivityTracker`. Moving the executable does not move or erase data.
`ACTIVITY_TRACKER_DATA_DIR` overrides the data directory for testing or a portable setup.
Source launches use the project directory unless that override is set.

## Database and backups

Fresh installations apply the complete Alembic migration chain before serving requests.
Startup creates a verified SQLite backup and keeps the latest seven. ZIP exports use
SQLite's backup API, including committed WAL records. The export includes CSV and JSON
alongside a restorable database. Keep a separate copy of exports for disk failure recovery.
Unversioned pre-existing databases are not silently stamped; this release is intended for
the confirmed fresh installation. Do not use the repaired baseline to migrate an unknown
legacy database without reviewing its schema first.

## Behavior changes

Deletion uses a confirmation followed by a CSRF-protected POST. The row stays visible
until the server accepts deletion. Goal toggles also use protected POST requests.
Bulk close asks for one closing note and commits all selected activities together.
Bulk priority changes include CSRF protection. Analytics reflect current records,
with actual calendar months and no fabricated chart counts.
PWA caching covers static assets; dynamic pages and session tokens are never cached.
Everyday offline use means the local server runs without Internet access; the PWA does
not provide writes while that server is stopped.

Keep the service local. Authentication and public hosting are deferred to a later phase.
