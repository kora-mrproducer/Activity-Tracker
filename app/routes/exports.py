"""
Blueprint for data export routes.
"""
from flask import Blueprint, current_app, send_file, abort
from io import StringIO, BytesIO
import zipfile
import json
import csv
import os
from datetime import datetime, timezone
from app.models import Activity, Update, Goal

exports_bp = Blueprint('exports', __name__, url_prefix='/export')
@exports_bp.route('/all', methods=['GET'])
def export_all():
    """Bundle full data export into a single ZIP:
    - Raw SQLite database file
    - activities.csv
    - activities.json
    - goals.csv
    - goals.json
    - updates.csv
    - updates.json
    Returns ZIP as attachment.
    """
    # Locate DB file (instance path configured in app)
    # Derive physical SQLite file path. Prefer instance/tracker.db if present.
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    physical_path = None
    if db_uri.startswith('sqlite:///'):
        candidate = db_uri.replace('sqlite:///', '', 1)
        physical_path = candidate
    # Fallback to instance tracker.db (used elsewhere in app)
    inst_candidate = os.path.join(current_app.instance_path, 'tracker.db')
    if os.path.exists(inst_candidate):
        physical_path = inst_candidate
    if not physical_path or not os.path.exists(physical_path):
        # If file doesn't exist yet (fresh test DB), create it via create_all
        from app import db
        with current_app.app_context():
            db.create_all()
        if not physical_path or not os.path.exists(physical_path):
            abort(404, description='Database file not found.')

    # Query data
    activities = Activity.query.order_by(Activity.id).all()
    goals = Goal.query.order_by(Goal.id).all()
    updates = Update.query.order_by(Update.id).all()

    # Prepare in-memory ZIP
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Add raw DB
        zf.write(physical_path, arcname='activity_tracker.db')

        # Activities CSV
        act_csv_io = StringIO()
        act_writer = csv.writer(act_csv_io)
        act_writer.writerow(['id','activity_desc','source','start_date','end_date','blocking_points','status','observations','priority','tags','created_at','updated_at'])
        for a in activities:
            act_writer.writerow([
                a.id,
                a.activity_desc,
                a.source or '',
                a.start_date.isoformat() if a.start_date else '',
                a.end_date.isoformat() if a.end_date else '',
                a.blocking_points or '',
                a.status or '',
                a.observations or '',
                a.priority or '',
                a.tags or '',
                a.created_at.isoformat() if a.created_at else '',
                a.updated_at.isoformat() if a.updated_at else ''
            ])
        zf.writestr('activities.csv', act_csv_io.getvalue())

        # Activities JSON
        zf.writestr('activities.json', json.dumps([a.to_dict() for a in activities], indent=2))

        # Goals CSV
        goal_csv_io = StringIO()
        goal_writer = csv.writer(goal_csv_io)
        goal_writer.writerow(['id','text','week_of','is_complete'])
        for g in goals:
            goal_writer.writerow([
                g.id,
                g.text,
                g.week_of.isoformat() if g.week_of else '',
                int(g.is_complete)
            ])
        zf.writestr('goals.csv', goal_csv_io.getvalue())
        zf.writestr('goals.json', json.dumps([g.to_dict() for g in goals], indent=2))

        # Updates CSV
        upd_csv_io = StringIO()
        upd_writer = csv.writer(upd_csv_io)
        upd_writer.writerow(['id','activity_id','text','created_at','bp_snapshot'])
        for u in updates:
            upd_writer.writerow([
                u.id,
                u.activity_id,
                u.text,
                u.created_at.isoformat() if u.created_at else '',
                u.bp_snapshot or ''
            ])
        zf.writestr('updates.csv', upd_csv_io.getvalue())
        zf.writestr('updates.json', json.dumps([u.to_dict() for u in updates], indent=2))

        # Manifest file
        manifest = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'counts': {
                'activities': len(activities),
                'goals': len(goals),
                'updates': len(updates)
            },
            'files': [
                'activity_tracker.db',
                'activities.csv','activities.json',
                'goals.csv','goals.json',
                'updates.csv','updates.json'
            ]
        }
        zf.writestr('manifest.json', json.dumps(manifest, indent=2))

    zip_io.seek(0)
    filename = f"activity_tracker_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(zip_io, mimetype='application/zip', as_attachment=True, download_name=filename)


@exports_bp.route('/csv')
def export_csv():
    """Export all activities and updates to CSV file"""
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'Activity ID', 'Description', 'Source', 'Start Date', 'End Date',
        'Status', 'Priority', 'Blocking Points', 'Tags', 'Latest Observation',
        'Update Count', 'Latest Update Date'
    ])
    
    # Get all activities
    activities = Activity.query.order_by(Activity.start_date.desc()).all()
    
    for activity in activities:
        update_count = Update.query.filter_by(activity_id=activity.id).count()
        latest_update = Update.query.filter_by(activity_id=activity.id).order_by(Update.created_at.desc()).first()
        latest_update_date = latest_update.created_at.strftime('%Y-%m-%d %H:%M') if latest_update else ''
        
        writer.writerow([
            activity.id,
            activity.activity_desc,
            activity.source or '',
            activity.start_date.strftime('%Y-%m-%d') if activity.start_date else '',
            activity.end_date.strftime('%Y-%m-%d') if activity.end_date else '',
            activity.status,
            activity.priority,
            activity.blocking_points or '',
            activity.tags or '',
            activity.observations or '',
            update_count,
            latest_update_date
        ])
    
    # Prepare file for download
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    filename = f'activity_tracker_export_{timestamp}.csv'
    
    # Convert to bytes for send_file
    byte_output = BytesIO()
    byte_output.write(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    
    return send_file(
        byte_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )
