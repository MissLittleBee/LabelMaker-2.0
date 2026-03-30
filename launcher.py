"""Compatibility launcher entry point.

This module exists for legacy scripts or tooling that invoke launcher.py.
It delegates execution to the system-tray launcher.
"""

from launcher_tray import main

if __name__ == "__main__":
    main()
