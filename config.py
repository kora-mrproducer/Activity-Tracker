"""
Configuration settings for the Activity Tracker application.
"""
import os
import secrets

# Application version
__version__ = '1.0.0'


class Config:
    """Base configuration class"""
    
    # Get the base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Secret key management
    SECRET_KEY_FILE = os.path.join(BASE_DIR, '.secret_key')
    
    # Generate or load secret key
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'r') as f:
            SECRET_KEY = f.read().strip()
    else:
        # Generate new secret key
        SECRET_KEY = secrets.token_hex(32)
        with open(SECRET_KEY_FILE, 'w') as f:
            f.write(SECRET_KEY)
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tracker.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging configuration
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'activity_tracker.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 5_000_000))  # 5 MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # Backup configuration
    BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
    BACKUP_KEEP_COUNT = 7


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = False  # Set to True for detailed errors
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # In-memory database for tests
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
