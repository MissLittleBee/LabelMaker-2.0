# LabelMaker 2.0

Modern web application for Czech pharmacy to generate price labels with full Czech diacritics support.

## 🎯 Features

- **Label Management** - Create, edit, and delete price labels
- **Form Management** - Manage pharmaceutical forms (tablets, drops, ointments, ...)
- **PDF Generation** - Print labels per A4 page (48×35mm, 0mm gaps)
- **Czech Support** - Full support for Czech characters (č, ř, ž, Č, Ř, Ž)
- **Smart Text Wrapping** - Automatic wrapping of long product names (max 25 chars/line)
- **Sorting** - Sort by name, date, or print status
- **Bulk Operations** - Mark/unmark all labels for printing

## 📋 Requirements

- Python 3.9 or newer
- Web browser (Chrome, Firefox, Edge, Safari)

## 🚀 Instalace a Spuštění

### Step 1: clone this repo

```bash
git clone <repository-url>
cd "LabelMaker 2.0"
```

### Step 2: Create venv (recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the application

```bash
python main.py
```

The application will start automatically at: **http://127.0.0.1:5000**

## 🖨️ Usage

### Adding a pharmaceutical form
1. Click on "Lékové formy" (Forms)
2. Fill in name (e.g., "Tablety"), short name (e.g., "tbl"), and unit (e.g., "ks")
3. Click "Přidat formu" (Add form)

### Creating a label
1. Click on "Nová cenovka" (New label)
2. Fill in:
   - **Product name** - e.g., "Paralen 500mg"
   - **Pharmaceutical form** - select from dropdown
   - **Amount** - e.g., 24 (pieces)
   - **Price** - e.g., 89.50 Kč
3. Check "Označit k tisku" (Mark for printing) if you want to print immediately
4. Click "Přidat cenovku" (Add label)

### Printing labels
1. On the "Cenovky" (Labels) page, check the labels you want to print
2. Click "Tisknout označené" (Print marked)
3. Review the preview and click "Stáhnout PDF" (Download PDF)
4. Print the PDF on colored A4 paper

### Printing tips
- **Paper**: A4 colored paper (48×35mm labels)
- **Orientation**: Portrait
- **Margins**: 0mm (full bleed)
- **Scale**: 100% (no scaling)
- **Layout**: 32 labels (4 columns × 8 rows)

## 🏗️ Project Structure

```
LabalMaker 2.0/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── BUILD_INSTRUCTIONS.md  # Guide for building Windows EXE
├── launcher.py            # Windows launcher (with console)
├── launcher_tray.py       # Windows launcher (system tray)
├── build_exe.py           # Build script for PyInstaller
│
├── app/                   # Main application
│   ├── __init__.py
│   ├── app.py            # Flask application factory
│   ├── config.py         # Configuration
│   ├── db.py             # Database (SQLAlchemy)
│   ├── models.py         # Database models
│   ├── utils.py          # Utility functions
│   ├── pdf_generator.py  # PDF generation
│   ├── central_logging.py # Logging configuration
│   │
│   └── routes/           # Flask routes
│       ├── routes.py     # Main routes
│       ├── labels/       # Routes for labels
│       └── forms/        # Routes for pharmaceutical forms
│
├── templates/            # HTML templates (Jinja2)
│   ├── base.html
│   ├── home.html
│   ├── labels/
│   └── forms/
│
├── static/               # Static files
│   ├── css/
│   └── js/
│
└── instance/             # Instance data (created automatically)
    ├── labelmaker.db     # SQLite database
    └── logs/             # Application logs
```

## 🛠️ Technologies

- **Backend**: Flask 3.0+ (Python web framework)
- **Database**: SQLite + SQLAlchemy ORM
- **PDF**: ReportLab with DejaVu Sans fonts
- **Frontend**: Vanilla JavaScript + CSS
- **Templating**: Jinja2

## 📦 Windows EXE Version

For creating a standalone Windows EXE file, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md).

## 🔧 Configuration

### Environment Variables

```bash
# Database path (optional)
DATABASE_URL=sqlite:///path/to/custom.db

# Logging level (optional)
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR

# Debug mode (optional)
DEBUG=true  # or false
```

### Changing Port

Edit `main.py`:
```python
app.run(debug=True, port=8080)  # Change 5000 to 8080
```

## 🐛 Troubleshooting

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

### Database errors
```bash
# Delete database and start fresh
rm -rf instance/labelmaker.db
python main.py
```

### Czech characters not displaying in PDF
- The application uses DejaVu Sans fonts with full Czech support
- If missing, install: `pip install reportlab --upgrade`

### Application won't start
```bash
# Check Python version (must be 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📝 Database Schema

### Table: `label` (Price Labels)
- `id` - Primary key (auto-increment)
- `product_name` - Product name
- `form` - Pharmaceutical form (foreign key)
- `amount` - Amount/quantity
- `price` - Price
- `unit_price` - Price per unit (auto-calculated)
- `marked_to_print` - Marked for printing (boolean)
- `created_at` - Creation date

### Table: `form` (Pharmaceutical Forms)
- `name` - Form name (primary key)
- `short_name` - Abbreviation (unique)
- `unit` - Unit (ks, ml, g, ...)

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 License

MIT

## 👨‍💻 Author

Barbora Hůlová

---

**Version**: 2.0  
**Date**: December 2025  
**Status**: ✅ Production Ready
