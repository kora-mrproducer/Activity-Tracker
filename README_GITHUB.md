# 🎯 Activity Tracker

A powerful, production-ready desktop application for tracking activities, managing priorities, and analyzing productivity. Built with Flask, SQLAlchemy, and TailwindCSS.

![Python](https://img.shields.io/badge/python-3.14-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 📊 **Activity Management**
- Create, edit, and track activities with detailed metadata
- Priority levels (High, Medium, Low)
- Status tracking (Ongoing, Closed, N/A)
- Tags for categorization
- Blocking points tracking
- Source attribution

### 📈 **Analytics & Insights**
- Real-time dashboard with key metrics
- Activity completion trends
- Priority distribution charts
- Status overview
- Weekly progress tracking
- 5-minute smart caching for performance

### 🎯 **Goals & Planning**
- Weekly goal setting
- Goal completion tracking
- Progress visualization

### 📝 **Activity Updates**
- Timestamped update history
- Blocking points snapshots
- Timeline view
- Quick update modal

### 🔍 **Universal Search**
- Full-text search across all activities
- Press `/` to search anywhere
- Real-time results with debouncing
- Keyboard navigation (Arrow keys, Enter)

### ⌨️ **Keyboard Shortcuts**
- `J` / `K` - Navigate activities (Vim-style)
- `/` - Open search
- `E` - Edit focused activity
- `A` - Add new activity
- `?` - Show help overlay
- `U` - Quick update (on activity row)
- `S` - Edit status (on activity row)

### 📤 **Export Options**
- **CSV** - Spreadsheet-compatible export
- **PDF** - Professional report generation
- **ZIP** - Complete backup (DB + JSON + CSV)

### 🚀 **Performance Optimizations**
- SQL query optimization (N+1 elimination)
- Analytics caching (5-minute TTL)
- Database indexes on key fields
- Efficient JOIN queries (51 queries → 2 queries)

### 🎨 **Modern UI**
- Material Design 3 styling
- Dark/Light theme support
- Responsive layout
- Custom error pages (404/500)
- Glass morphism effects
- Professional color palette

## 🖥️ Desktop App

**Standalone Windows executable** with:
- ✅ No Python installation required
- ✅ Self-contained (79 MB, 851 files)
- ✅ Custom application icon
- ✅ Production-ready Waitress server
- ✅ Automatic database backups on startup
- ✅ All features working (including PDF export)

## 🛠️ Tech Stack

**Backend:**
- Python 3.14
- Flask 3.0.0
- SQLAlchemy 2.0
- Alembic (migrations)
- xhtml2pdf (PDF generation)
- Waitress (production server)

**Frontend:**
- TailwindCSS 3.x
- JavaScript (ES6+)
- Chart.js (analytics)
- Font Awesome icons
- Outfit font family

**Database:**
- SQLite 3
- Indexed for performance
- Automatic backups

**Development:**
- pytest (66 passing tests)
- PyInstaller (desktop builds)
- Black/Flake8 (code quality)

## 📦 Installation

### **Option 1: Desktop App (Recommended for Users)**

1. Download the latest release from the releases page
2. Extract the ZIP file
3. Run `ActivityTracker.exe`
4. App opens automatically in your browser

### **Option 2: Development Setup**

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/activity-tracker.git
cd activity-tracker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Run development server
python run.py
```

Visit `http://127.0.0.1:5000` in your browser.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_routes.py
```

**Current Status:** ✅ 66/66 tests passing

## 📁 Project Structure

```
activity-tracker/
├── app/                    # Application package
│   ├── __init__.py        # App factory
│   ├── models.py          # Database models
│   ├── utils.py           # Utility functions
│   └── routes/            # Route blueprints
│       ├── activities.py  # Activity management
│       ├── analytics.py   # Analytics & insights
│       ├── exports.py     # Data exports
│       ├── goals.py       # Goal management
│       └── search.py      # Universal search
├── static/                # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript
│   ├── fonts/            # Custom fonts
│   └── fontawesome/      # Icons
├── templates/            # HTML templates
├── tests/                # Test suite
├── migrations/           # Database migrations
├── config.py            # Configuration
├── run.py               # Development server
├── desktop_app.py       # Desktop wrapper
├── requirements.txt     # Python dependencies
└── ActivityTracker.spec # PyInstaller config
```

## ⚙️ Configuration

Create a `.env` file (optional):

```env
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
LOG_MAX_BYTES=5000000
LOG_BACKUP_COUNT=10
```

The app generates a secure secret key automatically if not provided.

## 🔧 Building Desktop App

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --clean --noconfirm ActivityTracker.spec

# Output: dist/ActivityTracker/ActivityTracker.exe
```

## 📊 Performance Benchmarks

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Dashboard queries | 51 | 2 | **25x faster** |
| Analytics (first load) | 350ms | 50ms | **7x faster** |
| Analytics (cached) | 350ms | <10ms | **35x faster** |
| Search query | N/A | <50ms | **NEW** |

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- TailwindCSS for the utility-first CSS framework
- Font Awesome for icons
- Chart.js for analytics visualizations
- The Flask and SQLAlchemy communities

## 📧 Contact

Your Name - [@yourhandle](https://twitter.com/yourhandle)

Project Link: [https://github.com/YOUR_USERNAME/activity-tracker](https://github.com/YOUR_USERNAME/activity-tracker)

---

**Made with ❤️ by [Your Name]**
