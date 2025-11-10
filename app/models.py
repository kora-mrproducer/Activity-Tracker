"""
Database models for the Activity Tracker application.
"""
from datetime import datetime, timezone
from app import db
from sqlalchemy.orm import validates


class Activity(db.Model):
    """Model for tracking activities/tasks"""
    __tablename__ = 'activities'
    __table_args__ = (
        db.Index('idx_status', 'status'),
        db.Index('idx_priority', 'priority'),
        db.Index('idx_start_date', 'start_date'),
        db.Index('idx_end_date', 'end_date'),  # Added for analytics performance
    )
    
    id = db.Column(db.Integer, primary_key=True)
    activity_desc = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100))  # e.g., "BUM", "BUT/DCRA"
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    blocking_points = db.Column(db.Text, nullable=True)
    # Restrict status to known set; add DB-level CHECK via migration
    status = db.Column(db.String(50), default='Ongoing')  # Allowed: Ongoing, Closed, NA
    observations = db.Column(db.Text, nullable=True)
    # Restrict priority to known set; add DB-level CHECK via migration
    priority = db.Column(db.String(20), default='Medium')  # Allowed: High, Medium, Low
    tags = db.Column(db.Text, nullable=True)  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
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
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    # SQLAlchemy-level validation on assignment
    @validates('status')
    def _validate_status(self, key, value):
        return Activity.validate_status(value)

    @validates('priority')
    def _validate_priority(self, key, value):
        return Activity.validate_priority(value)

    @staticmethod
    def validate_status(value: str):
        allowed = {"Ongoing", "Closed", "NA"}
        if value not in allowed:
            raise ValueError(f"Invalid status '{value}'. Allowed: {', '.join(sorted(allowed))}")
        return value

    @staticmethod
    def validate_priority(value: str):
        allowed = {"High", "Medium", "Low"}
        if value not in allowed:
            raise ValueError(f"Invalid priority '{value}'. Allowed: {', '.join(sorted(allowed))}")
        return value


class Goal(db.Model):
    """Model for tracking weekly goals"""
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    week_of = db.Column(db.Date, nullable=False)
    is_complete = db.Column(db.Boolean, default=False)
    
    @property
    def goal_text(self):
        """Backward compatibility alias for text"""
        return self.text
    
    @goal_text.setter
    def goal_text(self, value):
        self.text = value
    
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
    # Snapshot of blocking points at time of update
    bp_snapshot = db.Column(db.Text, nullable=True)

    activity = db.relationship('Activity', backref=db.backref('updates', lazy='select', cascade='all, delete-orphan'))

    def __repr__(self):
        text_preview = self.text[:30] if self.text else ''
        return f'<Update {self.id} for Activity {self.activity_id}: {text_preview}>'

    def to_dict(self):
        return {
            'id': self.id,
            'activity_id': self.activity_id,
            'text': self.text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'bp_snapshot': self.bp_snapshot
        }
