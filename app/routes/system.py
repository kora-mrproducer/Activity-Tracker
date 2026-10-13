"""System/utility routes for health checks and assets like favicon."""
from flask import Blueprint, jsonify, current_app, Response, url_for, send_from_directory
import os

system_bp = Blueprint('system', __name__)


@system_bp.route('/health')
def health():
    """Simple health check endpoint with basic metadata."""
    info = {
        'status': 'ok',
        'ok': True,
        'env': current_app.config.get('ENV', 'production'),
        'debug': bool(current_app.debug),
        'testing': bool(current_app.testing),
        'version': current_app.config.get('__version__', None) or getattr(current_app, '__version__', None)
    }
    return jsonify(info), 200


@system_bp.route('/favicon.ico')
def favicon():
    """Return empty 204 to avoid noisy 404s if no favicon is packaged."""
    # Alternatively, serve a packaged icon via send_from_directory if available.
    return Response(status=204)


@system_bp.route('/manifest.json')
def manifest():
    """Serve PWA manifest for standalone app mode."""
    return send_from_directory(
        current_app.static_folder,
        'manifest.json',
        mimetype='application/manifest+json'
    )


@system_bp.route('/sw.js')
def service_worker():
    response = send_from_directory(current_app.static_folder, 'sw.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache'
    return response
