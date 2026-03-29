"""GTK import helpers.

GTK and libadwaita require version selection before importing from gi.repository.
"""

import gi

# The Gtk/Adw versions must be required before gi.repository imports.
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import (  # noqa: E402  pylint: disable=wrong-import-position
    Adw,
    Gio,
    GLib,
    Gtk,
)

__all__ = ["Adw", "Gio", "GLib", "Gtk"]
