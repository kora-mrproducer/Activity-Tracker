# Pytest Configuration
import pytest
from app import create_app, db
from app.models import Activity, Goal, Update
from datetime import datetime, timedelta

@pytest.fixture(scope='session')
def app():
    """Create application instance for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        # Clean up any existing data
        db.session.query(Update).delete()
        db.session.query(Activity).delete()
        db.session.query(Goal).delete()
        db.session.commit()
        
        yield db.session
        
        # Cleanup after test
        db.session.rollback()
        db.session.query(Update).delete()
        db.session.query(Activity).delete()
        db.session.query(Goal).delete()
        db.session.commit()

@pytest.fixture
def sample_activity(db_session):
    """Create a sample activity for testing"""
    activity = Activity(
        activity_desc='Test Activity',
        source='Test',
        start_date=datetime.now().date(),
        status='Ongoing',
        priority='High',
        tags='test, sample',
        blocking_points='None'
    )
    db_session.add(activity)
    db_session.commit()
    return activity

@pytest.fixture
def sample_closed_activity(db_session):
    """Create a closed activity for testing"""
    activity = Activity(
        activity_desc='Closed Test Activity',
        source='Test',
        start_date=datetime.now().date() - timedelta(days=10),
        end_date=datetime.now().date(),
        status='Closed',
        priority='Medium',
        tags='test',
        blocking_points='None'
    )
    db_session.add(activity)
    db_session.commit()
    return activity

@pytest.fixture
def sample_goal(db_session):
    """Create a sample goal for testing"""
    from datetime import datetime
    goal = Goal(
        text='Test Weekly Goal',
        week_of=datetime.now().date(),
        is_complete=False
    )
    db_session.add(goal)
    db_session.commit()
    return goal

@pytest.fixture
def sample_update(db_session, sample_activity):
    """Create a sample update for testing"""
    update = Update(
        activity_id=sample_activity.id,
        text='Test update',
        bp_snapshot='None'
    )
    db_session.add(update)
    db_session.commit()
    return update
