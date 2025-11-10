# Test Database Models
import pytest
from datetime import datetime, timedelta
from app.models import Activity, Goal, Update

class TestActivityModel:
    """Test Activity model"""
    
    def test_create_activity(self, db_session):
        """Test creating an activity"""
        activity = Activity(
            activity_desc='New Test Activity',
            source='Unit Test',
            start_date=datetime.now().date(),
            status='Ongoing',
            priority='High'
        )
        db_session.add(activity)
        db_session.commit()
        
        assert activity.id is not None
        assert activity.activity_desc == 'New Test Activity'
        assert activity.source == 'Unit Test'
        assert activity.status == 'Ongoing'
        assert activity.priority == 'High'
    
    def test_activity_repr(self, sample_activity):
        """Test activity string representation"""
        repr_str = repr(sample_activity)
        assert 'Test Activity' in repr_str
    
    def test_activity_to_dict(self, sample_activity):
        """Test activity to_dict method"""
        activity_dict = sample_activity.to_dict()
        
        assert isinstance(activity_dict, dict)
        assert activity_dict['activity_desc'] == 'Test Activity'
        assert activity_dict['source'] == 'Test'
        assert activity_dict['status'] == 'Ongoing'
        assert activity_dict['priority'] == 'High'
        assert 'id' in activity_dict
        assert 'created_at' in activity_dict
    
    def test_activity_with_end_date(self, sample_closed_activity):
        """Test activity with end date"""
        assert sample_closed_activity.end_date is not None
        assert sample_closed_activity.status == 'Closed'
    
    def test_activity_tags(self, db_session):
        """Test activity with tags"""
        activity = Activity(
            activity_desc='Tagged Activity',
            source='Test',
            start_date=datetime.now().date(),
            status='Ongoing',
            priority='Low',
            tags='python, flask, testing'
        )
        db_session.add(activity)
        db_session.commit()
        
        assert 'python' in activity.tags
        assert 'flask' in activity.tags
        assert 'testing' in activity.tags
    
    def test_activity_blocking_points(self, db_session):
        """Test activity with blocking points"""
        activity = Activity(
            activity_desc='Blocked Activity',
            source='Test',
            start_date=datetime.now().date(),
            status='Ongoing',
            priority='High',
            blocking_points='Waiting for approval'
        )
        db_session.add(activity)
        db_session.commit()
        
        assert activity.blocking_points == 'Waiting for approval'

class TestGoalModel:
    """Test Goal model"""
    
    def test_create_goal(self, db_session):
        """Test creating a goal"""
        goal = Goal(
            text='Complete unit tests',
            week_of=datetime.now().date(),
            is_complete=False
        )
        db_session.add(goal)
        db_session.commit()
        
        assert goal.id is not None
        assert goal.goal_text == 'Complete unit tests'
        assert goal.is_complete is False
    
    def test_goal_repr(self, sample_goal):
        """Test goal string representation"""
        repr_str = repr(sample_goal)
        assert 'Test Weekly Goal' in repr_str
    
    def test_complete_goal(self, sample_goal, db_session):
        """Test completing a goal"""
        sample_goal.is_complete = True
        db_session.commit()
        
        assert sample_goal.is_complete is True
    
    def test_goal_to_dict(self, sample_goal):
        """Test goal to_dict method"""
        goal_dict = sample_goal.to_dict()
        
        assert isinstance(goal_dict, dict)
        assert goal_dict['text'] == 'Test Weekly Goal'
        assert goal_dict['is_complete'] is False
        assert 'id' in goal_dict

class TestUpdateModel:
    """Test Update model"""
    
    def test_create_update(self, db_session, sample_activity):
        """Test creating an update"""
        update = Update(
            activity_id=sample_activity.id,
            text='Progress update',
            bp_snapshot='Still waiting'
        )
        db_session.add(update)
        db_session.commit()
        
        assert update.id is not None
        assert update.activity_id == sample_activity.id
        assert update.text == 'Progress update'
        assert update.bp_snapshot == 'Still waiting'
    
    def test_update_repr(self, sample_update):
        """Test update string representation"""
        repr_str = repr(sample_update)
        assert 'Test update' in repr_str
    
    def test_update_timestamp(self, sample_update):
        """Test update has created_at timestamp"""
        assert sample_update.created_at is not None
        assert isinstance(sample_update.created_at, datetime)
    
    def test_update_relationship(self, db_session, sample_activity):
        """Test update relationship with activity"""
        update1 = Update(
            activity_id=sample_activity.id,
            text='First update'
        )
        update2 = Update(
            activity_id=sample_activity.id,
            text='Second update'
        )
        db_session.add_all([update1, update2])
        db_session.commit()
        
        # Refresh to load relationship
        db_session.refresh(sample_activity)
        assert len(sample_activity.updates) >= 2
    
    def test_update_to_dict(self, sample_update):
        """Test update to_dict method"""
        update_dict = sample_update.to_dict()
        
        assert isinstance(update_dict, dict)
        assert update_dict['text'] == 'Test update'
        assert 'id' in update_dict
        assert 'activity_id' in update_dict
        assert 'created_at' in update_dict

class TestModelRelationships:
    """Test model relationships and cascades"""
    
    def test_activity_delete_cascades_updates(self, db_session, sample_activity):
        """Test that deleting activity deletes its updates"""
        # Create updates
        update1 = Update(activity_id=sample_activity.id, text='Update 1')
        update2 = Update(activity_id=sample_activity.id, text='Update 2')
        db_session.add_all([update1, update2])
        db_session.commit()
        
        activity_id = sample_activity.id
        
        # Delete activity
        db_session.delete(sample_activity)
        db_session.commit()
        
        # Check updates are also deleted
        remaining_updates = db_session.query(Update).filter_by(activity_id=activity_id).all()
        assert len(remaining_updates) == 0
