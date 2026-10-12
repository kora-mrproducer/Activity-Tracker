"""
Utility functions for the Activity Tracker application.
"""
from datetime import datetime, timezone
from sqlalchemy import text
import os
import shutil


def timeago_filter(dt):
    """Convert datetime to relative time string (e.g., '2h ago')"""
    if not dt:
        return ''
    
    now = datetime.now(timezone.utc)
    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes}m ago' if minutes > 1 else '1m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago' if hours > 1 else '1h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago' if days > 1 else '1d ago'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks}w ago' if weeks > 1 else '1w ago'
    else:
        months = int(seconds / 2592000)
        return f'{months}mo ago' if months > 1 else '1mo ago'


def ensure_update_bp_column(db):
    """Ensure updates table has bp_snapshot column (SQLite runtime migration)."""
    try:
        with db.engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(updates)")).fetchall()]
            if 'bp_snapshot' not in cols:
                conn.execute(text("ALTER TABLE updates ADD COLUMN bp_snapshot TEXT"))
                conn.commit()
    except Exception:
        # Best-effort; ignore if not possible
        pass


def sqlite_snapshot(db, destination):
    """Copy a consistent SQLite snapshot, including committed WAL contents."""
    import sqlite3
    from contextlib import closing
    source = db.engine.raw_connection()
    try:
        with closing(sqlite3.connect(str(destination))) as target:
            source.driver_connection.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Database backup failed integrity check')
    finally:
        source.close()


def backup_database(app, db):
    """Atomically publish a verified backup before pruning older backups."""
    import tempfile
    if db.engine.dialect.name != 'sqlite':
        raise RuntimeError('Personal Edition requires SQLite')
    backup_dir = app.config['BACKUP_DIR']
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    backup_path = os.path.join(backup_dir, f'tracker_backup_{timestamp}.db')
    fd, temporary = tempfile.mkstemp(dir=backup_dir, suffix='.tmp')
    os.close(fd)
    try:
        sqlite_snapshot(db, temporary)
        os.replace(temporary, backup_path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    cleanup_old_backups(backup_dir, app.config.get('BACKUP_KEEP_COUNT', 7))
    app.logger.info('Database backup completed')
    return backup_path


def initialize_database(app, db):
    """Apply versioned migrations; refuse to silently stamp an unknown schema."""
    from flask_migrate import upgrade
    upgrade(directory=app.config['MIGRATIONS_DIR'])


def cleanup_old_backups(backup_dir, keep_count=7):
    """Remove old backup files, keeping only the most recent ones"""
    try:
        backups = [f for f in os.listdir(backup_dir) if f.startswith('tracker_backup_') and f.endswith('.db')]
        backups.sort(reverse=True)  # Most recent first
        
        # Delete old backups
        for old_backup in backups[keep_count:]:
            os.remove(os.path.join(backup_dir, old_backup))
            print(f"✓ Cleaned up old backup: {old_backup}")
    except Exception as e:
        print(f"Warning: Could not cleanup old backups: {e}")
