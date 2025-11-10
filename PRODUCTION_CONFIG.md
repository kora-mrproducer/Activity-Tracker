# Production Server and Desktop Packaging

## Summary
The Activity Tracker application has been reconfigured to use **Waitress**, a production-ready WSGI server, instead of Flask's development server.

## Changes Made

### 1. Added Waitress to Dependencies
- **File**: `requirements.txt`
- **Change**: Added `waitress==3.0.0`

### 2. Updated Main Entry Point
- **File**: `run.py`
- **Changes**:
  - Replaced `app.run()` with `waitress.serve()`
  - Changed default environment from `development` to `production`
  - Added informational console output

### 3. Updated Legacy Entry Point
- **File**: `app.py`
- **Changes**:
  - Added warning message when running directly
  - Kept `if __name__ == '__main__'` block for backward compatibility but discouraged its use
  - Changed `debug=False` to `debug=True` to make it obvious when development server is running

## Current Server Configuration

### Production Entry Points (Recommended)
Both of these use Waitress WSGI server:

1. **run.py** (Primary entry point)
   ```bash
   python run.py
   ```
   - Uses Waitress production server
   - 4 worker threads
   - Binds to 127.0.0.1:5000

2. **desktop_app.py** (Desktop application)
   ```bash
   python desktop_app.py
   ```
   - Uses Waitress production server
   - Automatically opens browser
   - Same configuration as run.py

### Development Entry Point (Not Recommended)
- **app.py** direct execution
  - Only for testing/debugging
  - Shows warning message
  - Uses Flask development server

## Waitress Benefits

- **Production-ready**: Designed for production use, not development
- **Thread-safe**: Handles concurrent requests efficiently
- **No debugging overhead**: No auto-reloader or debugger
- **Better performance**: More stable under load
- **Windows-friendly**: Works reliably on Windows (unlike some other WSGI servers)

## How to Install Waitress

If you need to reinstall dependencies:

```powershell
# Using virtual environment
venv\Scripts\python.exe -m pip install -r requirements.txt

# Or install waitress directly
venv\Scripts\python.exe -m pip install waitress==3.0.0
```

## Starting the Application

### Using start_tracker.bat (Recommended)
```batch
start_tracker.bat
```
This batch file:
- Checks for virtual environment
- Launches `run.py` with Waitress
- Opens browser automatically

### Manual start
```powershell
venv\Scripts\python.exe run.py
```

## Configuration Settings

### Server Settings
- **Host**: 127.0.0.1 (localhost only)
- **Port**: 5000
- **Threads**: 4
- **Environment**: production (default)

### To change environment
Set the `FLASK_ENV` environment variable:
```powershell
$env:FLASK_ENV="development"
python run.py
```

## Desktop Packaging (Windows, PyInstaller)

The app is ready to be packaged as a standalone desktop application using PyInstaller. A spec file is provided and `desktop_app.py` is the entry point that opens your browser and serves via Waitress.

### Build prerequisites
- Python 3.11+ in a virtual environment
- Install dependencies:
  ```powershell
  venv\Scripts\python.exe -m pip install -r requirements.txt
  venv\Scripts\python.exe -m pip install pyinstaller
  ```

### Build
```powershell
venv\Scripts\python.exe -m PyInstaller ActivityTracker.spec
```
Outputs to `dist/ActivityTracker`.

### Prepare release folder (optional)
Use the provided script to stage a clean release folder with instance/logs/backups and docs:
```powershell
./build_release.ps1
```
This creates `release/ActivityTracker-v1.0.0/` with supporting files, version text, and quick start guide.

### Run the packaged app
Double-click `ActivityTracker.exe`. It will:
- Initialize the database in `instance/tracker.db`
- Open your browser to `http://127.0.0.1:5000/`
- Write logs under `logs/`
- Store backups in `backups/`

### Health and diagnostics
- `GET /health` returns JSON with environment flags and DB URI
- `/favicon.ico` returns 204 to suppress 404 noise (add a real icon later if desired)

## Notes

- App defaults to production mode (Waitress)
- SQLite database is stored under the writable `instance/` folder to support frozen apps
- Automatic database backups still occur on startup
- Logging writes to the local `logs/` directory; rotates per config
- In-memory SQLite (`sqlite:///:memory:`) is intentionally preserved in the **testing** configuration.
  The app factory only rewrites file-based relative SQLite URIs (those that start with `sqlite:///` and
  are not `:memory:`) to live under `instance/`. This keeps tests fast and avoids filesystem side effects.
  See `tests/test_sqlite_rewrite.py` for a regression test ensuring this behavior remains stable.
