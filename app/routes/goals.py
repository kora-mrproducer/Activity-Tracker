"""
Blueprint for goals management routes.
"""
from flask import current_app, Blueprint, request, redirect, url_for, flash, abort
from datetime import date, timedelta
from app import db
from app.models import Goal

goals_bp = Blueprint('goals', __name__, url_prefix='/goal')


@goals_bp.route('/add', methods=['POST'])
def add_goal():
    """Add a new weekly goal"""
    try:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Accept both 'text' and 'goal_text' for backward compatibility
        text_content = request.form.get('text') or request.form.get('goal_text', '')
        if not text_content.strip() or len(text_content.strip()) < 3:
            flash('Goal text is required (minimum 3 characters).', 'error')
            return redirect(url_for('activities.dashboard'))
        
        goal = Goal(
            text=text_content,
            week_of=start_of_week,
            is_complete=False
        )
        
        db.session.add(goal)
        db.session.commit()
        flash('Goal added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error adding goal')
        flash('Error adding goal. Please try again.', 'error')
    
    return redirect(url_for('activities.dashboard'))


@goals_bp.route('/toggle/<int:id>', methods=['POST'])
def toggle_goal(id):
    """Toggle goal completion status"""
    goal = db.session.get(Goal, id)
    if not goal:
        abort(404)
    try:
        goal.is_complete = not goal.is_complete
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error updating goal')
        flash('Error updating goal. Please try again.', 'error')
    
    return redirect(url_for('activities.dashboard'))
