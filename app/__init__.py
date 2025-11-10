"""
Application factory for the Activity Tracker.
"""
from flask import Flask, g, request as flask_request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import logging
import time
import uuid
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name='default'):
    """
    Application factory pattern.
    
    Args:
        config_name: Configuration to use ('development', 'production', 'testing')
    
    Returns:
        Flask application instance
    """
    # Determine base directory depending on frozen (PyInstaller) vs dev
    if getattr(sys, 'frozen', False):
        # Running in bundled executable
        # _MEIPASS is present for onefile; for onefolder, use executable's parent
        if hasattr(sys, '_MEIPASS'):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(sys.executable).resolve().parent
    else:
        # Running from source
        base_dir = Path(__file__).resolve().parent.parent

    template_dir = (base_dir / 'templates').resolve()
    static_dir = (base_dir / 'static').resolve()

    # Ensure instance folder lives alongside executable when frozen
    instance_path = (base_dir / 'instance').resolve()

    app = Flask(
        __name__,
        instance_path=str(instance_path),
        instance_relative_config=True,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])

    # Ensure SQLite DB path is inside instance folder for portability
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    # Don't rewrite in-memory DB used by tests
    if uri.startswith('sqlite:///:memory:'):
        pass
    elif uri.startswith('sqlite:///'):
        # Extract path part
        db_path = uri.replace('sqlite:///', '', 1)
        # If not absolute, place it in instance folder
        if not os.path.isabs(db_path):
            abs_db_path = os.path.join(app.instance_path, db_path)
            # Make sure instance dir exists before assigning
            try:
                os.makedirs(app.instance_path, exist_ok=True)
            except OSError:
                pass
            app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{abs_db_path}"

    # When frozen, override paths to ensure writability next to the executable
    if getattr(sys, 'frozen', False):
        logs_dir = str((base_dir / 'logs').resolve())
        backups_dir = str((base_dir / 'backups').resolve())
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(backups_dir, exist_ok=True)
        try:
            os.makedirs(instance_path, exist_ok=True)
        except OSError:
            pass
        app.config['LOG_DIR'] = logs_dir
        app.config['LOG_FILE'] = os.path.join(logs_dir, 'activity_tracker.log')
        app.config['BACKUP_DIR'] = backups_dir

    # Ensure SECRET_KEY is stored/loaded from instance folder (writable in frozen env)
    secret_path = os.path.join(app.instance_path, '.secret_key')
    try:
        if os.path.exists(secret_path):
            with open(secret_path, 'r', encoding='utf-8') as f:
                app.config['SECRET_KEY'] = f.read().strip()
        else:
            import secrets as _secrets
            sk = _secrets.token_hex(32)
            with open(secret_path, 'w', encoding='utf-8') as f:
                f.write(sk)
            app.config['SECRET_KEY'] = sk
    except Exception:
        # Fallback to existing SECRET_KEY from config if any
        pass
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register Jinja filters
    register_filters(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register request hooks for access logging
    register_request_hooks(app)

    # Register CLI commands
    register_cli(app)
    
    # Note: Database migrations are now handled by Flask-Migrate
    # Run: flask db upgrade
    
    app.logger.info('Activity Tracker startup')
    
    return app


def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        log_dir = app.config.get('LOG_DIR', 'logs')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        
        file_handler = RotatingFileHandler(
            app.config.get('LOG_FILE', 'logs/activity_tracker.log'),
            maxBytes=app.config.get('LOG_MAX_BYTES', 5_000_000),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5),
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    
    # Add console handler for development/testing
    if app.debug or app.testing:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.DEBUG)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)


def register_filters(app):
    """Register Jinja template filters"""
    from app.utils import timeago_filter
    app.template_filter('timeago')(timeago_filter)
    # Inject a simple now() helper into templates
    from datetime import datetime, timezone
    def _now():
        # Use UTC to avoid timezone issues in PDFs/exports
        return datetime.now(timezone.utc)
    app.jinja_env.globals['now'] = _now


