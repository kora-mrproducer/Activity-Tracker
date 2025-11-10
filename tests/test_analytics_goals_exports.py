# Test Analytics, Goals, and Export Routes
import pytest
import json
from datetime import datetime, timedelta
from io import BytesIO

class TestAnalyticsRoute:
    """Test analytics route"""
    
    def test_analytics_page(self, client):
        """Test analytics page loads"""
        response = client.get('/analytics')
        assert response.status_code == 200
    
    def test_analytics_with_data(self, client, sample_activity, sample_closed_activity):
        """Test analytics with activities"""
        response = client.get('/analytics')
        assert response.status_code == 200
        # Should contain some statistics
        assert b'Priority Distribution' in response.data or b'Analytics' in response.data
    
    def test_analytics_empty_state(self, client):
        """Test analytics with no data"""
        response = client.get('/analytics')
        assert response.status_code == 200

class TestTimelineRoute:
    """Test timeline route"""
    
    def test_timeline_page(self, client):
        """Test timeline page loads"""
        response = client.get('/timeline')
        assert response.status_code == 200
    
    def test_timeline_with_activities(self, client, sample_activity):
        """Test timeline displays activities"""
        response = client.get('/timeline')
        assert response.status_code == 200
    
    def test_timeline_date_filter(self, client, sample_activity):
        """Test timeline with date filters"""
        from datetime import datetime, timedelta
        start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end = datetime.now().strftime('%Y-%m-%d')
        
        response = client.get(f'/timeline?start_date={start}&end_date={end}')
        assert response.status_code == 200

