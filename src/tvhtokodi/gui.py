#
# Copyright (c) 2023, Chris Allison
#
#     This file is part of tvhtokodi.
#
#     tvhtokodi is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     tvhtokodi is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with tvhtokodi.  If not, see <http://www.gnu.org/licenses/>.
#
"""GTK4 GUI for tvhtokodi - Recording browser and Kodi media organizer."""

import logging
import sys
import threading
from pathlib import Path
from typing import Optional

import tvhtokodi
from tvhtokodi import errorNotify
from tvhtokodi.gtk_setup import Adw, Gio, GLib, Gtk
from tvhtokodi.kodi import (
    kodi_jsonrpc_url,
    kodi_scan_path_for_category,
    scan_kodi_path,
    test_kodi_connection,
)
from tvhtokodi.nfo import hmsDisplay, makeFilmNfo, makeProgNfo
from tvhtokodi.recordings import tidyRecording
from tvhtokodi.remotefiles import (
    allShowFiles,
    copyTVFiles,
    remoteExists,
    remoteWriteTextFile,
)
from tvhtokodi.tvh import allRecordings, deleteRecording

log = logging.getLogger(tvhtokodi.appname)
MOVE_LOCK = threading.Lock()


def escape_markup(text: str) -> str:
    """Escape special HTML/XML characters for use in GTK markup.

    Escapes: &, <, >, ", '
    """
    if not text:
        return text
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


class RecordingRow(Gtk.Box):
    """A single recording row showing title, duration, and metadata."""

    def __init__(self, recording: dict):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(12)
        self.set_margin_end(12)

        self.recording = recording

        # Title
        title_label = Gtk.Label()
        title_text = escape_markup(recording.get("title", "Unknown"))
        title_label.set_markup(f"<b>{title_text}</b>")
        title_label.set_halign(Gtk.Align.START)
        self.append(title_label)

        # Subtitle and duration
        subtitle = recording.get("subtitle", "")
        duration_str = hmsDisplay(recording.get("duration", 0))
        info_text = f"{subtitle} • {duration_str}" if subtitle else duration_str
        info_label = Gtk.Label(label=info_text)
        info_label.set_halign(Gtk.Align.START)
        info_label.add_css_class("dim-label")
        info_label.set_wrap(True)
        self.append(info_label)

        # Description (truncated)
        description = recording.get("disp_description", "")
        if description and len(description) > 100:
            description = description[:100] + "…"
        if description:
            desc_label = Gtk.Label(label=description)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_wrap(True)
            desc_label.add_css_class("dim-label")
            self.append(desc_label)