def register_blueprints(app):
    """Register application blueprints"""
    from app.routes.activities import activities_bp
    from app.routes.analytics import analytics_bp
    from app.routes.goals import goals_bp
    from app.routes.exports import exports_bp
    from app.routes.system import system_bp
    from app.routes.search import search_bp
    
    app.register_blueprint(activities_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(search_bp)


def register_error_handlers(app):
    """Register error handlers"""
    from flask import redirect, url_for, flash, request
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        request_id = getattr(g, 'request_id', 'unknown')
        app.logger.warning(
            f'[{request_id}] 404 Error: {error} - '
            f'{flask_request.method} {flask_request.path} from {flask_request.remote_addr}'
        )
        # Return 404 status for API/test requests; redirect for browser
        # Check if this is a test environment or if the user agent suggests automated client
        is_test = app.config.get('TESTING', False)
        is_api = request and request.path.startswith('/api/')
        accepts_json = request and request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
        
        if is_test or is_api or accepts_json:
            return {'error': 'Not found'}, 404
        flash('Page not found.', 'error')
        return redirect(url_for('activities.dashboard')), 302
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        request_id = getattr(g, 'request_id', 'unknown')
        error_id = uuid.uuid4().hex[:8]
        
        # Enhanced error logging with context
        app.logger.error(
            f'[{request_id}] 500 Error (error_id={error_id}): {error} - '
            f'{flask_request.method} {flask_request.path} from {flask_request.remote_addr}',
            exc_info=True
        )
        
        db.session.rollback()
        # Check if this is a test environment or if the user agent suggests automated client
        is_test = app.config.get('TESTING', False)
        is_api = request and request.path.startswith('/api/')
        accepts_json = request and request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
        
        if is_test or is_api or accepts_json:
            return {'error': 'Internal server error', 'error_id': error_id, 'request_id': request_id}, 500
        
        # Render custom 500 error page
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors with custom page"""
        from flask import render_template as rt
        is_api = request and request.path.startswith('/api/')
        accepts_json = request and request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html
        
        if is_api or accepts_json:
            return {'error': 'Not found'}, 404
        
        # Render custom 404 error page
        return rt('errors/404.html'), 404


def register_request_hooks(app):
    """Register before/after request hooks for access logging"""
    
    @app.before_request
    def start_request():
        """Generate request ID and capture start time"""
        g.request_id = uuid.uuid4().hex[:8]
        g.start_time = time.perf_counter()
    
    @app.after_request
    def log_request(response):
        """Log access details after each request"""
        if hasattr(g, 'start_time'):
            duration_ms = int((time.perf_counter() - g.start_time) * 1000)
        else:
            duration_ms = 0
        
        request_id = getattr(g, 'request_id', 'unknown')
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id
        
        # Log access line
        app.logger.info(
            f'[{request_id}] {flask_request.method} {flask_request.path} '
            f'{response.status_code} {duration_ms}ms - {flask_request.remote_addr}'
        )
        
        return response


def register_cli(app):
    """Register Flask CLI commands"""
    import click
    from app.utils import backup_database

    @app.cli.command("init-db")
    def init_db_command():
        """Initialize database tables (use 'flask db upgrade' for migrations)."""
        with app.app_context():
            db.create_all()
            click.echo("✓ Database initialized (create_all). For schema migrations, run: flask db upgrade")

    @app.cli.command("backup-now")
    def backup_now_command():
        """Create a backup of the current database file."""
        with app.app_context():
            backup_database(app, db)

    @app.cli.command("export-all")
    @click.option("--out", "out_path", default=None, help="Output ZIP path (defaults to ./activity_tracker_export_*.zip)")
    def export_all_command(out_path):
        """Export a full data bundle (DB + CSV/JSON) to a ZIP file."""
        import io
        import zipfile
        import os
        from datetime import datetime, timezone
        # Reuse the HTTP route logic via test_client to avoid duplication
        with app.app_context():
            client = app.test_client()
            resp = client.get('/export/all')
            if resp.status_code != 200:
                click.echo(f"Export failed with status {resp.status_code}")
                raise SystemExit(1)
            data = resp.data
            if not out_path:
                ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                out_path = os.path.join(os.getcwd(), f'activity_tracker_export_{ts}.zip')
            with open(out_path, 'wb') as f:
                f.write(data)
            # Quick validation: ensure manifest exists
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as zf:
                    assert 'manifest.json' in zf.namelist()
            except Exception:
                click.echo('Warning: Export ZIP saved, but validation failed to find manifest.json')
            click.echo(f"✓ Export written to: {out_path}")
