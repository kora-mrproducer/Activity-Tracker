from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime, date, timezone
import os
import shutil
import csv
import secrets
import logging
from logging.handlers import RotatingFileHandler
from io import StringIO

# Initialize Flask app
app = Flask(__name__)

# Generate or load secret key
secret_key_file = os.path.join(os.path.dirname(__file__), '.secret_key')
if os.path.exists(secret_key_file):
    with open(secret_key_file, 'r') as f:
        app.config['SECRET_KEY'] = f.read().strip()
else:
    # Generate new secret key
    new_key = secrets.token_hex(32)
    app.config['SECRET_KEY'] = new_key
    # Save for future runs
    with open(secret_key_file, 'w') as f:
        f.write(new_key)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/activity_tracker.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Activity Tracker startup')

# Initialize database
db = SQLAlchemy(app)

# ==================== JINJA FILTERS ====================

@app.template_filter('timeago')
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

# ==================== DATABASE MODELS ====================

class Activity(db.Model):
    """Model for tracking activities/tasks"""
    __tablename__ = 'activities'
    __table_args__ = (
        db.Index('idx_status', 'status'),
        db.Index('idx_priority', 'priority'),
        db.Index('idx_start_date', 'start_date'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    activity_desc = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100))  # e.g., "BUM", "BUT/DCRA"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    blocking_points = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Ongoing')  # "Ongoing", "Closed", "NA"
    observations = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), default='Medium')  # "High", "Medium", "Low"
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags
    
    def __repr__(self):
        return f'<Activity {self.id}: {self.activity_desc[:30]}...>'
    
    def to_dict(self):
        """Convert activity to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'activity_desc': self.activity_desc,
            'source': self.source,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'blocking_points': self.blocking_points,
            'status': self.status,
            'observations': self.observations,
            'priority': self.priority,
            'tags': self.tags
        }


class Goal(db.Model):
    """Model for tracking weekly goals"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    week_of = db.Column(db.Date, nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Goal {self.id}: {self.text[:30]}...>'
    
    def to_dict(self):
        """Convert goal to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'text': self.text,
            'week_of': self.week_of.isoformat() if self.week_of else None,
            'is_complete': self.is_complete
        }


class Update(db.Model):
    """Model for storing logged updates (history) for activities"""
    __tablename__ = 'updates'

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Snapshot of blocking points at time of update (added via runtime migration if missing)
    bp_snapshot = db.Column(db.Text, nullable=True)

    activity = db.relationship('Activity', backref=db.backref('updates', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Update {self.id} for Activity {self.activity_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'text': self.text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ==================== ROUTES ====================

@app.route('/')
def dashboard():
    """Main dashboard showing ongoing activities"""
    from datetime import timedelta
    # Query all ongoing activities, sorted by priority
    priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    
    # Base query
    query = Activity.query.filter(Activity.status != 'Closed')
    
    # Apply filters from request args
    search = request.args.get('search', '').strip()
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            (Activity.activity_desc.like(search_pattern)) |
            (Activity.source.like(search_pattern)) |
            (Activity.blocking_points.like(search_pattern))
        )
    
    filter_priority = request.args.get('priority', '').strip()
    if filter_priority:
        query = query.filter(Activity.priority == filter_priority)
    
    filter_status = request.args.get('status', '').strip()
    if filter_status:
        query = query.filter(Activity.status == filter_status)
    
    has_blockers = request.args.get('has_blockers')
    if has_blockers:
        query = query.filter(Activity.blocking_points != None, Activity.blocking_points != '')
    
    activities = query.all()
    
    # Sorting
    sort_by = request.args.get('sort', 'priority')
    sort_dir = request.args.get('dir', 'asc')
    
    if sort_by == 'start_date':
        activities.sort(key=lambda x: x.start_date if x.start_date else date.min, reverse=(sort_dir == 'desc'))
    elif sort_by == 'status':
        activities.sort(key=lambda x: x.status or '', reverse=(sort_dir == 'desc'))
    else:  # priority
        activities.sort(key=lambda x: priority_order.get(x.priority, 4), reverse=(sort_dir == 'desc'))
    
    # Get current week's goals
    today = date.today()
    # Calculate start of week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    goals = Goal.query.filter_by(week_of=start_of_week).all()
    
    # Optimize: Load all updates in one query instead of N+1
    activity_ids = [a.id for a in activities]
    if activity_ids:
        all_updates = Update.query.filter(Update.activity_id.in_(activity_ids)).order_by(Update.created_at.desc()).all()
        # Group by activity_id and limit to 2 per activity
        activity_updates = {}
        for activity in activities:
            activity_updates[activity.id] = [u for u in all_updates if u.activity_id == activity.id][:2]
    else:
        activity_updates = {}
    
    # Get latest 10 updates across all activities for activity rail
    recent_updates = Update.query.join(Activity).filter(Activity.status != 'Closed').order_by(Update.created_at.desc()).limit(10).all()
    
    # Calculate dashboard stats
    all_activities = Activity.query.all()
    active_count = len([a for a in all_activities if a.status == 'Ongoing'])
    high_priority_count = len([a for a in all_activities if a.status == 'Ongoing' and a.priority == 'High'])
    blocker_count = len([a for a in all_activities if a.status == 'Ongoing' and a.blocking_points and a.blocking_points.strip()])
    
    # Calculate streak (consecutive days with updates)
    all_updates_sorted = Update.query.order_by(Update.created_at.desc()).all()
    streak_days = 0
    if all_updates_sorted:
        dates_with_updates = set()
        for upd in all_updates_sorted:
            update_date = upd.created_at.date() if upd.created_at.tzinfo else upd.created_at.replace(tzinfo=timezone.utc).date()
            dates_with_updates.add(update_date)
        
        # Count consecutive days backwards from today
        check_date = today
        while check_date in dates_with_updates:
            streak_days += 1
            check_date -= timedelta(days=1)
    
    # Updates this week
    updates_this_week = len([u for u in all_updates_sorted if (today - (u.created_at.date() if u.created_at.tzinfo else u.created_at.replace(tzinfo=timezone.utc).date())).days < 7])
    
    dashboard_stats = {
        'active_count': active_count,
        'high_priority_count': high_priority_count,
        'blocker_count': blocker_count,
        'streak_days': streak_days,
        'updates_this_week': updates_this_week
    }
    
    # Smart Suggestions: Stale and Long-Running Activities
    ongoing_activities = [a for a in all_activities if a.status == 'Ongoing']
    stale_activities = []
    long_running_activities = []
    
    for activity in ongoing_activities:
        # Check if stale (no updates in 14+ days)
        latest_update = Update.query.filter_by(activity_id=activity.id).order_by(Update.created_at.desc()).first()
        if latest_update:
            days_since = (datetime.now(timezone.utc) - latest_update.created_at.replace(tzinfo=timezone.utc)).days
        else:
            days_since = (today - activity.start_date).days
        
        if days_since >= 14:
            activity.days_since = days_since
            stale_activities.append(activity)
        
        # Check if long-running (30+ days)
        days_running = (today - activity.start_date).days
        if days_running >= 30:
            activity.days_running = days_running
            long_running_activities.append(activity)
    
    smart_suggestions = {
        'stale_activities': sorted(stale_activities, key=lambda a: a.days_since, reverse=True)[:5],
        'long_running': sorted(long_running_activities, key=lambda a: a.days_running, reverse=True)[:5]
    }
    
    return render_template('dashboard.html', activities=activities, goals=goals, activity_updates=activity_updates, recent_updates=recent_updates, dashboard_stats=dashboard_stats, smart_suggestions=smart_suggestions)


@app.route('/add', methods=['GET', 'POST'])
def add_activity():
    """Add a new activity"""
    clone_source = None
    
    # Check if cloning an existing activity
    if request.method == 'GET' and request.args.get('clone'):
        clone_id = request.args.get('clone')
        clone_source = Activity.query.get(clone_id)
    
    if request.method == 'POST':
        try:
            # Parse date strings to date objects
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = None
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            # Create new activity
            initial_obs = request.form.get('observations', '').strip()
            activity = Activity(
                activity_desc=request.form['activity_desc'],
                source=request.form.get('source', ''),
                start_date=start_date,
                end_date=end_date,
                blocking_points=request.form.get('blocking_points', ''),
                status=request.form.get('status', 'Ongoing'),
                observations=initial_obs,  # keep latest snapshot
                priority=request.form.get('priority', 'Medium'),
                tags=request.form.get('tags', '')
            )
            db.session.add(activity)
            db.session.commit()

            # If an initial observation was provided, also create the first Update entry
            if initial_obs:
                # Ensure bp_snapshot column exists
                ensure_update_bp_column()
                first_update = Update(activity_id=activity.id, text=initial_obs, created_at=datetime.now(timezone.utc), bp_snapshot=activity.blocking_points or '')
                db.session.add(first_update)
                db.session.commit()
            
            flash('Activity added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding activity: {str(e)}', 'error')
            return redirect(url_for('add_activity'))
    
    return render_template('add_activity.html', clone_source=clone_source)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_activity(id):
    """Edit an existing activity"""
    activity = Activity.query.get_or_404(id)
    # Load update history for display
    updates = Update.query.filter_by(activity_id=id).order_by(Update.created_at.desc()).all()
    
    if request.method == 'POST':
        try:
            old_status = activity.status
            
            # Update activity fields
            activity.activity_desc = request.form['activity_desc']
            activity.source = request.form.get('source', '')
            activity.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            
            if request.form.get('end_date'):
                activity.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            else:
                activity.end_date = None
            
            activity.blocking_points = request.form.get('blocking_points', '')
            activity.status = request.form.get('status', 'Ongoing')
            activity.priority = request.form.get('priority', 'Medium')
            activity.tags = request.form.get('tags', '')
            
            # Handle optional new update
            new_update = request.form.get('new_update', '').strip()
            if new_update:
                upd = Update(activity_id=id, text=new_update, created_at=datetime.now(timezone.utc))
                activity.observations = new_update
                db.session.add(upd)
            
            # If status changed to Closed and there's a closing note, auto-create an update
            closing_note = request.form.get('closing_note', '').strip()
            if activity.status == 'Closed' and old_status != 'Closed':
                if closing_note:
                    closing_update_text = f"[CLOSED] {closing_note}"
                    upd = Update(activity_id=id, text=closing_update_text, created_at=datetime.now(timezone.utc))
                    activity.observations = closing_update_text
                    db.session.add(upd)
                elif not new_update:
                    # If closing without a note or update, require one
                    flash('Please provide a closing note when marking activity as Closed.', 'error')
                    return redirect(url_for('edit_activity', id=id))
            
            db.session.commit()
            flash('Activity updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating activity: {str(e)}', 'error')
            return redirect(url_for('edit_activity', id=id))
    
    return render_template('edit_activity.html', activity=activity, updates=updates)


@app.route('/delete/<int:id>')
def delete_activity(id):
    """Delete an activity"""
    try:
        activity = Activity.query.get_or_404(id)
        db.session.delete(activity)
        db.session.commit()
        flash('Activity deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting activity: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/completed')
def completed():
    """View completed/closed activities"""
    activities = Activity.query.filter_by(status='Closed').order_by(Activity.end_date.desc()).all()
    # Precompute stats to avoid complex Jinja expressions
    today = date.today()
    total_completed = len(activities)
    high_count = sum(1 for a in activities if (a.priority == 'High'))
    this_month_count = sum(
        1 for a in activities
        if (a.end_date is not None and a.end_date.month == today.month and a.end_date.year == today.year)
    )
    return render_template(
        'completed.html',
        activities=activities,
        total_completed=total_completed,
        high_count=high_count,
        this_month_count=this_month_count
    )


@app.route('/report', methods=['GET', 'POST'])
def report():
    """Generate custom date-range report"""
    activities = []
    start_date = None
    end_date = None
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        
        # Query activities within date range
        activities = Activity.query.filter(
            Activity.start_date >= start_date,
            Activity.start_date <= end_date
        ).order_by(Activity.start_date).all()
    
    return render_template('report.html', activities=activities, 
                          start_date=start_date, end_date=end_date)


@app.route('/analytics')
def analytics():
    """Analytics dashboard with comprehensive stats"""
    from datetime import timedelta
    from collections import Counter
    
    today = date.today()
    
    # Basic counts
    all_activities = Activity.query.all()
    total_activities = len(all_activities)
    ongoing_count = len([a for a in all_activities if a.status == 'Ongoing'])
    
    # This month vs last month completions
    completed_this_month = len([a for a in all_activities 
                                if a.status == 'Closed' and a.end_date and 
                                a.end_date.month == today.month and a.end_date.year == today.year])
    
    last_month = today.replace(day=1) - timedelta(days=1)
    completed_last_month = len([a for a in all_activities 
                                if a.status == 'Closed' and a.end_date and 
                                a.end_date.month == last_month.month and a.end_date.year == last_month.year])
    
    # Average days to complete
    closed_activities = [a for a in all_activities if a.status == 'Closed' and a.end_date and a.start_date]
    if closed_activities:
        avg_days = sum((a.end_date - a.start_date).days for a in closed_activities) / len(closed_activities)
        avg_days_to_complete = round(avg_days, 1)
        
        # By priority
        high_closed = [a for a in closed_activities if a.priority == 'High']
        avg_days_high = round(sum((a.end_date - a.start_date).days for a in high_closed) / len(high_closed), 1) if high_closed else 0
        
        medium_closed = [a for a in closed_activities if a.priority == 'Medium']
        avg_days_medium = round(sum((a.end_date - a.start_date).days for a in medium_closed) / len(medium_closed), 1) if medium_closed else 0
        
        low_closed = [a for a in closed_activities if a.priority == 'Low']
        avg_days_low = round(sum((a.end_date - a.start_date).days for a in low_closed) / len(low_closed), 1) if low_closed else 0
    else:
        avg_days_to_complete = 0
        avg_days_high = 0
        avg_days_medium = 0
        avg_days_low = 0
    
    # Blocker stats
    blocker_count = len([a for a in all_activities if a.status == 'Ongoing' and a.blocking_points and a.blocking_points.strip()])
    blocker_percentage = round((blocker_count / ongoing_count * 100)) if ongoing_count > 0 else 0

    # Completion velocity (last 6 months)
    completion_months = []
    completion_counts = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_label = month_date.strftime('%b %Y')
        count = len([a for a in all_activities 
                    if a.status == 'Closed' and a.end_date and 
                    a.end_date.month == month_date.month and a.end_date.year == month_date.year])
        completion_months.append(month_label)
        completion_counts.append(count)
    
    # Priority distribution
    priority_high = len([a for a in all_activities if a.priority == 'High'])
    priority_medium = len([a for a in all_activities if a.priority == 'Medium'])
    priority_low = len([a for a in all_activities if a.priority == 'Low'])

    # Ensure we have data for charts (prevent errors with empty datasets)
    if not completion_months:
        completion_months = ['No Data']
        completion_counts = [0]

    if priority_high == 0 and priority_medium == 0 and priority_low == 0:
        # Prevent empty chart by assigning a placeholder category
        priority_low = 1
    
    # Status distribution
    status_ongoing = len([a for a in all_activities if a.status == 'Ongoing'])
    status_closed = len([a for a in all_activities if a.status == 'Closed'])
    status_na = len([a for a in all_activities if a.status == 'NA'])
    
    # Tag cloud
    all_tags = []
    for activity in all_activities:
        if activity.tags:
            tags = [t.strip() for t in activity.tags.split(',') if t.strip()]
            all_tags.extend(tags)
    tag_counter = Counter(all_tags)
    tag_counts = tag_counter.most_common(10)
    
    # Long running activities
    ongoing_activities = [a for a in all_activities if a.status == 'Ongoing']
    for activity in ongoing_activities:
        activity.days_running = (today - activity.start_date).days
    long_running = sorted(ongoing_activities, key=lambda a: a.days_running, reverse=True)[:5]
    
    # Stale activities (no updates in 14+ days)
    stale_activities = []
    for activity in ongoing_activities:
        latest_update = Update.query.filter_by(activity_id=activity.id).order_by(Update.created_at.desc()).first()
        if latest_update:
            days_since = (datetime.now(timezone.utc) - latest_update.created_at.replace(tzinfo=timezone.utc)).days
        else:
            days_since = (today - activity.start_date).days
        
        if days_since >= 14:
            activity.days_since_update = days_since
            stale_activities.append(activity)
    
    stale_activities = sorted(stale_activities, key=lambda a: a.days_since_update, reverse=True)
    
    stats = {
        'total_activities': total_activities,
        'ongoing_count': ongoing_count,
        'completed_this_month': completed_this_month,
        'completed_last_month': completed_last_month,
        'avg_days_to_complete': avg_days_to_complete,
        'avg_days_high_priority': avg_days_high,
        'avg_days_medium_priority': avg_days_medium,
        'avg_days_low_priority': avg_days_low,
        'blocker_count': blocker_count,
        'blocker_percentage': blocker_percentage,
        'completion_months': completion_months,
        'completion_counts': completion_counts,
        'priority_high': priority_high,
        'priority_medium': priority_medium,
        'priority_low': priority_low,
        'status_ongoing': status_ongoing,
        'status_closed': status_closed,
        'status_na': status_na,
        'tag_counts': tag_counts,
        'long_running': long_running,
        'stale_activities': stale_activities
    }
    
    return render_template('analytics.html', stats=stats)


@app.route('/timeline')
def timeline():
    """Visual timeline view of all activities"""
    from datetime import timedelta
    
    today = date.today()
    
    # Get filter params
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', '')
    range_days = request.args.get('range', '90')
    
    # Calculate date range
    if range_days == 'all':
        start_range = date(2020, 1, 1)  # Arbitrary early date
    else:
        start_range = today - timedelta(days=int(range_days))
    
    # Query activities
    query = Activity.query
    
    if status_filter != 'all':
        query = query.filter(Activity.status == status_filter)
    
    if priority_filter:
        query = query.filter(Activity.priority == priority_filter)
    
    # Filter by date range (activities that overlap with the range)
    query = query.filter(Activity.start_date >= start_range)
    
    activities = query.order_by(Activity.start_date).all()
    
    # Calculate timeline data
    if activities:
        # Find earliest and latest dates
        earliest_date = min(a.start_date for a in activities)
        latest_date = max((a.end_date if a.end_date else today) for a in activities)
        total_days = (latest_date - earliest_date).days
        
        # Generate month labels
        months = []
        current_month = earliest_date.replace(day=1)
        while current_month <= latest_date:
            months.append(current_month.strftime('%b %y'))
            # Move to next month
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        # Calculate bar positions and colors
        timeline_activities = []
        for activity in activities:
            end_date = activity.end_date if activity.end_date else today
            days_from_start = (activity.start_date - earliest_date).days
            duration_days = (end_date - activity.start_date).days
            
            # Calculate percentages
            start_percent = (days_from_start / total_days * 100) if total_days > 0 else 0
            width_percent = (duration_days / total_days * 100) if total_days > 0 else 1
            width_percent = max(width_percent, 1)  # Minimum width
            
            # Assign color based on priority
            color_map = {'High': '#ef4444', 'Medium': '#f59e0b', 'Low': '#10b981'}
            color = color_map.get(activity.priority, '#6b7280')
            
            timeline_activities.append({
                'id': activity.id,
                'activity_desc': activity.activity_desc,
                'start_date': activity.start_date.strftime('%Y-%m-%d'),
                'end_date': activity.end_date.strftime('%Y-%m-%d') if activity.end_date else 'Ongoing',
                'days_duration': duration_days,
                'start_percent': round(start_percent, 2),
                'width_percent': round(width_percent, 2),
                'color': color,
                'status': activity.status,
                'priority': activity.priority
            })
    else:
        months = []
        timeline_activities = []
    
    timeline_data = {
        'activities': timeline_activities,
        'months': months
    }
    
    return render_template('timeline.html', timeline_data=timeline_data)


@app.route('/goal/add', methods=['POST'])
def add_goal():
    """Add a new weekly goal"""
    try:
        from datetime import timedelta
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        goal = Goal(
            text=request.form['text'],
            week_of=start_of_week,
            is_complete=False
        )
        
        db.session.add(goal)
        db.session.commit()
        flash('Goal added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding goal: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/goal/toggle/<int:id>')
def toggle_goal(id):
    """Toggle goal completion status"""
    try:
        goal = Goal.query.get_or_404(id)
        goal.is_complete = not goal.is_complete
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating goal: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/activity/<int:id>/update', methods=['POST'])
def add_update(id):
    """Append a logged update to an activity"""
    try:
        activity = Activity.query.get_or_404(id)
        text = request.form.get('update_text', '').strip()
        # Optionally update blocking points if provided from quick update modal
        new_bp = (request.form.get('blocking_points') or '').strip()
        if text:
            # Ensure bp_snapshot column exists
            ensure_update_bp_column()
            upd = Update(activity_id=id, text=text, created_at=datetime.now(timezone.utc))
            # Keep the latest snapshot in activity.observations for quick access
            activity.observations = text
            # If user supplied new blocking points, persist them before taking the snapshot
            if new_bp:
                activity.blocking_points = new_bp
            # Capture snapshot of blocking points at the time of update
            try:
                upd.bp_snapshot = activity.blocking_points or ''
            except Exception:
                pass
            db.session.add(upd)
            db.session.commit()
            flash('Update added successfully!', 'success')
        else:
            flash('Update cannot be empty.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding update: {str(e)}', 'error')
    
    # Decide where to redirect (stay on dashboard for quick modal updates)
    redirect_target = request.form.get('redirect')
    if redirect_target == 'dashboard':
        return redirect(url_for('dashboard'))
    return redirect(url_for('edit_activity', id=id))


# Removed inline blocking points update per latest requirements


# ==================== BACKUP SYSTEM ====================

def backup_database():
    """Create a backup of the database file"""
    try:
        db_path = os.path.join(app.instance_path, 'tracker.db')
        if not os.path.exists(db_path):
            print("No database file found to backup")
            return
        
        # Create backups directory
        backup_dir = os.path.join(os.path.dirname(app.instance_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_filename = f'tracker_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        
        # Cleanup old backups (keep last 7)
        cleanup_old_backups(backup_dir, keep_count=7)
        
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


# ==================== CSV EXPORT ====================

@app.route('/export/csv')
def export_csv():
    """Export all activities and updates to CSV file"""
    try:
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
        output.seek(0)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f'activity_tracker_export_{timestamp}.csv'
        
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    flash('Page not found.', 'error')
    return redirect(url_for('dashboard'))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    flash('An unexpected error occurred. Please try again.', 'error')
    return redirect(url_for('dashboard'))


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        # ensure updates table has bp_snapshot column
        ensure_update_bp_column()
        print("Database initialized successfully!")


def ensure_update_bp_column():
    """Ensure updates table has bp_snapshot column (SQLite runtime migration)."""
    try:
        with db.engine.connect() as conn:
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(updates)")).fetchall()]
            if 'bp_snapshot' not in cols:
                conn.execute(text("ALTER TABLE updates ADD COLUMN bp_snapshot TEXT"))
    except Exception:
        # best-effort; ignore if not possible
        pass

@app.route('/activity/<int:id>/status', methods=['POST'])
def update_status(id):
    """Update status inline from dashboard."""
    try:
        activity = Activity.query.get_or_404(id)
        old_status = activity.status
        new_status = None
        closing_note = None
        
        if request.is_json:
            data = request.get_json(silent=True) or {}
            new_status = (data.get('status') or '').strip()
            closing_note = (data.get('closing_note') or '').strip()
        else:
            new_status = (request.form.get('status') or '').strip()
            closing_note = (request.form.get('closing_note') or '').strip()

        allowed = {'Ongoing', 'Closed', 'NA'}
        if new_status not in allowed:
            return jsonify({'ok': False, 'error': 'Invalid status'}), 400

        # Require closing note when changing to Closed
        if new_status == 'Closed' and old_status != 'Closed' and not closing_note:
            return jsonify({'ok': False, 'error': 'Closing note is required when marking activity as Closed'}), 400

        activity.status = new_status
        # Auto-set end_date if Closed and missing
        if new_status == 'Closed' and not activity.end_date:
            activity.end_date = date.today()
        
        # Create closing note update if provided
        if closing_note and new_status == 'Closed':
            closing_update_text = f"[CLOSED] {closing_note}"
            upd = Update(activity_id=id, text=closing_update_text, created_at=datetime.now(timezone.utc))
            activity.observations = closing_update_text
            db.session.add(upd)

        db.session.commit()
        return jsonify({'ok': True, 'status': new_status, 'end_date': activity.end_date.isoformat() if activity.end_date else None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/activities/bulk/priority', methods=['POST'])
def bulk_update_priority():
    """Update priority for multiple activities at once."""
    try:
        data = request.get_json(silent=True) or {}
        activity_ids = data.get('activity_ids', [])
        new_priority = data.get('priority', '').strip()
        
        # Validate
        if not activity_ids or not isinstance(activity_ids, list):
            return jsonify({'ok': False, 'error': 'activity_ids must be a non-empty array'}), 400
        
        allowed_priorities = {'High', 'Medium', 'Low'}
        if new_priority not in allowed_priorities:
            return jsonify({'ok': False, 'error': 'Invalid priority. Must be High, Medium, or Low'}), 400
        
        # Update in bulk
        updated_count = Activity.query.filter(Activity.id.in_(activity_ids)).update(
            {'priority': new_priority},
            synchronize_session=False
        )
        
        db.session.commit()
        
        return jsonify({
            'ok': True,
            'updated_count': updated_count,
            'priority': new_priority
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


# ==================== MAIN ====================
# Note: This app should be run via run.py or desktop_app.py which use Waitress production server.
# Direct execution is not recommended for production use.

if __name__ == '__main__':
    print("WARNING: Running Flask development server. For production, use run.py or desktop_app.py instead.")
    # Ensure database tables exist (creates missing tables without destroying data)
    init_db()
    
    # Create automatic backup on startup
    backup_database()
    
    app.run(host='127.0.0.1', port=5000, debug=True)
