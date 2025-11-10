"""
Blueprint for search functionality.
"""
from flask import Blueprint, jsonify, request
from app.models import Activity

search_bp = Blueprint('search', __name__)


@search_bp.route('/search')
def search_activities():
    """Full-text search across all activity fields"""
    query_str = request.args.get('q', '').strip()
    
    if not query_str or len(query_str) < 2:
        return jsonify([])
    
    # Build search pattern
    search_pattern = f'%{query_str}%'
    
    # Search across multiple fields (case-insensitive)
    results = Activity.query.filter(
        (Activity.activity_desc.ilike(search_pattern)) |
        (Activity.tags.ilike(search_pattern)) |
        (Activity.blocking_points.ilike(search_pattern)) |
        (Activity.observations.ilike(search_pattern)) |
        (Activity.source.ilike(search_pattern))
    ).order_by(
        # Prioritize ongoing activities
        Activity.status.desc(),
        # Then by priority
        Activity.priority.desc(),
        # Then by recency
        Activity.start_date.desc()
    ).limit(20).all()
    
    # Convert to JSON-serializable format
    return jsonify([{
        'id': a.id,
        'desc': a.activity_desc[:100] + ('...' if len(a.activity_desc) > 100 else ''),
        'status': a.status,
        'priority': a.priority,
        'start_date': a.start_date.isoformat() if a.start_date else None,
        'source': a.source
    } for a in results])
