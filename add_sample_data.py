"""Add sample data to the desktop app database for testing."""
import sys
import os
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Activity, Update

def add_sample_data():
    """Add sample activities to the database."""
    app = create_app('production')
    
    with app.app_context():
        # Check if we already have data
        count = Activity.query.count()
        if count > 0:
            print(f"Database already has {count} activities. Skipping.")
            return
        
        # Add sample activities
        activities = [
            Activity(
                activity_desc='Desktop App Testing - PDF Generation',
                source='Manual Test',
                start_date=(datetime.now() - timedelta(days=10)).date(),
                end_date=(datetime.now() - timedelta(days=2)).date(),
                status='Closed',
                priority='High',
                tags='testing, desktop, pdf',
                blocking_points='None'
            ),
            Activity(
                activity_desc='Feature: Auto-terminate Previous Instance',
                source='Development',
                start_date=(datetime.now() - timedelta(days=5)).date(),
                status='Ongoing',
                priority='High',
                tags='feature, enhancement',
                blocking_points='Testing in progress'
            ),
            Activity(
                activity_desc='Remove WeasyPrint Dependencies',
                source='Cleanup',
                start_date=(datetime.now() - timedelta(days=3)).date(),
                end_date=datetime.now().date(),
                status='Closed',
                priority='Medium',
                tags='cleanup, dependencies',
                blocking_points='None'
            ),
            Activity(
                activity_desc='PyInstaller Build Optimization',
                source='Development',
                start_date=(datetime.now() - timedelta(days=7)).date(),
                status='Ongoing',
                priority='Medium',
                tags='build, optimization',
                blocking_points='Need to verify hidden imports'
            ),
        ]
        
        for activity in activities:
            db.session.add(activity)
        
        db.session.commit()
        
        # Add some updates
        for activity in activities[:2]:
            update = Update(
                activity_id=activity.id,
                text=f'Progress update for {activity.activity_desc}',
                bp_snapshot=activity.blocking_points,
                timestamp=datetime.now()
            )
            db.session.add(update)
        
        db.session.commit()
        
        print(f"✓ Added {len(activities)} sample activities")
        print(f"✓ Database now has {Activity.query.count()} activities")
        
        # Show what was added
        print("\nSample activities:")
        for activity in Activity.query.all():
            print(f"  - {activity.activity_desc} ({activity.status})")

if __name__ == '__main__':
    add_sample_data()
