# Activity Tracker

A standalone desktop application for tracking activities, tasks, and projects with analytics, timeline views, and comprehensive reporting.

## Features

- **Dashboard** - Quick stats, smart suggestions, focus mode, and bulk operations
- **Analytics** - Charts, completion velocity, priority distribution, and insights
- **Timeline** - Visual Gantt-style view of activity lifespans
- **Reports** - Custom date-range reports with export to CSV
- **Themes** - 5 built-in themes (Grayscale, Ocean, Forest, Sunset, Cyberpunk)
- **Offline** - Fully standalone, no internet connection required
- **Automatic Backups** - Daily database backups (keeps last 7)

## Requirements

- Python 3.8 or higher
- Windows 10/11 (tested), macOS/Linux (should work)
- Google Chrome, Firefox, or Edge browser

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
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

5. **Open your browser** to `http://127.0.0.1:5000`

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
```bash
python desktop_app.py
```

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
├── run.py                  # Entry point (app factory)
├── desktop_app.py          # Standalone desktop launcher
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
- Ensure Python 3.8+ is installed: `python --version`
- Verify virtual environment is activated
- Check dependencies: `pip install -r requirements.txt`

**Database errors:**
- Delete `instance/tracker.db` to reset (will lose data)
- Restore from backup: copy from `backups/` folder

**Port already in use:**
- Edit `app.py` and change `port=5000` to another port
- Or stop other Flask applications running

**Styles not loading:**
- Clear browser cache
- Verify `static/` folder contains all assets
- Check browser console for errors (F12)

**PDF export not working:**
- The app uses xhtml2pdf for PDF generation (Windows-friendly, no native libraries required).
- Ensure dependencies are installed: `pip install -r requirements.txt` (includes `xhtml2pdf`).
- If the PDF looks unstyled, verify `static/css/tailwind-built.css` exists. xhtml2pdf supports a subset of CSS; complex Tailwind utilities may be simplified.

---

## Install as Android App (PWA)

Your Activity Tracker is now a **Progressive Web App** that can be installed on Android phones for a native app experience—no Play Store needed!

### Features
- ✅ Install to home screen (looks/launches like a native app)
- ✅ Offline support (cached assets work without internet)
- ✅ Fast load times
- ✅ Full-screen standalone mode
- ✅ Material Design 3 optimized UI

### How to Install on Android

1. **Host the app** (choose one):
   - **Local network:** Run on your PC and access from phone on same WiFi:
     ```powershell
     # Set host to bind to all interfaces
     $env:HOST="0.0.0.0"; python run.py
     ```
     Then visit `http://YOUR_PC_IP:5000` from phone (find PC IP with `ipconfig`)
   
   - **Cloud hosting:** Deploy to a free service like:
     - [Render](https://render.com) - Free tier for web apps
     - [Railway](https://railway.app) - Easy deployment with GitHub
     - [Fly.io](https://fly.io) - Global edge deployment
     - Use the included `Dockerfile` for easy deployment

2. **Install on phone:**
   - Open the app URL in **Chrome** on Android
   - Tap the **⋮** menu (top right)
   - Select **"Install app"** or **"Add to Home Screen"**
   - Confirm installation
   - App icon appears on home screen!

3. **Launch the installed app:**
   - Tap the Activity Tracker icon
   - Runs in full-screen standalone mode
   - Works offline for cached pages

### Testing PWA Locally

Chrome DevTools can simulate PWA installation:
1. Open app in Chrome
2. Press `F12` → `Application` tab
3. Check `Service Workers` (should show registered)
4. Check `Manifest` (validates your `manifest.json`)
5. Use `Lighthouse` audit for PWA score

### PWA Requirements
- ✅ HTTPS (required for service worker in production)
- ✅ `manifest.json` with icons and metadata
- ✅ Service worker (`sw.js`) for offline caching
- ✅ Installable (passes Chrome's install criteria)

**Note:** For local testing, `http://localhost` and `http://127.0.0.1` bypass HTTPS requirement.

---

## Development

**Enable debug mode:**
```python
# In app.py, last line:
app.run(debug=True)
```

**Database migrations:**
- Schema changes: modify models in `app/models.py`
- Delete and recreate: `rm instance/tracker.db; python run.py`

**Add new features:**
1. Create route in `app.py`
2. Add template in `templates/`
3. Update navigation in `layout.html`

## Security Notes

- **Single-user application** - no authentication needed
- **Local only** - binds to 127.0.0.1 (not accessible over network)
- **Secret key** - automatically generated on first run
- **No internet** - all assets local, no external connections

## Credits

- **Tailwind CSS** - Utility-first CSS framework
- **Font Awesome** - Icon library
- **Chart.js** - Charting library
- **Google Fonts (Outfit)** - Typography

## License

This project is for personal use. All third-party libraries retain their original licenses.

## Version

**1.0.0** - November 2025

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Verify all dependencies are installed
3. Review browser console (F12) for errors
4. Restore from backup if database is corrupted

---

**Made for personal productivity tracking** 🚀
