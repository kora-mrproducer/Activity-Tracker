"""
Desktop entrypoint for Activity Tracker.

Starts the Flask app with Waitress production server and opens the default web browser.
Handles running from a PyInstaller bundle (one-folder/one-file).
"""
import os
import threading
import time
import webbrowser
import socket
import sys
from app import create_app, db
from app.utils import backup_database


def open_browser(url: str, delay: float = 1.5):
    """Open in app mode (chromeless window) to feel like a native desktop app.
    
    Falls back to regular browser if app mode not supported.
    """
    def _opener():
        time.sleep(delay)
        try:
            # Try Chrome/Edge app mode first (chromeless window)
            import subprocess
            import platform
            
            # Determine OS-specific browser paths
            if platform.system() == 'Windows':
                # Try Edge first (more common on Windows), then Chrome
                edge_paths = [
                    os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 
                                 'Microsoft\\Edge\\Application\\msedge.exe'),
                    os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 
                                 'Microsoft\\Edge\\Application\\msedge.exe'),
                ]
                chrome_paths = [
                    os.path.join(os.environ.get('LOCALAPPDATA', ''), 
                                 'Google\\Chrome\\Application\\chrome.exe'),
                    os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), 
                                 'Google\\Chrome\\Application\\chrome.exe'),
                    os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 
                                 'Google\\Chrome\\Application\\chrome.exe'),
                ]
                
                # Try Edge app mode
                for edge in edge_paths:
                    if os.path.exists(edge):
                        subprocess.Popen([
                            edge, 
                            '--app=' + url,
                            '--window-size=1280,800',
                            '--window-position=100,50'
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
                
                # Try Chrome app mode
                for chrome in chrome_paths:
                    if os.path.exists(chrome):
                        subprocess.Popen([
                            chrome, 
                            '--app=' + url,
                            '--window-size=1280,800',
                            '--window-position=100,50'
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
            
            elif platform.system() == 'Darwin':  # macOS
                # Try Chrome app mode on macOS
                chrome_mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
                if os.path.exists(chrome_mac):
                    subprocess.Popen([chrome_mac, '--app=' + url])
                    return
            
            # Fallback to default browser
            webbrowser.open(url, new=1)
            
        except Exception:
            # Final fallback
            try:
                webbrowser.open(url, new=1)
            except Exception:
                pass
    
    threading.Thread(target=_opener, daemon=True).start()


LOCK_FILE = 'activity_tracker.lock'


def acquire_single_instance_lock(app):
    """Prevent multiple instances by creating a lock file opened exclusively.

    Uses OS file semantics; on Windows, opening with 'x' will fail if exists.
    """
    lock_path = os.path.join(app.instance_path, LOCK_FILE)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(fd, str(os.getpid()).encode('utf-8'))
        return fd  # keep fd open to hold lock
    except FileExistsError:
        return None
    except Exception:
        # Non-fatal if locking fails; allow app to continue
        return None


def find_available_port(preferred=5000, max_tries=5):
    """Try sequential ports starting at preferred until one is free."""
    for i in range(max_tries):
        port = preferred + i
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return preferred  # fallback to preferred even if busy (will raise later)


def main():
    env = os.getenv('FLASK_ENV', 'production')
    app = create_app(env)

    # Attempt single-instance lock
    lock_fd = acquire_single_instance_lock(app)
    if lock_fd is None:
        print("Another instance appears to be running. Exiting.")
        return

    # Ensure database exists and make a startup backup (throttling could be added later)
    with app.app_context():
        db.create_all()
        backup_database(app, db)

    port = find_available_port(5000, max_tries=6)
    url = f'http://127.0.0.1:{port}/'
    open_browser(url)

    print(f"Starting Activity Tracker on {url}")
    print("Press Ctrl+C to stop the server")

    from waitress import serve
    try:
        serve(app, host='127.0.0.1', port=port, threads=4)
    finally:
        # Release lock by deleting file if we created it
        try:
            if lock_fd is not None:
                lock_path = os.path.join(app.instance_path, LOCK_FILE)
                os.close(lock_fd)
                os.remove(lock_path)
        except Exception:
            pass


if __name__ == '__main__':
    main()
