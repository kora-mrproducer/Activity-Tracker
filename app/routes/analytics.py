"""
Blueprint for analytics and timeline routes.
"""
from flask import Blueprint, render_template, request
from datetime import date, datetime, timezone, timedelta
from collections import Counter
from app.models import Activity, Update
from app import db

analytics_bp = Blueprint('analytics', __name__)

# Simple in-memory cache for analytics (expires after 5 minutes)
_analytics_cache = {'data': None, 'expires': None}


@analytics_bp.route('/analytics')
def analytics():
    """Analytics dashboard with comprehensive stats"""
    # Check cache first
    now = datetime.now(timezone.utc)
    if _analytics_cache['expires'] and now < _analytics_cache['expires']:
        return render_template('analytics.html', **_analytics_cache['data'])
    
    # Calculate fresh statistics
    today = date.today()
    
    # Basic counts - use SQL COUNT for better performance
    from sqlalchemy.sql import func
    
    total_activities = db.session.query(func.count(Activity.id)).scalar()
    ongoing_count = db.session.query(func.count(Activity.id)).filter(Activity.status == 'Ongoing').scalar()
    
    # Completion comparisons - use SQL queries
    first_day_this_month = today.replace(day=1)
    if today.month == 12:
        first_day_next_month = date(today.year + 1, 1, 1)
    else:
        first_day_next_month = today.replace(month=today.month + 1, day=1)
    
    completed_this_month = db.session.query(func.count(Activity.id)).filter(
        Activity.status == 'Closed',
        Activity.end_date >= first_day_this_month,
        Activity.end_date < first_day_next_month
    ).scalar()
    
    last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_month.replace(day=1)
    
    completed_last_month = db.session.query(func.count(Activity.id)).filter(
        Activity.status == 'Closed',
        Activity.end_date >= first_day_last_month,
        Activity.end_date < first_day_this_month
    ).scalar()
    
    # Average days to complete - still need to load closed activities for calculations
    # (Can't easily do date arithmetic in SQLite aggregations)
    closed_activities = Activity.query.filter(
        Activity.status == 'Closed',
        Activity.end_date.isnot(None),
        Activity.start_date.isnot(None)
    ).all()
    
    if closed_activities:
        avg_days = sum((a.end_date - a.start_date).days for a in closed_activities) / len(closed_activities)
        avg_days_to_complete = round(avg_days, 1)
        
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
    
    # Blocker stats - use SQL query
    blocker_count = db.session.query(func.count(Activity.id)).filter(
        Activity.status == 'Ongoing',
        Activity.blocking_points.isnot(None),
        Activity.blocking_points != ''
    ).scalar()
    blocker_percentage = round((blocker_count / ongoing_count * 100)) if ongoing_count > 0 else 0
    
    # Priority distribution - use SQL queries
    priority_high = db.session.query(func.count(Activity.id)).filter(Activity.priority == 'High').scalar()
    priority_medium = db.session.query(func.count(Activity.id)).filter(Activity.priority == 'Medium').scalar()
    priority_low = db.session.query(func.count(Activity.id)).filter(Activity.priority == 'Low').scalar()
    
    if priority_high == 0 and priority_medium == 0 and priority_low == 0:
        priority_low = 1  # Prevent empty chart
    
    # Status distribution - use SQL queries
    status_ongoing = ongoing_count  # Already calculated
    status_closed = db.session.query(func.count(Activity.id)).filter(Activity.status == 'Closed').scalar()
    status_na = db.session.query(func.count(Activity.id)).filter(Activity.status == 'NA').scalar()
    
    # For remaining calculations that need activity objects, load them
    all_activities = Activity.query.all()
    
    # Completion velocity (last 6 months)
    completion_months = []
    completion_counts = []
    for i in range(5, -1, -1):  # Approximate past 6 months (30-day chunks)
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_label = month_date.strftime('%b %Y')
        count = len([a for a in all_activities 
                    if a.status == 'Closed' and a.end_date and 
                    a.end_date.month == month_date.month and a.end_date.year == month_date.year])
        completion_months.append(month_label)
        completion_counts.append(count)
    
    # Ensure we have data for charts
    if not completion_months:
        completion_months = ['No Data']
        completion_counts = [0]
    
    # Tag cloud - still requires loading activities
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
    
    # Stale activities
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
    
    # Convert Activity objects to dictionaries for JSON serialization
    long_running_data = [
        {
            'id': a.id,
            'activity_desc': a.activity_desc,
            'days_running': a.days_running,
            'priority': a.priority
        }
        for a in long_running
    ]
    
    stale_activities_data = [
        {
            'id': a.id,
            'activity_desc': a.activity_desc,
            'days_since_update': a.days_since_update,
            'priority': a.priority
        }
        for a in stale_activities
    ]
    
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
        'long_running': long_running_data,
        'stale_activities': stale_activities_data
    }
    
    # Cache the template context for 5 minutes
    template_context = {
        'stats': stats,
        'long_running_activities': long_running,
        'stale_activities_list': stale_activities
    }
    _analytics_cache['data'] = template_context
    _analytics_cache['expires'] = now + timedelta(minutes=5)
    
    return render_template('analytics.html', **template_context)


@analytics_bp.route('/timeline')
def timeline():
    """Visual timeline view of all activities"""
    today = date.today()
    
    # Get filter params
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', '')
    range_days = request.args.get('range', '90')
    
    # Calculate date range
    if range_days == 'all':
        start_range = date(2020, 1, 1)
    else:
        start_range = today - timedelta(days=int(range_days))
    
    # Query activities
    query = Activity.query
    
    if status_filter != 'all':
        query = query.filter(Activity.status == status_filter)
    
    if priority_filter:
        query = query.filter(Activity.priority == priority_filter)
    
    query = query.filter(Activity.start_date >= start_range)
    activities = query.order_by(Activity.start_date).all()
    
    # Calculate timeline data
    if activities:
        earliest_date = min(a.start_date for a in activities)
        latest_date = max((a.end_date if a.end_date else today) for a in activities)
        total_days = (latest_date - earliest_date).days
        
        # Generate month labels
        months = []
        current_month = earliest_date.replace(day=1)
        while current_month <= latest_date:
            months.append(current_month.strftime('%b %y'))
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
            
            start_percent = (days_from_start / total_days * 100) if total_days > 0 else 0
            width_percent = (duration_days / total_days * 100) if total_days > 0 else 1
            width_percent = max(width_percent, 1)
            
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
