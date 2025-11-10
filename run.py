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

    port = _find_port(5000, max_tries=5)
    print(f"Starting Activity Tracker on http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the server")

    from waitress import serve
    serve(app, host='127.0.0.1', port=port, threads=4)
