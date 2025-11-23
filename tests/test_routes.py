# Test Activity Routes
import pytest
import json
from datetime import datetime

class TestDashboardRoute:
    """Test dashboard route"""
    
    def test_dashboard_loads(self, client):
        """Test dashboard page loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Activity Tracker' in response.data or b'Dashboard' in response.data
    
    def test_dashboard_with_activities(self, client, sample_activity):
        """Test dashboard displays activities"""
        response = client.get('/')
        assert response.status_code == 200
        assert sample_activity.activity_desc.encode() in response.data
    
    def test_dashboard_filters_by_status(self, client, sample_activity):
        """Test dashboard status filter"""
        response = client.get('/?status=Ongoing')
        assert response.status_code == 200
    
    def test_dashboard_filters_by_priority(self, client, sample_activity):
        """Test dashboard priority filter"""
        response = client.get('/?priority=High')
        assert response.status_code == 200
    
    def test_dashboard_search(self, client, sample_activity):
        """Test dashboard search functionality"""
        response = client.get('/?search=Test')
        assert response.status_code == 200

class TestAddActivityRoute:
    """Test add activity routes"""
    
    def test_add_activity_get(self, client):
        """Test GET add activity page"""
        response = client.get('/add')
        assert response.status_code == 200
    
    def test_add_activity_post(self, client, db_session):
        """Test POST new activity"""
        data = {
            'activity_desc': 'New Activity from Test',
            'source': 'Unit Test',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Ongoing',
            'priority': 'Medium',
            'tags': 'test',
            'blocking_points': 'None'
        }
        response = client.post('/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify activity was created
        from app.models import Activity
        activity = db_session.query(Activity).filter_by(
            activity_desc='New Activity from Test'
        ).first()
        assert activity is not None
        assert activity.source == 'Unit Test'
        assert activity.priority == 'Medium'
    
    def test_add_activity_with_initial_update(self, client, db_session):
        """Test adding activity with initial update"""
        data = {
            'activity_desc': 'Activity with Update',
            'source': 'Test',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Ongoing',
            'priority': 'High',
            'initial_update': 'Initial note'
        }
        response = client.post('/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        from app.models import Activity, Update
        activity = db_session.query(Activity).filter_by(
            activity_desc='Activity with Update'
        ).first()
        assert activity is not None
        
        # Check update was created
        update = db_session.query(Update).filter_by(activity_id=activity.id).first()
        assert update is not None
        assert update.text == 'Initial note'
    
    def test_add_activity_clone(self, client, sample_activity):
        """Test cloning an existing activity"""
        response = client.get(f'/add?clone={sample_activity.id}')
        assert response.status_code == 200
        assert sample_activity.activity_desc.encode() in response.data

class TestEditActivityRoute:
    """Test edit activity routes"""
    
    def test_edit_activity_get(self, client, sample_activity):
        """Test GET edit activity page"""
        response = client.get(f'/edit/{sample_activity.id}')
        assert response.status_code == 200
        assert sample_activity.activity_desc.encode() in response.data
    
    def test_edit_activity_post(self, client, sample_activity, db_session):
        """Test POST edit activity"""
        data = {
            'activity_desc': 'Updated Activity Description',
            'source': sample_activity.source,
            'start_date': sample_activity.start_date.strftime('%Y-%m-%d'),
            'status': sample_activity.status,
            'priority': 'Low',  # Changed from High
            'tags': sample_activity.tags,
            'blocking_points': 'Updated blocking points'
        }
        response = client.post(
            f'/edit/{sample_activity.id}',
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Verify changes
        db_session.refresh(sample_activity)
        assert sample_activity.activity_desc == 'Updated Activity Description'
        assert sample_activity.priority == 'Low'
        assert sample_activity.blocking_points == 'Updated blocking points'
    
    def test_edit_activity_with_update(self, client, sample_activity, db_session):
        """Test editing activity and adding update"""
        data = {
            'activity_desc': sample_activity.activity_desc,
            'source': sample_activity.source,
            'start_date': sample_activity.start_date.strftime('%Y-%m-%d'),
            'status': sample_activity.status,
            'priority': sample_activity.priority,
            'new_update': 'Added during edit'
        }
        response = client.post(
            f'/edit/{sample_activity.id}',
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        
        from app.models import Update
        update = db_session.query(Update).filter_by(
            activity_id=sample_activity.id
        ).first()
        assert update is not None
        assert update.text == 'Added during edit'
    
    def test_edit_nonexistent_activity(self, client):
        """Test editing non-existent activity returns 404"""
        response = client.get('/edit/99999')
        assert response.status_code == 404

class TestDeleteActivityRoute:
    """Test delete activity route"""
    
    def test_delete_activity(self, client, sample_activity, db_session):
        """Test deleting an activity"""
        activity_id = sample_activity.id
        response = client.get(f'/delete/{activity_id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify activity was deleted
        from app.models import Activity
        activity = db_session.query(Activity).filter_by(id=activity_id).first()
        assert activity is None
    
    def test_delete_nonexistent_activity(self, client):
        """Test deleting non-existent activity"""
        response = client.get('/delete/99999')
        assert response.status_code == 404

class TestCompletedRoute:
    """Test completed activities route"""
    
    def test_completed_page(self, client, sample_closed_activity):
        """Test completed activities page"""
        response = client.get('/completed')
        assert response.status_code == 200
        assert sample_closed_activity.activity_desc.encode() in response.data
    
    def test_completed_excludes_ongoing(self, client, sample_activity):
        """Test completed page doesn't show ongoing activities"""
        response = client.get('/completed')
        assert response.status_code == 200
        # Ongoing activity should not appear
        assert sample_activity.activity_desc.encode() not in response.data or b'Closed' in response.data

