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
import signal
import subprocess
import traceback
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


def _process_exists(pid: int) -> bool:
    """Return True if a process with given PID appears to be alive.

    Tries psutil if available for robustness; falls back to os.kill(pid, 0) probe.
    """
    if pid <= 0:
        return False
    try:
        import psutil  # type: ignore
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except Exception:
        # Fallback: os.kill(pid, 0) raises OSError if process does not exist
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True


def _attempt_terminate(pid: int, timeout: float = 3.0) -> bool:
    """Attempt graceful then forced termination of a process.

    Returns True if process gone at end.
    """
    if not _process_exists(pid):
        return True
    try:
        # Graceful
        os.kill(pid, signal.SIGTERM)
    except Exception:
        pass
    # Wait a bit
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _process_exists(pid):
            return True
        time.sleep(0.2)
    # Forceful (platform specific)
    if _process_exists(pid):
        if sys.platform.startswith('win'):
            try:
                subprocess.run(['taskkill', '/PID', str(pid), '/F', '/T'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass
    return not _process_exists(pid)


def acquire_single_instance_lock(app, *, force: bool = False, auto_terminate: bool = False):
    """Prevent multiple instances using a lock file & optional auto-termination.

    Behavior:
    1. If lock file absent: create it exclusive and write current PID.
    2. If present: read PID; if process dead treat as stale and replace.
    3. If present & alive:
       - if auto_terminate True attempt to terminate prior instance then claim lock.
       - if force True (and termination failed or not requested) steal lock anyway.

    Returns file descriptor if lock acquired, else None.
    """
    lock_path = os.path.join(app.instance_path, LOCK_FILE)
    os.makedirs(app.instance_path, exist_ok=True)

    def _write_lock():
        fd_local = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.write(fd_local, str(os.getpid()).encode('utf-8'))
        return fd_local

    # Fast path
    try:
        return _write_lock()
    except FileExistsError:
        pass
    except Exception:
        return None

    # Lock exists; inspect
    try:
        with open(lock_path, 'r', encoding='utf-8') as f:
            raw = f.read().strip()
        existing_pid = int(raw) if raw.isdigit() else -1
    except Exception:
        existing_pid = -1

    if existing_pid == -1 or not _process_exists(existing_pid):
        # Stale lock; remove and retry
        try:
            os.remove(lock_path)
        except Exception:
            pass
        try:
            return _write_lock()
        except Exception:
            return None

    # Process alive
    # If not terminating, try to bring existing instance to foreground by opening its URL
    if not auto_terminate and not force:
        try:
            import urllib.request
            # Probe the typical port range we use
            for probe_port in range(5000, 5006):
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{probe_port}/health', timeout=0.75) as resp:
                        if resp.status == 200:
                            print(f"Existing Activity Tracker detected at http://127.0.0.1:{probe_port}/ — opening browser...")
                            open_browser(f'http://127.0.0.1:{probe_port}/', delay=0.2)
                            break
                except Exception:
                    continue
        except Exception:
            pass
    if auto_terminate:
        if _attempt_terminate(existing_pid):
            # Removed process; attempt to acquire
            try:
                os.remove(lock_path)
            except Exception:
                pass
            try:
                return _write_lock()
            except Exception:
                return None
        else:
            # Failed termination
            return None

    if force:
        try:
            os.remove(lock_path)
        except Exception:
            return None
        try:
            return _write_lock()
        except Exception:
            return None

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

    # Environment-controlled behavior
    auto_terminate = os.getenv('ACTIVITY_TRACKER_AUTO_TERMINATE', '0') == '1'
    force_lock = os.getenv('ACTIVITY_TRACKER_FORCE_LOCK', '0') == '1'

    lock_fd = acquire_single_instance_lock(app, force=force_lock, auto_terminate=auto_terminate)
    if lock_fd is None:
        msg = "Another Activity Tracker instance is already running."
        if auto_terminate:
            msg = "Previous instance could not be terminated (permission denied or still shutting down)."
        elif force_lock:
            msg = "Could not force lock acquisition (file in use)."
        print(msg)
        print("Opening existing instance (if detected). If it doesn't appear, manually open http://127.0.0.1:5000/ in your browser.")
        print("Hints: ACTIVITY_TRACKER_AUTO_TERMINATE=1 will close the prior instance; ACTIVITY_TRACKER_FORCE_LOCK=1 will override a stale lock.")
        # Provide a short grace period so double-click users can read the message before the window closes.
        if os.getenv('ACTIVITY_TRACKER_NO_GRACE', '0') != '1':
            for remaining in range(5, 0, -1):
                print(f"Exiting in {remaining}…", end="\r", flush=True)
                time.sleep(1)
            print("Exiting now.        ")
        return

    # Ensure database exists and make a startup backup (throttling could be added later)
    try:
        with app.app_context():
            db.create_all()
            backup_database(app, db)
    except Exception as e:
        print(f"Startup database initialization failed: {e}")
        try:
            app.logger.error("Startup database initialization failed", exc_info=True)
        except Exception:
            pass
        traceback.print_exc()
        # Continue; app might still run for health/info routes

    port = find_available_port(5000, max_tries=6)
    url = f'http://127.0.0.1:{port}/'
    open_browser(url)

    print(f"Starting Activity Tracker on {url}")
    print("Press Ctrl+C to stop the server")
    # Proactive health probe
    def _post_start_probe():
        try:
            import urllib.request
            with urllib.request.urlopen(f'{url}health', timeout=5) as resp:
                if resp.status == 200:
                    print("Health check OK (HTTP 200)")
        except Exception as pe:
            print(f"Health check failed (non-fatal): {pe}")
    threading.Thread(target=_post_start_probe, daemon=True).start()
    if auto_terminate:
        print("Auto-terminate of prior instance was enabled.")
    elif force_lock:
        print("Force lock override enabled; previous instance (if any) not terminated.")

    from waitress import serve
    try:
        serve(app, host='127.0.0.1', port=port, threads=4)
    except Exception as e:
        print(f"Fatal server error: {e}")
        try:
            app.logger.error("Fatal server error", exc_info=True)
        except Exception:
            pass
        traceback.print_exc()
        # Pause briefly so a double-clicked console window doesn't vanish instantly on fatal errors.
        if os.getenv('ACTIVITY_TRACKER_NO_GRACE', '0') != '1':
            try:
                for remaining in range(6, 0, -1):
                    print(f"Closing in {remaining}…", end='\r', flush=True)
                    time.sleep(1)
                print("Closing now.       ")
            except Exception:
                pass
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