class TestGoalRoutes:
    """Test goal-related routes"""
    
    def test_add_goal(self, client, db_session):
        """Test adding a new goal"""
        data = {
            'goal_text': 'Test goal from unit test',
            'week_of': datetime.now().strftime('%Y-%m-%d')
        }
        response = client.post('/goal/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        
        # Verify goal was created
        from app.models import Goal
        goal = db_session.query(Goal).filter_by(
            text='Test goal from unit test'
        ).first()
        assert goal is not None
        assert goal.is_complete is False
    
    def test_add_empty_goal_fails(self, client):
        """Test adding empty goal fails"""
        data = {
            'goal_text': '',
            'week_of': datetime.now().strftime('%Y-%m-%d')
        }
        response = client.post('/goal/add', data=data, follow_redirects=True)
        assert response.status_code == 200
        # Should redirect back with error message
    
    def test_toggle_goal_completion(self, client, sample_goal, db_session):
        """Test toggling goal completion status"""
        initial_status = sample_goal.is_complete
        
        response = client.get(f'/goal/toggle/{sample_goal.id}', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify status toggled
        db_session.refresh(sample_goal)
        assert sample_goal.is_complete != initial_status
    
    def test_toggle_goal_twice(self, client, sample_goal, db_session):
        """Test toggling goal twice returns to original state"""
        initial_status = sample_goal.is_complete
        
        # Toggle once
        client.get(f'/goal/toggle/{sample_goal.id}', follow_redirects=True)
        db_session.refresh(sample_goal)
        assert sample_goal.is_complete != initial_status
        
        # Toggle again
        client.get(f'/goal/toggle/{sample_goal.id}', follow_redirects=True)
        db_session.refresh(sample_goal)
        assert sample_goal.is_complete == initial_status
    
    def test_toggle_nonexistent_goal(self, client):
        """Test toggling non-existent goal"""
        response = client.get('/goal/toggle/99999')
        assert response.status_code == 404

class TestExportRoutes:
    """Test export routes"""
    
    def test_export_csv(self, client, sample_activity):
        """Test CSV export"""
        response = client.get('/export/csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        # Check CSV content
        csv_data = response.data.decode('utf-8')
        assert 'Description' in csv_data or 'Activity ID' in csv_data
        assert sample_activity.activity_desc in csv_data
    
    def test_export_csv_empty(self, client):
        """Test CSV export with no activities"""
        response = client.get('/export/csv')
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        
        # Check CSV header
        csv_data = response.data.decode('utf-8')
        assert 'Description' in csv_data or 'Activity ID' in csv_data
    
    def test_export_csv_includes_all_fields(self, client, sample_activity, sample_update):
        """Test CSV export includes all relevant fields"""
        response = client.get('/export/csv')
        assert response.status_code == 200
        
        csv_data = response.data.decode('utf-8')
        # Check that key fields are present
        assert sample_activity.source in csv_data
        assert sample_activity.priority in csv_data
        assert sample_activity.status in csv_data

class TestErrorHandlers:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    def test_invalid_activity_id(self, client):
        """Test accessing activity with invalid ID"""
        response = client.get('/edit/invalid_id')
        assert response.status_code == 404

class TestIntegrationScenarios:
    """Test complete user workflows"""
    
    def test_complete_activity_workflow(self, client, db_session):
        """Test creating, updating, and closing an activity"""
        # Step 1: Create activity
        create_data = {
            'activity_desc': 'Integration Test Activity',
            'source': 'Integration Test',
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Ongoing',
            'priority': 'High',
            'initial_update': 'Starting work'
        }
        response = client.post('/add', data=create_data, follow_redirects=True)
        assert response.status_code == 200
        
        from app.models import Activity, Update
        activity = db_session.query(Activity).filter_by(
            activity_desc='Integration Test Activity'
        ).first()
        assert activity is not None
        
        # Step 2: Add progress update
        update_data = {
            'update_text': 'Made some progress',
            'blocking_points': 'None'
        }
        response = client.post(
            f'/activity/{activity.id}/update',
            data=update_data,
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Step 3: Edit activity
        edit_data = {
            'activity_desc': activity.activity_desc,
            'source': activity.source,
            'start_date': activity.start_date.strftime('%Y-%m-%d'),
            'status': activity.status,
            'priority': 'Medium',  # Change priority
            'tags': 'integration, test'
        }
        response = client.post(
            f'/edit/{activity.id}',
            data=edit_data,
            follow_redirects=True
        )
        assert response.status_code == 200
        
        # Step 4: Close activity
        close_data = {
            'status': 'Closed',
            'closing_note': 'Work completed successfully'
        }
        response = client.post(
            f'/activity/{activity.id}/status',
            data=json.dumps(close_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # Verify final state
        db_session.refresh(activity)
        assert activity.status == 'Closed'
        assert activity.end_date is not None
        assert activity.priority == 'Medium'
        
        # Verify updates exist
        updates = db_session.query(Update).filter_by(activity_id=activity.id).all()
        assert len(updates) >= 3  # Initial, progress, closing note
    
    def test_goal_lifecycle(self, client, db_session):
        """Test creating and completing a goal"""
        # Create goal
        create_data = {
            'goal_text': 'Complete integration tests',
            'week_of': datetime.now().strftime('%Y-%m-%d')
        }
        response = client.post('/goal/add', data=create_data, follow_redirects=True)
        assert response.status_code == 200
        
        from app.models import Goal
        goal = db_session.query(Goal).filter_by(
            text='Complete integration tests'
        ).first()
        assert goal is not None
        assert goal.is_complete is False
        
        # Complete goal
        response = client.get(f'/goal/toggle/{goal.id}', follow_redirects=True)
        assert response.status_code == 200
        
        db_session.refresh(goal)
        assert goal.is_complete is True
    
    def test_bulk_operations(self, client, db_session):
        """Test bulk operations on multiple activities"""
        from app.models import Activity
        
        # Create multiple activities
        activities = []
        for i in range(3):
            activity = Activity(
                activity_desc=f'Bulk Test Activity {i}',
                source='Bulk Test',
                start_date=datetime.now().date(),
                status='Ongoing',
                priority='Low'
            )
            activities.append(activity)
        
        db_session.add_all(activities)
        db_session.commit()
        
        # Bulk update priority
        activity_ids = [a.id for a in activities]
        data = {
            'activity_ids': activity_ids,
            'priority': 'High'
        }
        response = client.post(
            '/activities/bulk/priority',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['updated_count'] == 3
        
        # Verify all priorities updated
        for activity in activities:
            db_session.refresh(activity)
            assert activity.priority == 'High'
