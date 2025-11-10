"""Lightweight smoke test for Activity Tracker using Flask test client.

Runs a handful of GET requests against core endpoints and reports HTTP status codes.
This avoids relying on network binding and works in CI or local environments.
"""
from app import create_app, db


def run_smoke():
    app = create_app('testing')
    results = {}
    with app.app_context():
        db.create_all()
        client = app.test_client()
        endpoints = ['/', '/analytics', '/timeline', '/add', '/completed']
        for ep in endpoints:
            resp = client.get(ep)
            results[ep] = resp.status_code
    return results


if __name__ == '__main__':
    results = run_smoke()
    for ep, code in results.items():
        print(f"{ep}: {code}")
    # Non-zero exit if any non-200 for core pages (except redirects) 
    # Here we expect 200 for all listed endpoints
    import sys
    if any(code != 200 for code in results.values()):
        sys.exit(1)
