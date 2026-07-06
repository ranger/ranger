"""Cross-platform trash functionality for ranger."""

import os
import shutil
import subprocess
import sys


def trash_paths(paths):
    """Move files to trash, platform-aware.

    Args:
        paths: list of filesystem paths (strings)

    Raises:
        RuntimeError: if no trash method available
        subprocess.CalledProcessError: if trash command fails
    """
    if not paths:
        return

    if sys.platform == 'darwin':
        _trash_macos(paths)
    else:
        _trash_linux(paths)


def _trash_macos(paths):
    """macOS: try 'trash' utility, fallback to AppleScript/Finder."""
    if shutil.which('trash'):
        subprocess.run(['trash'] + paths, check=True)
        return

    for path in paths:
        escaped = path.replace('"', '\\"')
        subprocess.run([
            'osascript', '-e',
            'tell application "Finder" to delete POSIX file "%s"' % escaped
        ], check=True)


def _trash_linux(paths):
    """Linux: try trash-put, gio, fallback to local dir."""
    if shutil.which('trash-put'):
        subprocess.run(['trash-put', '--'] + paths, check=True)
        return

    if shutil.which('gio'):
        subprocess.run(['gio', 'trash'] + paths, check=True)
        return

    _trash_fallback(paths)


def _trash_fallback(paths):
    """Last resort: move to ranger's local trash directory."""
    trash_dir = os.path.expanduser('~/.local/share/ranger/trash')
    os.makedirs(trash_dir, exist_ok=True)
    for path in paths:
        subprocess.run(['mv', '--', path, trash_dir], check=True)