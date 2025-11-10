"""
Blueprint for activity-related routes (CRUD operations).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from datetime import datetime, date, timezone, timedelta
from io import BytesIO
from app import db
from app.models import Activity, Update, Goal

activities_bp = Blueprint('activities', __name__)


@activities_bp.route('/')
def dashboard():
    """Main dashboard showing ongoing activities"""
    # Query all ongoing activities
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
        query = query.filter(Activity.blocking_points.isnot(None), Activity.blocking_points != '')
    
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
    start_of_week = today - timedelta(days=today.weekday())
    goals = Goal.query.filter_by(week_of=start_of_week).all()
    
    # Optimize: Load all updates in one query instead of N+1
    activity_ids = [a.id for a in activities]
    if activity_ids:
        all_updates = Update.query.filter(Update.activity_id.in_(activity_ids)).order_by(Update.created_at.desc()).all()
        activity_updates = {}
        for activity in activities:
            activity_updates[activity.id] = [u for u in all_updates if u.activity_id == activity.id][:2]
    else:
        activity_updates = {}
    
    # Get latest 10 updates across all activities with eager loading
    recent_updates = Update.query.options(db.joinedload(Update.activity)).join(Activity).filter(Activity.status != 'Closed').order_by(Update.created_at.desc()).limit(10).all()
    
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
    
    # Smart Suggestions - Optimized to avoid N+1 queries
    ongoing_activities = [a for a in all_activities if a.status == 'Ongoing']
    stale_activities = []
    long_running_activities = []
    
    # Get all latest updates in ONE query for ongoing activities
    if ongoing_activities:
        from sqlalchemy.sql import func
        activity_ids = [a.id for a in ongoing_activities]
        
        # Subquery to get max created_at per activity
        latest_updates_subq = db.session.query(
            Update.activity_id,
            func.max(Update.created_at).label('max_created')
        ).filter(Update.activity_id.in_(activity_ids)).group_by(Update.activity_id).subquery()
        
        # Join to get the actual Update records
        latest_updates = db.session.query(Update).join(
            latest_updates_subq,
            db.and_(
                Update.activity_id == latest_updates_subq.c.activity_id,
                Update.created_at == latest_updates_subq.c.max_created
            )
        ).all()
        
        # Build dictionary for O(1) lookups
        updates_dict = {u.activity_id: u for u in latest_updates}
    else:
        updates_dict = {}
    
    for activity in ongoing_activities:
        # Check if stale (no updates in 14+ days) - optimized lookup
        latest_update = updates_dict.get(activity.id)
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
    
    return render_template('dashboard.html', activities=activities, goals=goals, 
                          activity_updates=activity_updates, recent_updates=recent_updates,
                          dashboard_stats=dashboard_stats, smart_suggestions=smart_suggestions)


@activities_bp.route('/activities')
def all_activities():
    """Show all activities with full details"""
    # Query all activities (including closed)
    query = Activity.query
    
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
        query = query.filter(Activity.blocking_points.isnot(None), Activity.blocking_points != '')
    
    activities = query.all()
    
    # Sorting
    sort_by = request.args.get('sort', 'start_date')
    sort_dir = request.args.get('dir', 'desc')
    
    priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    
    if sort_by == 'start_date':
        activities.sort(key=lambda x: x.start_date if x.start_date else date.min, reverse=(sort_dir == 'desc'))
    elif sort_by == 'status':
        activities.sort(key=lambda x: x.status, reverse=(sort_dir == 'desc'))
    elif sort_by == 'priority':
        activities.sort(key=lambda x: priority_order.get(x.priority, 4), reverse=(sort_dir == 'desc'))
    elif sort_by == 'activity':
        activities.sort(key=lambda x: x.activity_desc.lower(), reverse=(sort_dir == 'desc'))
    
    # Get updates for each activity
    activity_updates = {}
    for activity in activities:
        updates = Update.query.filter_by(activity_id=activity.id).order_by(Update.created_at.desc()).all()
        activity_updates[activity.id] = updates
    
    return render_template('activities.html', activities=activities, activity_updates=activity_updates)


@activities_bp.route('/activity/<int:id>')
def activity_detail(id):
    """View detailed information about a specific activity"""
    activity = db.session.get(Activity, id)
    if not activity:
        abort(404)
    
    # Get all updates for this activity, ordered by most recent first
    updates = Update.query.filter_by(activity_id=id).order_by(Update.created_at.desc()).all()
    
    # Calculate activity stats
    days_active = (date.today() - activity.start_date).days if activity.start_date else 0
    update_count = len(updates)
    
    # Get latest update date
    latest_update_date = updates[0].created_at if updates else None
    
    # Days since last update
    if latest_update_date:
        days_since_update = (datetime.now(timezone.utc) - latest_update_date.replace(tzinfo=timezone.utc)).days
    else:
        days_since_update = days_active
    
    stats = {
        'days_active': days_active,
        'update_count': update_count,
        'days_since_update': days_since_update
    }
    
    return render_template('activity_detail.html', activity=activity, updates=updates, stats=stats)


@activities_bp.route('/add', methods=['GET', 'POST'])
def add_activity():
    """Add a new activity"""
    clone_source = None
    
    # Check if cloning an existing activity
    if request.method == 'GET' and request.args.get('clone'):
        clone_id = request.args.get('clone')
        clone_source = db.session.get(Activity, clone_id)
    
    if request.method == 'POST':
        try:
            # Validate required fields
            activity_desc = request.form.get('activity_desc', '').strip()
            if not activity_desc or len(activity_desc) < 3:
                flash('Activity description is required (minimum 3 characters).', 'error')
                return redirect(url_for('activities.add_activity'))
            
            # Parse dates
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = None
            if request.form.get('end_date'):
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            # Create new activity
            initial_obs = request.form.get('observations', '').strip() or request.form.get('initial_update', '').strip()
            activity = Activity(
                activity_desc=activity_desc,
                source=request.form.get('source', ''),
                start_date=start_date,
                end_date=end_date,
                blocking_points=request.form.get('blocking_points', ''),
                status=request.form.get('status', 'Ongoing'),
                observations=initial_obs,
                priority=request.form.get('priority', 'Medium'),
                tags=request.form.get('tags', '')
            )
            db.session.add(activity)
            db.session.commit()

            # Create initial update if observation provided
            if initial_obs:
                first_update = Update(
                    activity_id=activity.id,
                    text=initial_obs,
                    created_at=datetime.now(timezone.utc),
                    bp_snapshot=activity.blocking_points or ''
                )
                db.session.add(first_update)
                db.session.commit()
            
            flash('Activity added successfully!', 'success')
            return redirect(url_for('activities.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding activity: {str(e)}', 'error')
            return redirect(url_for('activities.add_activity'))
    
    return render_template('add_activity.html', clone_source=clone_source)


@activities_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_activity(id):
    """Edit an existing activity"""
    activity = db.session.get(Activity, id)
    if not activity:
        abort(404)
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
            
            # Handle closing note
            closing_note = request.form.get('closing_note', '').strip()
            if activity.status == 'Closed' and old_status != 'Closed':
                if closing_note:
                    closing_update_text = f"[CLOSED] {closing_note}"
                    upd = Update(activity_id=id, text=closing_update_text, created_at=datetime.now(timezone.utc))
                    activity.observations = closing_update_text
                    db.session.add(upd)
                elif not new_update:
                    flash('Please provide a closing note when marking activity as Closed.', 'error')
                    return redirect(url_for('activities.edit_activity', id=id))
            
            db.session.commit()
            flash('Activity updated successfully!', 'success')
            return redirect(url_for('activities.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating activity: {str(e)}', 'error')
            return redirect(url_for('activities.edit_activity', id=id))
    
    return render_template('edit_activity.html', activity=activity, updates=updates)


@activities_bp.route('/delete/<int:id>')
def delete_activity(id):
    """Delete an activity"""
    activity = db.session.get(Activity, id)
    if not activity:
        abort(404)
    try:
        db.session.delete(activity)
        db.session.commit()
        flash('Activity deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting activity: {str(e)}', 'error')
    
    return redirect(url_for('activities.dashboard'))


@activities_bp.route('/completed')
def completed():
    """View completed/closed activities"""
    activities = Activity.query.filter_by(status='Closed').order_by(Activity.end_date.desc()).all()
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


@activities_bp.route('/report', methods=['GET', 'POST'])
def report():
    """Generate custom date-range report"""
    activities = []
    start_date = None
    end_date = None
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        
        activities = Activity.query.filter(
            Activity.start_date >= start_date,
            Activity.start_date <= end_date
        ).order_by(Activity.start_date).all()
    
    return render_template('report.html', activities=activities, 
                          start_date=start_date, end_date=end_date)

@activities_bp.route('/report/pdf', methods=['POST'])
def report_pdf():
    """Generate a PDF version of the report for the provided date range.

    Accepts start_date and end_date via POST. Returns a PDF file attachment.
    Renders HTML and converts to PDF using xhtml2pdf (pure-Python, Windows friendly).
    """
    start_date_raw = request.form.get('start_date')
    end_date_raw = request.form.get('end_date')
    if not start_date_raw or not end_date_raw:
        abort(400, description='start_date and end_date are required')
    try:
        start_date_dt = datetime.strptime(start_date_raw, '%Y-%m-%d').date()
        end_date_dt = datetime.strptime(end_date_raw, '%Y-%m-%d').date()
    except ValueError:
        abort(400, description='Invalid date format. Use YYYY-MM-DD')

    activities = Activity.query.filter(
        Activity.start_date >= start_date_dt,
        Activity.start_date <= end_date_dt
    ).order_by(Activity.start_date).all()

    html = render_template('report_pdf.html', activities=activities, start_date=start_date_dt, end_date=end_date_dt)

    # Single engine: xhtml2pdf
    try:
        from xhtml2pdf import pisa
        pdf_io = BytesIO()
        result = pisa.CreatePDF(src=html, dest=pdf_io, encoding='UTF-8')
        if result.err:
            abort(500, description='Failed to generate PDF. reportlab barcode modules may be missing in the packaged app.')
        pdf_io.seek(0)
        filename = f"activity_report_{start_date_dt.strftime('%Y%m%d')}_{end_date_dt.strftime('%Y%m%d')}.pdf"
        return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name=filename)
    except (ImportError, ModuleNotFoundError) as e:
        # In packaged desktop app, PDF generation may fail due to missing reportlab modules
        # Provide user-friendly error message
        error_msg = ('PDF generation is not available in the desktop app due to missing dependencies. '
                    'Please use the web browser version (http://127.0.0.1:5000) for PDF exports, '
                    'or use the CSV/ZIP export options which work in both modes.')
        abort(500, description=error_msg)


@activities_bp.route('/activity/<int:id>/update', methods=['POST'])
def add_update(id):
    """Append a logged update to an activity"""
    try:
        activity = db.session.get(Activity, id)
        if not activity:
            abort(404)
        text = request.form.get('update_text', '').strip()
        new_bp = (request.form.get('blocking_points') or '').strip()
        
        if text:
            upd = Update(activity_id=id, text=text, created_at=datetime.now(timezone.utc))
            activity.observations = text
            
            if new_bp:
                activity.blocking_points = new_bp
            
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
    
    redirect_target = request.form.get('redirect')
    if redirect_target == 'dashboard':
        return redirect(url_for('activities.dashboard'))
    elif redirect_target == 'detail':
        return redirect(url_for('activities.activity_detail', id=id))
    return redirect(url_for('activities.edit_activity', id=id))


@activities_bp.route('/activity/<int:id>/status', methods=['POST'])
def update_status(id):
    """Update status inline from dashboard"""
    try:
        activity = db.session.get(Activity, id)
        if not activity:
            return jsonify({'ok': False, 'error': 'Activity not found'}), 404
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
        if new_status == 'Closed' and not activity.end_date:
            activity.end_date = date.today()
        
        # Create closing note update if provided
        if closing_note and new_status == 'Closed':
            closing_update_text = f"[CLOSED] {closing_note}"
            upd = Update(activity_id=id, text=closing_update_text, created_at=datetime.now(timezone.utc))
            activity.observations = closing_update_text
            db.session.add(upd)

        db.session.commit()
        return jsonify({
            'ok': True,
            'status': new_status,
            'end_date': activity.end_date.isoformat() if activity.end_date else None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@activities_bp.route('/activities/bulk/priority', methods=['POST'])
def bulk_update_priority():
    """Update priority for multiple activities at once"""
    try:
        data = request.get_json(silent=True) or {}
        activity_ids = data.get('activity_ids', [])
        new_priority = data.get('priority', '').strip()
        
        if not activity_ids or not isinstance(activity_ids, list):
            return jsonify({'ok': False, 'error': 'activity_ids must be a non-empty array'}), 400
        
        allowed_priorities = {'High', 'Medium', 'Low'}
        if new_priority not in allowed_priorities:
            return jsonify({'ok': False, 'error': 'Invalid priority. Must be High, Medium, or Low'}), 400
        
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
