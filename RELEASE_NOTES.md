# Activity Tracker v1.0.0 - Production Release

## About
Activity Tracker is a personal productivity application for Windows that helps you track tasks, monitor progress, and analyze your workflow.

## Installation
1. Extract the entire `ActivityTracker` folder to your desired location (e.g., `C:\Program Files\ActivityTracker`)
2. Double-click `ActivityTracker.exe` to launch the application
3. The application will automatically create a database and configuration files on first run

## System Requirements
- Windows 10 or Windows 11 (64-bit)
- No Python installation required - fully standalone
- Minimum 100MB free disk space
- 2GB RAM recommended

## Features
- ✅ Track activities with priority levels, status, and tags
- ✅ Add updates and notes to activities
- ✅ Weekly goal management
- ✅ Analytics dashboard with charts
- ✅ Timeline view of all activities
- ✅ Custom date range reports
- ✅ Export to PDF, CSV, and ZIP
- ✅ Dark/Light theme with Material Design 3
- ✅ Keyboard shortcuts for power users
- ✅ Bulk operations (status, priority, close)
- ✅ Search and advanced filtering

## First Time Setup
1. Launch the application
2. The database will be automatically created in the `instance/` folder
3. Start adding activities using the "+" button or keyboard shortcut
4. Set weekly goals on the dashboard
5. View analytics and reports as you work

## Data Location
Your data is stored locally in the application folder:
- **Database:** `instance/tracker.db`
- **Logs:** `logs/activity_tracker.log`
- **Backups:** `backups/` (automatic weekly backups)
- **Configuration:** `.secret_key` (generated on first run)

## Backup Your Data
**Important:** Always backup your `instance/tracker.db` file regularly!
- The application creates automatic backups in the `backups/` folder
- You can also manually copy the database file
- Use the "Export All Data" feature to create ZIP archives

## Keyboard Shortcuts
- `?` - Show keyboard shortcuts help
- `U` - Open update modal
- `S` - Focus on status filter
- `G` - Toggle goal form
- `Escape` - Close modals

## Troubleshooting

### Application Won't Start
- Make sure Windows Defender/antivirus isn't blocking it
- Right-click the executable → Properties → Unblock
- Run as Administrator if needed

### Database Errors
- Check that the `instance/` folder has write permissions
- Delete `instance/tracker.db` to reset (you'll lose data!)
- Restore from a backup in the `backups/` folder

### Missing Features/Errors
- Check the `logs/` folder for error messages
- Ensure all files from the distribution are present
- Re-extract from the original ZIP if files are missing

## Version Information
- **Version:** 1.0.0
- **Release Date:** November 8, 2025
- **Build Type:** Production (Standalone Windows Executable)
- **Python Version:** 3.14.0 (embedded)
- **Framework:** Flask 3.1.0

## License
Personal use software. All rights reserved.

## Support
For issues or questions, check the following files in the application folder:
- `AUDIT_REPORT.md` - Comprehensive application audit
- `README.md` - Development documentation
- `MIGRATIONS.md` - Database schema information
- `REFACTORING_SUMMARY.md` - Architecture details

## Updates
Check for updates by visiting the distribution source or monitoring release announcements.

---

**Activity Tracker v1.0.0** - Built with ❤️ for productivity enthusiasts
