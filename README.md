# Activity Tracker

A standalone, offline desktop application for tracking activities, tasks, and projects with analytics, timeline views, and comprehensive reporting.

## Features

- **Dashboard** - Quick stats, smart suggestions, focus mode, and bulk operations
- **Analytics** - Charts, completion velocity, priority distribution, and insights
- **Timeline** - Visual Gantt-style view of activity lifespans
- **Reports** - Custom date-range reports with export to CSV
- **Themes** - 5 built-in themes (Grayscale, Ocean, Forest, Sunset, Cyberpunk)
- **Offline** - Fully standalone, no internet connection required (all assets local)
- **Automatic Backups** - Startup backups with retention (default keep last 7)
- **Desktop Window** - Native window shell via pywebview (optional), no browser chrome

## Requirements

- Python 3.10 or higher (tested on 3.14)
- Windows 10/11 (tested); macOS/Linux should work
- Optional for a native desktop window (no browser): `pywebview`

## Installation

### Option 1: Automated Setup (Windows)

1. **Download** or clone this repository
2. **Double-click** `setup.bat` to create virtual environment and install dependencies
3. **Double-click** `start_tracker.bat` to launch the application

### Option 2: Manual Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**
   ```powershell
   venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

4. **Run the application:**
   ```powershell
   venv\Scripts\python.exe run.py
   ```
   The server uses a production WSGI (Waitress) and binds to 127.0.0.1. If port 5000 is busy, it will pick the next available.

## Usage

### Starting the Application

**Quick Start (Windows):**
```bash
start_tracker.bat
```

**Standard:**
```bash
python run.py
```

**Desktop Mode (standalone window):**
```powershell
venv\Scripts\python.exe desktop_app.py
```
This will open a native window using `pywebview` if installed; otherwise it will open your default browser. The backend starts automatically and uses a single-instance lock to prevent multiple copies.

### First-Time Setup

1. The database will be created automatically on first run
2. Start by clicking "Add Activity" in the sidebar
3. Fill in activity details (description, priority, dates, etc.)
4. Use the dashboard to manage ongoing activities

### Key Features

**Dashboard:**
- View all ongoing activities organized by priority
- Quick update modal (click update icon)
- Bulk operations (select multiple activities)
- Focus mode (shows only top 3 high-priority items)
- Smart suggestions for stale or long-running activities

**Analytics:**
- Completion velocity charts
- Priority and status distributions
- Average completion times by priority
- Tag cloud and long-running activity alerts

**Timeline:**
- Visual representation of activity lifespans
- Color-coded by priority
- Interactive bars (click to edit)
- Filterable by status, priority, and date range

**Keyboard Shortcuts:**
- `?` - Show help overlay
- `U` - Quick update (when row focused)
- `S` - Edit status (when row focused)
- `G` - Toggle goal completion
- `Esc` - Close modals

### Themes

Access the settings panel in the sidebar to:
- Choose from 5 color themes
- Adjust font size (A-, A, A+)
- Toggle density (comfortable/compact)
- Show/hide columns

### Data Export

Click "Export CSV" button on:
- Dashboard (exports all activities)
- Completed page (exports closed activities)

For printable reports, use the Report page:
- Generate a date‑range report, then click "Download PDF" to save a styled PDF of the results.

#### Full Data Export (ZIP)
You can download a single ZIP containing the raw database plus CSV and JSON copies:

- From the browser: visit `/export/all` (or use the Export button if linked)
- From the CLI:
   ```bash
   flask export-all --out my_export.zip
   ```

The bundle includes: `activity_tracker.db`, `activities.csv/json`, `goals.csv/json`, `updates.csv/json`, and `manifest.json` (with counts).

### Backups

Automatic backups are created:
- On application startup
- Stored in `/backups` folder
- Last 7 backups retained automatically
- Manual backup: copy `instance/tracker.db`

You can also trigger a backup via CLI:
```bash
flask backup-now
```

## Project Structure

```
Activity Tracker/
├── run.py                  # CLI entry point (Waitress, dynamic port)
├── desktop_app.py          # Desktop launcher (single-instance, pywebview window)
├── start_tracker.bat       # Windows quick-start script
├── setup.bat              # Automated environment setup
├── requirements.txt       # Python dependencies
├── instance/
│   └── tracker.db         # SQLite database
├── backups/              # Automatic database backups
├── static/
│   ├── js/
│   │   ├── chart.min.js   # Chart.js (local)
│   │   └── tailwind.js    # Tailwind CSS (local)
│   ├── fontawesome/
│   │   ├── css/          # Font Awesome CSS
│   │   └── webfonts/     # Font Awesome fonts
│   └── fonts/
│       ├── outfit-local.css
│       └── outfit-*.ttf   # Outfit font files
└── templates/
    ├── layout.html        # Base template
    ├── dashboard.html     # Main dashboard
    ├── analytics.html     # Analytics page
    ├── timeline.html      # Timeline view
    ├── completed.html     # Completed activities
    ├── report.html        # Custom reports
    ├── add_activity.html  # Add new activity
    └── edit_activity.html # Edit activity
