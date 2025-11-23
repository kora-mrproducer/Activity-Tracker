"""Simple entry point for the Activity Tracker application."""
import os
import socket
from app import create_app
from app.utils import backup_database


# Create application instance via factory
app = create_app(os.getenv('FLASK_ENV', 'production'))


def _find_port(preferred=5000, max_tries=4):
    for i in range(max_tries):
        port = preferred + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return preferred


if __name__ == '__main__':
    with app.app_context():
        from app import db
        db.create_all()
        backup_database(app, db)

    # Allow overriding host/port via environment (useful for Docker)
    host = os.getenv('HOST', '127.0.0.1')
    env_port = os.getenv('PORT', '').strip()
    if env_port.isdigit():
        port = int(env_port)
    else:
        port = _find_port(5000, max_tries=5)

    display_host = 'localhost' if host in ('0.0.0.0', '::') else host
    print(f"Starting Activity Tracker on http://{display_host}:{port}")
    print("Press Ctrl+C to stop the server")

    from waitress import serve
    serve(app, host=host, port=port, threads=4)