class TestUpdateStatusRoute:
    """Test update status route"""
    
    def test_update_status_to_closed(self, client, sample_activity, db_session):
        """Test changing activity status to Closed"""
        data = {
            'status': 'Closed',
            'closing_note': 'Task completed successfully'
        }
        response = client.post(
            f'/activity/{sample_activity.id}/status',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['ok'] is True
        
        # Verify status changed
        db_session.refresh(sample_activity)
        assert sample_activity.status == 'Closed'
        assert sample_activity.end_date is not None
        
        # Verify closing note was added as update
        from app.models import Update
        update = db_session.query(Update).filter_by(
            activity_id=sample_activity.id
        ).first()
        assert update is not None
        assert 'Task completed successfully' in update.text
    
    def test_update_status_without_closing_note(self, client, sample_activity):
        """Test changing to Closed without closing note fails"""
        data = {'status': 'Closed'}
        response = client.post(
            f'/activity/{sample_activity.id}/status',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_update_status_to_ongoing(self, client, sample_closed_activity, db_session):
        """Test changing status to Ongoing"""
        data = {'status': 'Ongoing'}
        response = client.post(
            f'/activity/{sample_closed_activity.id}/status',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        db_session.refresh(sample_closed_activity)
        assert sample_closed_activity.status == 'Ongoing'

class TestAddUpdateRoute:
    """Test add update route"""
    
    def test_add_update(self, client, sample_activity, db_session):
        """Test adding update to activity"""
        data = {
            'update_text': 'New progress update',
            'blocking_points': 'Still blocked'
        }
        response = client.post(
            f'/activity/{sample_activity.id}/update',
            data=data,
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Verify update was added
        from app.models import Update
        update = db_session.query(Update).filter_by(
            activity_id=sample_activity.id,
            text='New progress update'
        ).first()
        assert update is not None
        assert update.bp_snapshot == 'Still blocked'
    
    def test_add_empty_update_fails(self, client, sample_activity):
        """Test adding empty update fails"""
        data = {'update_text': ''}
        response = client.post(
            f'/activity/{sample_activity.id}/update',
            data=data,
            follow_redirects=True
        )
        # Should redirect back with flash message
        assert response.status_code == 200

class TestBulkUpdatePriority:
    """Test bulk update priority route"""
    
    def test_bulk_update_priority(self, client, db_session, sample_activity):
        """Test bulk updating activity priorities"""
        # Create additional activities
        from app.models import Activity
        activity2 = Activity(
            activity_desc='Activity 2',
            source='Test',
            start_date=datetime.now().date(),
            status='Ongoing',
            priority='Low'
        )
        db_session.add(activity2)
        db_session.commit()
        
        data = {
            'activity_ids': [sample_activity.id, activity2.id],
            'priority': 'High'
        }
        response = client.post(
            '/activities/bulk/priority',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['ok'] is True
        assert response_data['updated_count'] == 2
        
        # Verify priorities changed
        db_session.refresh(sample_activity)
        db_session.refresh(activity2)
        assert sample_activity.priority == 'High'
        assert activity2.priority == 'High'
    
    def test_bulk_update_invalid_priority(self, client, sample_activity):
        """Test bulk update with invalid priority"""
        data = {
            'activity_ids': [sample_activity.id],
            'priority': 'Invalid'
        }
        response = client.post(
            '/activities/bulk/priority',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400

class TestReportRoute:
    """Test report route"""
    
    def test_report_get(self, client):
        """Test GET report page"""
        response = client.get('/report')
        assert response.status_code == 200
    
    def test_report_post(self, client, sample_closed_activity):
        """Test POST report with date range"""
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')
        
        data = {
            'start_date': start,
            'end_date': end
        }
        response = client.post('/report', data=data)
        assert response.status_code == 200

    def test_report_pdf(self, client, sample_closed_activity):
        """Test PDF generation route for report (xhtml2pdf implementation)."""
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')
        data = {
            'start_date': start,
            'end_date': end
        }
        response = client.post('/report/pdf', data=data)
        assert response.status_code == 200
        assert response.headers.get('Content-Type', '').startswith('application/pdf')