class RecordingDetailPane(Gtk.Box):
    """Detail pane showing full recording info and category selector."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.recording: Optional[dict] = None
        self.category_combo: Optional[Gtk.ComboBoxText] = None
        self.description_label: Optional[Gtk.Label] = None
        self.season_episode_label: Optional[Gtk.Label] = None
        self.source_filename_label: Optional[Gtk.Label] = None
        self.destination_filename_label: Optional[Gtk.Label] = None

        # Create scrolled window for content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(8)
        content_box.set_margin_start(8)
        content_box.set_margin_end(8)

        # Title
        self.title_label = Gtk.Label(label="Select a recording")
        self.title_label.set_wrap(True)
        self.title_label.set_markup(
            '<b><span size="large">Select a recording</span></b>'
        )
        content_box.append(self.title_label)

        # Channel and date
        self.channel_date_label = Gtk.Label()
        self.channel_date_label.set_halign(Gtk.Align.START)
        self.channel_date_label.add_css_class("dim-label")
        content_box.append(self.channel_date_label)

        # Season/Episode
        self.season_episode_label = Gtk.Label()
        self.season_episode_label.set_halign(Gtk.Align.START)
        self.season_episode_label.add_css_class("dim-label")
        content_box.append(self.season_episode_label)

        # Description
        self.description_label = Gtk.Label()
        self.description_label.set_wrap(True)
        self.description_label.set_halign(Gtk.Align.START)
        self.description_label.set_vexpand(True)
        self.description_label.set_valign(Gtk.Align.START)
        content_box.append(self.description_label)

        # Source filename
        source_heading = Gtk.Label(label="Source file:")
        source_heading.set_halign(Gtk.Align.START)
        source_heading.add_css_class("dim-label")
        content_box.append(source_heading)

        self.source_filename_label = Gtk.Label()
        self.source_filename_label.set_wrap(True)
        self.source_filename_label.set_selectable(True)
        self.source_filename_label.add_css_class("monospace")
        self.source_filename_label.add_css_class("dim-label")
        content_box.append(self.source_filename_label)

        # Destination filename preview
        destination_heading = Gtk.Label(label="Destination file (preview):")
        destination_heading.set_halign(Gtk.Align.START)
        destination_heading.add_css_class("dim-label")
        content_box.append(destination_heading)

        self.destination_filename_label = Gtk.Label()
        self.destination_filename_label.set_wrap(True)
        self.destination_filename_label.set_selectable(True)
        self.destination_filename_label.add_css_class("monospace")
        self.destination_filename_label.add_css_class("dim-label")
        content_box.append(self.destination_filename_label)

        scrolled.set_child(content_box)
        self.append(scrolled)

        # Category selector
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        category_label = Gtk.Label(label="Kodi Category:")
        category_label.set_halign(Gtk.Align.END)
        category_box.append(category_label)

        self.category_combo = Gtk.ComboBoxText()
        self.category_combo.append("drama", "Drama")
        self.category_combo.append("comedy", "Comedy")
        self.category_combo.append("film", "Film")
        self.category_combo.set_active_id("drama")
        self.category_combo.set_hexpand(True)
        category_box.append(self.category_combo)

        self.append(category_box)

    def set_recording(self, recording: dict) -> None:
        """Update the detail pane with a new recording."""
        self.recording = recording

        title = recording.get("title", "Unknown")
        escaped_title = escape_markup(title)
        self.title_label.set_markup(f'<b><span size="large">{escaped_title}</span></b>')

        channel = recording.get("channelname", "Unknown")
        date = recording.get("ctimestart", "")
        self.channel_date_label.set_text(f"{channel} • {date}")

        season = recording.get("season")
        episode = recording.get("episode")
        if season and episode:
            self.season_episode_label.set_text(f"S{season}E{episode}")
            self.season_episode_label.set_visible(True)
        else:
            self.season_episode_label.set_visible(False)

        description = recording.get("disp_description", "")
        if not description:
            description = recording.get("description", "No description available")
        self.description_label.set_text(description)

        filename = recording.get("filename", "")
        self.source_filename_label.set_text(filename)
        self.destination_filename_label.set_text(
            "Select category to preview destination"
        )

        # Auto-suggest category based on series vs film heuristics
        if season and episode:
            self.category_combo.set_active_id("drama")
        else:
            self.category_combo.set_active_id("film")

    def get_selected_category(self) -> str:
        """Get the currently selected category."""
        return self.category_combo.get_active_id()

    def set_destination_preview(self, destination_file: str) -> None:
        """Update destination filename preview in detail pane."""
        if self.destination_filename_label is not None:
            self.destination_filename_label.set_text(destination_file)


class RecordingsWindow(Adw.ApplicationWindow):
    """Main window for browsing and categorizing TVHeadend recordings."""

    def __init__(self, app: Adw.Application, **kwargs):
        super().__init__(application=app, **kwargs)
        self.set_title(f"{tvhtokodi.appname} v{tvhtokodi.version}")
        self.set_default_size(1000, 700)

        self.all_recordings: list[dict] = []
        self.selected_row: Optional[Gtk.ListBoxRow] = None
        self.loading_spinner: Optional[Gtk.Spinner] = None
        self.paned: Optional[Gtk.Paned] = None
        self.kodi_status_label: Optional[Gtk.Label] = None
        self.kodi_test_button: Optional[Gtk.Button] = None
        self.move_status_label: Optional[Gtk.Label] = None
        self.move_progress_bar: Optional[Gtk.ProgressBar] = None
        self.move_progress_pulse_id: Optional[int] = None

        # Build UI
        self._build_ui()

        # Set paned position after window is realized
        self.connect("realize", self._on_window_realize)

        # Run a Kodi connection test on startup.
        self._start_kodi_connection_test()

        # Load recordings in background
        threading.Thread(target=self._load_recordings, daemon=True).start()

    def _build_ui(self) -> None:
        """Build the main UI layout."""
        # Header bar
        header_bar = Adw.HeaderBar()

        # Action buttons
        action_box = Gtk.Box(spacing=8)
        action_box.set_margin_start(8)
        action_box.set_margin_end(8)

        self.move_button = Gtk.Button(label="Move to Kodi")
        self.move_button.add_css_class("suggested-action")
        self.move_button.set_sensitive(False)
        self.move_button.connect("clicked", self._on_move_clicked)
        action_box.append(self.move_button)

        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        action_box.append(refresh_button)

        self.kodi_test_button = Gtk.Button(label="Test Connection")
        self.kodi_test_button.connect("clicked", self._on_test_connection_clicked)
        action_box.append(self.kodi_test_button)

        header_bar.pack_end(action_box)

        self.kodi_status_label = Gtk.Label(
            label="Kodi: checking connection...",
            xalign=0,
        )
        self.kodi_status_label.add_css_class("dim-label")
        self.kodi_status_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        header_bar.pack_start(self.kodi_status_label)

        # Main content - split pane (60/40 split: left pane wider)
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_hexpand(True)
        self.paned.set_vexpand(True)

        # Left: Recordings list (60%)
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        left_box.set_hexpand(True)

        search_box = Gtk.SearchEntry()
        search_box.set_placeholder_text("Search recordings…")
        search_box.set_margin_top(8)
        search_box.set_margin_start(8)
        search_box.set_margin_end(8)
        search_box.connect("search-changed", self._on_search_changed)
        left_box.append(search_box)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-selected", self._on_row_selected)
        self.list_box.add_css_class("navigation-sidebar")

        scrolled_left = Gtk.ScrolledWindow()
        scrolled_left.set_child(self.list_box)
        scrolled_left.set_vexpand(True)
        scrolled_left.set_hexpand(True)
        left_box.append(scrolled_left)

        self.paned.set_start_child(left_box)
        self.paned.set_shrink_start_child(False)

        # Right: Recording details (40%)
        self.detail_pane = RecordingDetailPane()
        self.detail_pane.category_combo.connect("changed", self._on_category_changed)
        self.paned.set_end_child(self.detail_pane)
        self.paned.set_shrink_end_child(False)

        # Layout with header and content
        move_status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        move_status_box.set_margin_top(6)
        move_status_box.set_margin_start(8)
        move_status_box.set_margin_end(8)

        self.move_status_label = Gtk.Label(label="Move status: idle", xalign=0)
        self.move_status_label.add_css_class("dim-label")
        move_status_box.append(self.move_status_label)

        self.move_progress_bar = Gtk.ProgressBar()
        self.move_progress_bar.set_show_text(False)
        self.move_progress_bar.set_fraction(0.0)
        move_status_box.append(self.move_progress_bar)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header_bar)
        main_box.append(move_status_box)
        main_box.append(self.paned)

        self.set_content(main_box)

    def _load_recordings(self) -> None:
        """Load recordings from TVHeadend in background thread."""
        try:
            raw_recs, _ = allRecordings()
            # Filter out radio recordings and tidy them
            self.all_recordings = [
                tidyRecording(rec)
                for rec in raw_recs
                if not rec.get("filename", "").startswith("/var/lib/tvheadend/radio")
            ]

            # Sort by record date (newest first)
            self.all_recordings.sort(key=lambda x: x.get("recorddate", 0), reverse=True)

            # Update UI on main thread
            GLib.idle_add(self._populate_list)
        except Exception as e:
            error_msg = str(e)
            errorNotify(sys.exc_info()[2], e)
            GLib.idle_add(lambda msg=error_msg: self._show_error(msg))

    def _populate_list(self) -> None:
        """Populate the recordings list."""
        self.list_box.remove_all()
        for recording in self.all_recordings:
            row = Gtk.ListBoxRow()
            row.set_child(RecordingRow(recording))
            self.list_box.append(row)

    def _on_row_selected(
        self, list_box: Gtk.ListBox, row: Optional[Gtk.ListBoxRow]
    ) -> None:
        """Handle recording selection."""
        if row is None:
            self.move_button.set_sensitive(False)
            return

        idx = row.get_index()
        if idx >= 0 and idx < len(self.all_recordings):
            self.selected_row = row
            recording = self.all_recordings[idx]
            self.detail_pane.set_recording(recording)
            self._update_destination_preview()
            self.move_button.set_sensitive(True)

    def _on_category_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Update destination preview when media category changes."""
        self._update_destination_preview()

    def _update_destination_preview(self) -> None:
        """Refresh the destination filename preview for current selection/category."""
        if self.detail_pane.recording is None:
            return
        category = self.detail_pane.get_selected_category()
        destination_dir = self._compute_destination(
            self.detail_pane.recording, category
        )
        src_basename = Path(self.detail_pane.recording.get("filename", "")).name
        destination_file = str(Path(destination_dir) / src_basename)
        self.detail_pane.set_destination_preview(destination_file)

    def _on_window_realize(self, window: Adw.ApplicationWindow) -> None:
        """Set the paned position after window is realized."""
        # Defer position setting to idle so the window has its full size
        GLib.idle_add(self._set_paned_position)

    def _set_paned_position(self) -> bool:
        """Set the paned divider to 60/40 split (left pane wider)."""
        if self.paned is None:
            return False

        # Get the paned widget's allocated width
        width = self.paned.get_allocated_width()
        if width > 1:
            # Position at 60% (left pane gets 60%, right pane gets 40%)
            position = int(width * 0.6)
            self.paned.set_position(position)
            return False  # Remove this idle callback
        return True  # Try again later if width not yet allocated

    def _on_search_changed(self, search_entry: Gtk.SearchEntry) -> None:
        """Filter recordings by search text."""
        query = search_entry.get_text().lower()

        for idx, recording in enumerate(self.all_recordings):
            row = self.list_box.get_row_at_index(idx)
            if row:
                matches = (
                    query in recording.get("title", "").lower()
                    or query in recording.get("subtitle", "").lower()
                    or query in recording.get("disp_description", "").lower()
                )
                row.set_visible(matches)

    def _on_move_clicked(self, button: Gtk.Button) -> None:
        """Handle move to Kodi button click."""
        if self.detail_pane.recording is None:
            return

        recording = self.detail_pane.recording
        category = self.detail_pane.get_selected_category()

        # Show confirmation dialog
        dialog = Adw.MessageDialog()
        dialog.set_heading("Move to Kodi?")
        dialog.set_body(
            f"Title: {recording.get('title', 'Unknown')}\n"
            f"Category: {category.title()}\n\n"
            f"After copying, the recording will be deleted from TVHeadend."
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("move", "Move")
        dialog.set_default_response("move")
        dialog.set_response_appearance("move", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_transient_for(self)
        dialog.connect("response", self._on_move_confirmed, recording, category)
        dialog.present()

    def _on_move_confirmed(
        self,
        dialog: Adw.MessageDialog,
        response: str,
        recording: dict,
        category: str,
    ) -> None:
        """Execute move after confirmation."""
        if response != "move":
            return

        if MOVE_LOCK.locked():
            self._show_error(
                "Another move is currently in progress. Please wait for it to finish."
            )
            return

        GLib.idle_add(
            self._set_move_progress,
            "Move status: preparing job",
            0.05,
        )

        # Start move in background thread
        threading.Thread(
            target=self._execute_move, args=(recording, category), daemon=True
        ).start()

        # Show progress dialog
        self.move_button.set_sensitive(False)

    def _execute_move(self, recording: dict, category: str) -> None:
        """Execute the move operation (background thread)."""
        with MOVE_LOCK:
            try:
                GLib.idle_add(
                    self._set_move_progress,
                    "Move status: computing destination and metadata",
                    0.10,
                )
                # Enrich recording with destination path and metadata
                destination = self._compute_destination(recording, category)
                recording["destination"] = destination
                recording["category"] = category

                # Generate appropriate NFO file
                if category == "film":
                    # For films, if no year, use current year as fallback
                    if (
                        "copyright_year" not in recording
                        or recording["copyright_year"] < 1900
                    ):
                        import time

                        recording["year"] = time.localtime().tm_year
                    else:
                        recording["year"] = recording["copyright_year"]
                    nfo_content = makeFilmNfo(recording)
                else:
                    nfo_content = makeProgNfo(recording)

                recording["nfo"] = nfo_content

                log.info(
                    f"Moving {recording['title']} to {destination} category={category}"
                )

                GLib.idle_add(
                    self._set_move_progress,
                    "Move status: discovering source files",
                    0.20,
                )
                # Get all associated files (srt, nfo, txt, etc) from remote host.
                recording["allfiles"] = allShowFiles(recording)
                log.info(f"Associated files: {recording['allfiles']}")
                if not recording["allfiles"]:
                    raise RuntimeError(
                        "No source files found for the selected recording"
                    )

                GLib.idle_add(
                    self._set_move_progress_pulse,
                    "Move status: copying and checksumming files",
                )
                # Copy files on the media server via Fabric/SSH (includes mkdir -p).
                copied = copyTVFiles(recording["allfiles"], destination, banner=True)
                if not copied:
                    raise RuntimeError("Remote copy failed")

                GLib.idle_add(
                    self._set_move_progress,
                    "Move status: writing NFO metadata",
                    0.60,
                )
                # Write generated metadata into destination as a Kodi .nfo file.
                nfo_remote = str(
                    Path(destination) / f"{Path(recording['filename']).stem}.nfo"
                )
                nfo_written = remoteWriteTextFile(
                    nfo_remote, recording["nfo"], banner=True
                )
                if not nfo_written:
                    raise RuntimeError(f"Failed to write NFO file: {nfo_remote}")

                GLib.idle_add(
                    self._set_move_progress,
                    "Move status: deleting TVHeadend recording",
                    0.75,
                )
                # Request TVHeadend to remove the DVR entry and source files.
                deleteRecording(recording["uuid"])

                GLib.idle_add(
                    self._set_move_progress,
                    "Move status: triggering Kodi rescan",
                    0.85,
                )
                # Trigger Kodi scan for the category root path.
                scan_warning = ""
                try:
                    scan_root = kodi_scan_path_for_category(category)
                    scan_kodi_path(scan_root, showdialogs=False)
                except Exception as scan_exc:
                    scan_warning = f"Kodi scan warning: {scan_exc}"
                    log.warning(scan_warning)

                GLib.idle_add(
                    self._set_move_progress,
                    "Move status: verifying source cleanup",
                    0.95,
                )
                # Verify whether source files still exist after deletion request.
                remaining = [fn for fn in recording["allfiles"] if remoteExists(fn)]
                GLib.idle_add(
                    self._on_move_success,
                    recording.get("title", "Unknown"),
                    len(remaining),
                    scan_warning,
                )
            except Exception as e:
                error_msg = f"Move failed: {str(e)}"
                errorNotify(sys.exc_info()[2], e)
                GLib.idle_add(self._on_move_failure, error_msg)

    def _set_move_progress(self, status: str, fraction: float) -> bool:
        """Update move progress widgets from the UI thread."""
        self._stop_move_progress_pulse()
        if self.move_status_label is not None:
            self.move_status_label.set_text(status)
        if self.move_progress_bar is not None:
            self.move_progress_bar.set_fraction(max(0.0, min(1.0, fraction)))
        return False

    def _set_move_progress_pulse(self, status: str) -> bool:
        """Show indeterminate pulse progress for long-running copy/checksum stage."""
        if self.move_status_label is not None:
            self.move_status_label.set_text(status)
        if self.move_progress_bar is not None:
            self.move_progress_bar.set_pulse_step(0.08)
            self.move_progress_bar.pulse()
        if self.move_progress_pulse_id is None:
            self.move_progress_pulse_id = GLib.timeout_add(
                120, self._pulse_move_progress
            )
        return False

    def _pulse_move_progress(self) -> bool:
        """Advance the move progress pulse animation while copy/checksum is running."""
        if self.move_progress_bar is None:
            return False
        self.move_progress_bar.pulse()
        return True

    def _stop_move_progress_pulse(self) -> None:
        """Stop any active indeterminate pulse loop."""
        if self.move_progress_pulse_id is not None:
            GLib.source_remove(self.move_progress_pulse_id)
            self.move_progress_pulse_id = None

    def _reset_move_progress(self) -> bool:
        """Return move progress widgets to idle state."""
        self._stop_move_progress_pulse()
        if self.move_status_label is not None:
            self.move_status_label.set_text("Move status: idle")
        if self.move_progress_bar is not None:
            self.move_progress_bar.set_fraction(0.0)
        return False

    def _on_move_success(
        self, title: str, remaining_count: int, scan_warning: str = ""
    ) -> bool:
        """Handle successful copy and post-delete status in the UI thread."""
        self._set_move_progress("Move status: completed", 1.0)
        if remaining_count == 0 and not scan_warning:
            self._show_success(
                f"Moved '{title}', deleted from TVHeadend, and triggered Kodi scan"
            )
        elif remaining_count == 0:
            self._show_error(f"Moved '{title}'. {scan_warning}")
        else:
            self._show_error(
                f"Moved '{title}', but {remaining_count} source file(s) still exist. {scan_warning}"
            )
        self.move_button.set_sensitive(False)
        threading.Thread(target=self._load_recordings, daemon=True).start()
        GLib.timeout_add(1500, self._reset_move_progress)
        return False

    def _on_move_failure(self, message: str) -> bool:
        """Handle move failures in the UI thread."""
        self._set_move_progress("Move status: failed", 1.0)
        self._show_error(message)
        self.move_button.set_sensitive(True)
        GLib.timeout_add(1500, self._reset_move_progress)
        return False

    def _on_test_connection_clicked(self, button: Gtk.Button) -> None:
        """Handle click on Kodi connection test button."""
        self._start_kodi_connection_test()

    def _start_kodi_connection_test(self) -> None:
        """Start a non-blocking Kodi connection test."""
        if self.kodi_test_button is not None:
            self.kodi_test_button.set_sensitive(False)
        if self.kodi_status_label is not None:
            self.kodi_status_label.set_text("Kodi: checking connection...")
        threading.Thread(target=self._run_kodi_connection_test, daemon=True).start()

    def _run_kodi_connection_test(self) -> None:
        """Run Kodi connection test in a background thread."""
        endpoint = "unknown endpoint"
        try:
            endpoint = kodi_jsonrpc_url()
        except Exception:
            pass

        ok, detail = test_kodi_connection()
        if ok:
            status = f"Kodi: connected - {detail} @ {endpoint}"
        else:
            status = f"Kodi: disconnected - {detail} @ {endpoint}"
        GLib.idle_add(self._set_kodi_connection_status, status)

    def _set_kodi_connection_status(self, status: str) -> bool:
        """Update Kodi connection status in UI thread."""
        if self.kodi_status_label is not None:
            self.kodi_status_label.set_text(status)
        if self.kodi_test_button is not None:
            self.kodi_test_button.set_sensitive(True)
        return False

    def _compute_destination(self, recording: dict, category: str) -> str:
        """Compute the Kodi destination path based on category."""
        title = recording.get("title", "Unknown")
        season = recording.get("season")

        if category == "film":
            filmdir = tvhtokodi.cfg.get("filmdir", "/media/Films")
            year = recording.get("copyright_year", 0)
            if year < 1900:
                year = ""
            title_with_year = f"{title} ({year})" if year else title
            initial = title[0].upper() if title else "?"
            return f"{filmdir}/{initial}/{title_with_year}/"
        else:
            tvdir = tvhtokodi.cfg.get("tvdir", "/media/TV")
            subcategory = "Comedy" if category == "comedy" else "Drama"
            base = f"{tvdir}/{subcategory}/{title}/"
            if season:
                return f"{base}Series {int(season):02d}/"
            return base

    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        """Refresh the recordings list."""
        button.set_sensitive(False)
        threading.Thread(target=self._load_recordings, daemon=True).start()
        GLib.idle_add(lambda: button.set_sensitive(True))

    def _show_error(self, message: str) -> None:
        """Show an error dialog."""
        dialog = Adw.MessageDialog()
        dialog.set_heading("Error")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_transient_for(self)
        dialog.present()

    def _show_success(self, message: str) -> None:
        """Show a success notification."""
        dialog = Adw.MessageDialog()
        dialog.set_heading("Success")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_transient_for(self)
        dialog.present()


class TVHToKodiApplication(Adw.Application):
    """Main application class."""

    def __init__(self):
        super().__init__(
            application_id="com.example.tvhtokodi",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.connect("activate", self.on_activate)

    def on_activate(self, app: Adw.Application) -> None:
        """Handle application activation."""
        window = RecordingsWindow(app)
        window.present()


def doGui() -> None:
    """Entry point for the GTK4 GUI (called by pyproject.toml script)."""
    # Setup logging
    cformat = "%(asctime)s [%(levelname)-5.5s]  %(message)s"
    datefmt = "%d/%m/%Y %H:%M:%S"
    cfmt = logging.Formatter(cformat, datefmt=datefmt)
    consH = logging.StreamHandler(sys.stderr)
    consH.setFormatter(cfmt)
    log.addHandler(consH)
    log.setLevel(logging.DEBUG)

    # Load config
    tvhtokodi.readConfig()

    # Run application
    app = TVHToKodiApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


def main() -> None:
    """Alias for doGui() for standalone execution."""
    doGui()


if __name__ == "__main__":
    main()
