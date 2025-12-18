"""
Build script for creating Windows executable with PyInstaller.

This script packages the ENTIRE Flask application into ONE standalone .exe file.
NO external folders needed - everything is embedded in the EXE!
"""

import os
from pathlib import Path

import PyInstaller.__main__

# Get the directory where this script is located
script_dir = Path(__file__).parent

# Separator for --add-data (: on Linux/Mac, ; on Windows)
sep = ";" if os.name == "nt" else ":"

# PyInstaller configuration
PyInstaller.__main__.run(
    [
        str(script_dir / "launcher_tray.py"),  # Entry point (system tray launcher)
        "--name=LabelMaker",  # Name of the executable
        "--onefile",  # Create ONE single executable file (everything embedded)
        "--windowed",  # No console window (runs silently)
        "--icon=NONE",  # Add icon path here if you have one (e.g., --icon=icon.ico)
        # ⭐ EMBED ALL DATA FILES INTO EXE ⭐
        # These will be extracted to temp folder at runtime
        f"--add-data={script_dir / 'app'}{sep}app",  # Embed entire app/ folder
        f"--add-data={script_dir / 'templates'}{sep}templates",  # Embed templates/
        f"--add-data={script_dir / 'static'}{sep}static",  # Embed static/
        # Hidden imports that PyInstaller might miss (Flask, SQLAlchemy, ReportLab)
        "--hidden-import=flask",
        "--hidden-import=flask_sqlalchemy",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.pdfgen",
        "--hidden-import=reportlab.lib",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.lib.units",
        "--hidden-import=reportlab.pdfbase",
        "--hidden-import=reportlab.pdfbase.ttfonts",
        "--hidden-import=reportlab.pdfbase.pdfmetrics",
        "--hidden-import=pystray",  # System tray support
        "--hidden-import=PIL",  # PIL for system tray icon
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        # Collect all Flask/SQLAlchemy submodules
        "--collect-all=flask",
        "--collect-all=flask_sqlalchemy",
        # Clean previous builds
        "--clean",
        # Output directory
        f"--distpath={script_dir / 'dist'}",
        f"--workpath={script_dir / 'build'}",
        f"--specpath={script_dir}",
    ]
)

print("\n" + "=" * 70)
print("✅ Build complete!")
print(f"📦 Single EXE file: {script_dir / 'dist' / 'LabelMaker.exe'}")
print("\n📝 Distribution:")
print("   Just copy LabelMaker.exe - that's it!")
print("   • All Python code is embedded")
print("   • All templates are embedded")
print("   • All static files are embedded")
print("   • Database will be created automatically in instance/")
print("\n⚠️  Note: First run may take 5-10 seconds (extracting to temp)")
print("=" * 70)
