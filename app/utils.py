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


def backup_database(app, db):
    """Create a backup of the database file"""
    try:
        db_path = os.path.join(app.instance_path, 'tracker.db')
        if not os.path.exists(db_path):
            print("No database file found to backup")
            return
        
        # Create backups directory
        backup_dir = app.config.get('BACKUP_DIR', os.path.join(os.path.dirname(app.instance_path), 'backups'))
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_filename = f'tracker_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Verify backup integrity
        backup_size = os.path.getsize(backup_path)
        original_size = os.path.getsize(db_path)
        
        if backup_size < 1024:  # Less than 1KB
            os.remove(backup_path)
            raise Exception(f"Backup file suspiciously small ({backup_size} bytes). Deleted.")
        
        if abs(backup_size - original_size) > original_size * 0.1:  # More than 10% difference
            print(f"⚠ Warning: Backup size differs significantly from original ({backup_size} vs {original_size} bytes)")
        
        print(f"✓ Database backed up to: {backup_path} ({backup_size} bytes)")
        
        # Cleanup old backups
        cleanup_old_backups(backup_dir, app.config.get('BACKUP_KEEP_COUNT', 7))
        
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")


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
