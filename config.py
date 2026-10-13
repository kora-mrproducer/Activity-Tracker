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
    SECRET_KEY = secrets.token_hex(32)
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

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