```

## Database

- **Type:** SQLite (single-user, local)
- **Location:** `instance/tracker.db`
- **Tables:**
  - `activities` - Main activity records
  - `updates` - Update history with timestamps
  - `goals` - Weekly goals

## Troubleshooting

**Application won't start:**
- Ensure a modern Python is installed (3.10+ recommended)
- Verify virtual environment is activated
- Install dependencies: `venv\Scripts\python.exe -m pip install -r requirements.txt`

**Database errors:**
- Delete `instance/tracker.db` to reset (will lose data)
- Restore from backup: copy from `backups/` folder

**Port already in use:**
- No action needed: the app will try the next free port automatically (5000 → 5001 → ...)

**Styles not loading:**
- Verify `static/` folder contains all assets
- In desktop mode, styles are loaded locally without a network connection

**PDF export not working:**
- The app uses xhtml2pdf for PDF generation (Windows-friendly, no native libraries required).
- Ensure dependencies are installed: `pip install -r requirements.txt` (includes `xhtml2pdf`).
- If the PDF looks unstyled, verify `static/css/tailwind-built.css` exists. xhtml2pdf supports a subset of CSS; complex Tailwind utilities may be simplified.

## Development

**Run locally in development:**
```powershell
venv\Scripts\python.exe run.py
```
The code uses an application factory (`app.create_app`) and Waitress server. For tests, an in-memory SQLite DB is used.

**Database migrations:**
- Use Flask-Migrate via CLI (upgrade on startup is not automatic)
- To reset: delete `instance/tracker.db` (this will lose data) and restart

**Add new features:**
1. Create routes under `app/routes/`
2. Add templates in `templates/`
3. Update navigation in `templates/layout.html`

## Security Notes

- **Single-user application** - no authentication needed
- **Local only** - binds to 127.0.0.1 (not accessible over network)
- **Secret key** - automatically generated on first run
- **No internet** - all assets local, no external connections

## Credits

- **Tailwind CSS** - Utility-first CSS framework
- **Font Awesome** - Icon library
- **Chart.js** - Charting library
- **Outfit (Local fonts bundled)** - Typography

## License

This project is for personal use. All third-party libraries retain their original licenses.

## Version

**1.0.0** - November 2025

## Desktop Mode Details

- Single-instance: a small lock file in `instance/` prevents multiple copies.
- Dynamic port: starts on 5000; if busy, tries the next few ports.
- Native window: if `pywebview` is installed, a desktop window opens with no browser chrome. If not, your default browser opens.
- Health: visit `/health` for basic diagnostics.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all dependencies are installed
3. Review browser console (F12) for errors
4. Restore from backup if database is corrupted

---

**Made for personal productivity tracking** 🚀
