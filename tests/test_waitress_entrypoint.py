"""Tests ensuring production waitress configuration is used in run.py entrypoint.

We don't actually start the waitress server (would block). Instead we execute
run.py as if it were the main script using runpy.run_module, while patching
waitress.serve to capture call arguments.
"""
import runpy
import types
from unittest import mock


def test_run_uses_waitress_production(monkeypatch):
    """Verify that running run.py invokes waitress.serve with expected host/port/threads.

    We simulate __main__ execution by reloading the module after setting __name__.
    """
    import sys

    # Ensure environment variable sets production (default already, but explicit is fine)
    monkeypatch.setenv('FLASK_ENV', 'production')

    # Remove previously imported module if any
    if 'run' in sys.modules:
        del sys.modules['run']

    captured = {}

    def fake_serve(app, host, port, threads):  # signature must match usage
        captured['host'] = host
        captured['port'] = port
        captured['threads'] = threads
        # basic sanity about app object
        captured['has_logger'] = hasattr(app, 'logger')
        captured['config_name'] = app.config.get('TESTING') is False and app.config.get('DEBUG') is False

    # Patch waitress.serve before executing run.py
    monkeypatch.setitem(sys.modules, 'waitress', types.ModuleType('waitress'))
    sys.modules['waitress'].serve = fake_serve

    # Execute run.py as if it were run with `python run.py`
    with mock.patch.object(sys, 'argv', ['run.py']):
        runpy.run_module('run', run_name='__main__')

    # Assertions about captured waitress invocation
    assert captured.get('host') == '127.0.0.1'
    assert captured.get('port') == 5000
    assert captured.get('threads') == 4
    assert captured.get('has_logger') is True
    # config_name True means production flags (DEBUG False, TESTING False)
    assert captured.get('config_name') is True
