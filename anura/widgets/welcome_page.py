# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
from mimetypes import guess_type
from pathlib import Path

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.models.language_item import LanguageItem
from anura.services.language_manager import get_language_manager
from anura.services.settings import settings
from anura.utils import mask_url
from anura.utils.signal_manager import SignalManagerMixin
from anura.widgets.language_popover import LanguagePopover


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/welcome_page.ui")
class WelcomePage(Adw.NavigationPage, SignalManagerMixin):
    __gtype_name__ = "WelcomePage"

    spinner: Gtk.Spinner = Gtk.Template.Child()
    welcome: Adw.StatusPage = Gtk.Template.Child()
    screenshot_button: Gtk.Button = Gtk.Template.Child()
    more_options_button: Gtk.MenuButton = Gtk.Template.Child()
    more_options_popover: Gtk.Popover = Gtk.Template.Child()
    secondary_actions: Gtk.Box = Gtk.Template.Child()
    compact_actions: Gtk.Box = Gtk.Template.Child()
    action_clamp: Adw.Clamp = Gtk.Template.Child()
    open_image_button: Gtk.Button = Gtk.Template.Child()
    paste_image_button: Gtk.Button = Gtk.Template.Child()
    lang_combo: Gtk.MenuButton = Gtk.Template.Child()
    language_popover: LanguagePopover = Gtk.Template.Child()
    drop_button: Gtk.Button = Gtk.Template.Child()
    drop_area: Gtk.Box = Gtk.Template.Child()
    drop_revealer: Gtk.Revealer = Gtk.Template.Child()
    drop_area_label: Gtk.Label = Gtk.Template.Child()

    _language_changed_handler_id: int | None = None
    _drop_button_handler_id: int | None = None

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings

        self.connect_tracked(self.language_popover, "language-changed", self._on_language_changed)

        current_lang_code = self.settings.get_string("active-language")
        current_lang_title = get_language_manager().get_language(current_lang_code)
        self.lang_combo.set_label(current_lang_title)
        self._update_lang_combo_accessibility(current_lang_title)

        self.connect_tracked(self.open_image_button, "clicked", self._on_more_options_action_clicked)
        self.connect_tracked(self.paste_image_button, "clicked", self._on_more_options_action_clicked)
        self.action_buttons = (self.open_image_button, self.paste_image_button, self.drop_button)
        self._wide_action_layout = False
        self._action_layout_tick_id: int | None = None
        self._last_action_width = -1
        self.action_clamp.connect("map", self._on_action_clamp_mapped)
        self.action_clamp.connect("unmap", self._on_action_clamp_unmapped)
        self.connect_tracked(self.drop_button, "clicked", self._on_drop_button_clicked)
        self._setup_drop_target()

        # Initialize drop_button's accessibility expanded state to False
        if self.drop_button:
            self.drop_button.update_state([Gtk.AccessibleState.EXPANDED], [False])

        # Keyboard support: Add key controller to drop_area to collapse on Escape
        self._drop_key_ctrl = Gtk.EventControllerKey()
        self._drop_key_ctrl.connect("key-pressed", self._on_drop_area_key_pressed)
        self.drop_area.add_controller(self._drop_key_ctrl)

    def _on_drop_area_key_pressed(
        self,
        _controller: Gtk.EventControllerKey,
        keyval: int,
        _keycode: int,
        _state: Gdk.ModifierType,
    ) -> bool:
        """Collapse the drop area when user presses Escape inside it."""
        if keyval == Gdk.KEY_Escape and self.drop_revealer.get_reveal_child():
            self.drop_revealer.set_reveal_child(False)
            self.drop_button.remove_css_class("suggested-action")
            self.drop_button.set_tooltip_text(_("Drop image here"))
            self.drop_button.update_state([Gtk.AccessibleState.EXPANDED], [False])
            self.drop_button.update_property([Gtk.AccessibleProperty.LABEL], [_("Drop image here")])
            GLib.idle_add(self._focus_drop_action_idle)
            return True
        return False

    def _setup_drop_target(self) -> None:
        """Configure drop target with DropTargetAsync and explicit text/uri-list.

        We deliberately request only 'text/uri-list' and NOT Gdk.FileList.

        Why: including Gdk.FileList causes GTK to prefer
        'application/vnd.portal.filetransfer' as transfer channel. In VirtualBox
        guests with non-GNOME sessions (LXQt, XFCE, LXDE), xdg-desktop-portal is
        not available — the portal call hangs silently and the callback is NEVER
        invoked (no GLib.Error is raised, making it impossible to detect or recover).

        By requesting 'text/uri-list' exclusively, GDK uses the raw Xdnd protocol
        which PCManFM, Thunar and all standard file managers provide directly,
        bypassing the portal entirely.

        The stream read is fully asynchronous (read_bytes_async) so the GTK
        main loop is never blocked.
        """
        formats = Gdk.ContentFormats.new(["text/uri-list"])
        self._drop_target = Gtk.DropTargetAsync(
            formats=formats,
            actions=Gdk.DragAction.COPY,
        )
        self._drop_cancellable: Gio.Cancellable | None = None

        self.connect_tracked(self._drop_target, "drop", self._on_dnd_drop)
        self.connect_tracked(self._drop_target, "drag-enter", self._on_dnd_enter)
        self.connect_tracked(self._drop_target, "drag-leave", self._on_dnd_leave)

        self.add_controller(self._drop_target)

    def _get_wide_action_threshold(self) -> int:
        """Measure the width required by the three equal secondary action columns."""
        natural_widths = []
        for button in self.action_buttons:
            minimum_size, natural_size = button.get_preferred_size()
            natural_widths.append(max(minimum_size.width, natural_size.width))
        equal_column_width = max(natural_widths, default=0)
        return (
            (equal_column_width * len(self.action_buttons))
            + (self.secondary_actions.get_spacing() * (len(self.action_buttons) - 1))
            + self.secondary_actions.get_margin_start()
            + self.secondary_actions.get_margin_end()
        )

    def _on_action_clamp_mapped(self, _widget: Adw.Clamp) -> None:
        """Monitor allocated width while the responsive action container is mapped."""
        if self._action_layout_tick_id is None:
            self._last_action_width = -1
            self._action_layout_tick_id = self.action_clamp.add_tick_callback(self._on_action_layout_tick)
            GLib.idle_add(self._update_action_layout_idle)

    def _on_action_clamp_unmapped(self, _widget: Adw.Clamp) -> None:
        """Stop the frame-clock monitor while the page is not mapped."""
        if self._action_layout_tick_id is not None:
            self.action_clamp.remove_tick_callback(self._action_layout_tick_id)
            self._action_layout_tick_id = None

    def _update_action_layout_idle(self) -> bool:
        """Evaluate the initial layout after GTK completes the map allocation."""
        self._update_action_layout()
        return GLib.SOURCE_REMOVE

    def _on_action_layout_tick(self, widget: Gtk.Widget, _frame_clock: Gdk.FrameClock) -> bool:
        """Re-evaluate only when GTK allocates a different width."""

        available_width = widget.get_width()
        if available_width != self._last_action_width:
            self._last_action_width = available_width
            self._update_action_layout()
        return GLib.SOURCE_CONTINUE

    def _update_action_layout(self) -> None:
        """Choose the wide layout only when all three measured actions fit."""
        available_width = self.action_clamp.get_width()
        if available_width > 0:
            self._set_action_layout(available_width >= self._get_wide_action_threshold())

    def _set_action_layout(self, wide: bool) -> None:
        """Move the existing controls between layouts without duplicating actions."""
        if self._wide_action_layout == wide:
            return

        root = self.get_root()
        focused_widget = root.get_focus() if root and hasattr(root, "get_focus") else None
        focused_action = focused_widget if focused_widget in self.action_buttons else None
        destination = self.secondary_actions if wide else self.compact_actions

        for button in self.action_buttons:
            parent = button.get_parent()
            if parent is destination:
                continue
            if isinstance(parent, Gtk.Box):
                parent.remove(button)
            destination.append(button)

        self._wide_action_layout = wide
        self.secondary_actions.set_visible(wide)
        self.more_options_button.set_visible(not wide)

        if wide:
            self.more_options_popover.popdown()
            if focused_widget is self.more_options_button:
                self.screenshot_button.grab_focus()

        if focused_action is not None:
            if wide:
                GLib.idle_add(lambda: (focused_action.grab_focus(), GLib.SOURCE_REMOVE)[1])
            else:
                GLib.idle_add(self._focus_more_options_idle)

    def _focus_more_options_idle(self) -> bool:
        """Restore focus after the compact menu trigger becomes visible."""
        self.more_options_button.grab_focus()
        return GLib.SOURCE_REMOVE

    def _focus_drop_action(self) -> None:
        """Focus the visible Drop control or its compact-layout menu trigger."""
        target = self.drop_button if self._wide_action_layout else self.more_options_button
        target.grab_focus()

    def _focus_drop_action_idle(self) -> bool:
        """Restore focus after the drop area has completed its collapse transition."""
        self._focus_drop_action()
        return GLib.SOURCE_REMOVE

    def _on_more_options_action_clicked(self, _button: Gtk.Button) -> None:
        """Close the image-actions popover after choosing an action."""
        self.more_options_popover.popdown()

    def _on_drop_button_clicked(self, _button: Gtk.Button) -> None:
        """Close the actions menu and toggle the dedicated drop area."""
        try:
            self.more_options_popover.popdown()
            is_revealed = self.drop_revealer.get_reveal_child()
            new_revealed = not is_revealed
            self.drop_revealer.set_reveal_child(new_revealed)
            if new_revealed:
                self.drop_button.add_css_class("suggested-action")
                self.drop_button.set_tooltip_text(_("Hide drop area"))
                self.drop_button.update_state([Gtk.AccessibleState.EXPANDED], [True])
                self.drop_button.update_property([Gtk.AccessibleProperty.LABEL], [_("Hide drop area")])
                # Shift focus directly to the revealed drop area for accessible navigation asynchronously
                GLib.idle_add(lambda: (self.drop_area.grab_focus(), GLib.SOURCE_REMOVE)[1])
            else:
                self.drop_button.remove_css_class("suggested-action")
                self.drop_button.set_tooltip_text(_("Drop image here"))
                self.drop_button.update_state([Gtk.AccessibleState.EXPANDED], [False])
                self.drop_button.update_property([Gtk.AccessibleProperty.LABEL], [_("Drop image here")])
                # Shift focus back to the toggle button asynchronously
                GLib.idle_add(self._focus_drop_action_idle)
        except Exception as e:
            logger.exception(f"Anura: Failed to handle drop button click: {e}")

    def _on_dnd_enter(self, _target: Gtk.DropTargetAsync, _drop: Gdk.Drop, _x: float, _y: float) -> Gdk.DragAction:
        """Visual feedback when drag enters the drop area."""
        try:
            self.drop_revealer.set_reveal_child(True)
            self.drop_area.add_css_class("drag-hover")
            self.welcome.set_description(_("Drop image to extract text"))
        except (AttributeError, RuntimeError) as e:
            logger.exception(f"Anura: Failed to handle DnD enter: {e}")
        return Gdk.DragAction.COPY

    def _on_dnd_leave(self, _target: Gtk.DropTargetAsync, _drop: Gdk.Drop) -> None:
        """Remove visual feedback when drag leaves the drop area."""
        try:
            self.drop_area.remove_css_class("drag-hover")
            # Only hide if it wasn't already revealed (user clicked button)
            if not self.drop_button.has_css_class("suggested-action"):
                self.drop_revealer.set_reveal_child(False)
            self.welcome.set_description(_("Extract text from anywhere"))
        except (AttributeError, RuntimeError) as e:
            logger.exception(f"Anura: Failed to handle DnD leave: {e}")

    def _on_dnd_drop(self, _target: Gtk.DropTargetAsync, drop: Gdk.Drop, _x: float, _y: float) -> bool:
        """Handle drop signal. Initiates a fully async stream read of text/uri-list.

        We always read text/uri-list (never Gdk.FileList) to bypass the
        xdg-desktop-portal which is unavailable in VirtualBox/non-GNOME guests.
        drop.finish() MUST be called in the final callback (Xdnd protocol requirement).
        """
        self.drop_area.remove_css_class("drag-hover")
        window = self.get_root()
        operation_id = window._begin_ocr_operation() if window and hasattr(window, "_begin_ocr_operation") else None
        if operation_id is not None:
            self._set_drop_area_processing_state(True)

        if self._drop_cancellable:
            self._drop_cancellable.cancel()
        # #538: keep this reference and carry it through the async chain, so a
        # late callback from a cancelled drop cannot clear the newest drop's
        # cancellable (which would make the active read uncancellable).
        cancellable = Gio.Cancellable()
        self._drop_cancellable = cancellable

        drop.read_async(
            ["text/uri-list"],
            GLib.PRIORITY_DEFAULT,
            cancellable,
            self._on_drop_stream_ready,
            (drop, cancellable, operation_id),
        )
        return True  # Accept the drop; finish() will be called in _on_drop_bytes_ready

    def _on_drop_stream_ready(
        self,
        source_object: Gdk.Drop,
        result: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        """Called when the Xdnd stream is ready. Starts async byte read.

        source_object is the Gdk.Drop that initiated read_async (not an InputStream).
        We immediately start read_bytes_async — no blocking calls here.
        """
        drop, cancellable, operation_id = user_data
        try:
            input_stream, _mime_type = source_object.read_finish(result)
        except GLib.Error as e:
            logger.error(f"DnD: Failed to open drop stream: {e}")
            drop.finish(Gdk.DragAction.COPY)  # Always finish, even on error
            self._show_error_toast(_("Failed to read dropped file"), operation_id)
            return

        if not self._is_drop_operation_current(operation_id):
            drop.finish(Gdk.DragAction.COPY)
            return

        input_stream.read_bytes_async(
            65536,  # 64 KB — more than enough for any URI list
            GLib.PRIORITY_DEFAULT,
            cancellable,
            self._on_drop_bytes_ready,
            (input_stream, drop, cancellable, operation_id),
        )

    def _on_drop_bytes_ready(
        self,
        input_stream: Gio.InputStream,
        result: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        """Called when bytes are available. Parses URIs and triggers OCR.

        This is the end of the async chain. We call drop.finish() here (required),
        then process the first valid local image path.
        """
        stream, drop, cancellable, operation_id = user_data

        try:
            gbytes = stream.read_bytes_finish(result)
        except GLib.Error as e:
            logger.error(f"DnD: Failed to read drop bytes: {e}")
            drop.finish(Gdk.DragAction.COPY)
            self._show_error_toast(_("Failed to read dropped file"), operation_id)
            return
        finally:
            # #538: only release the cancellable this callback owns; a newer
            # drop may already have installed its own.
            if self._drop_cancellable is cancellable:
                self._drop_cancellable = None

        # Xdnd protocol: always call finish BEFORE processing
        drop.finish(Gdk.DragAction.COPY)
        if not self._is_drop_operation_current(operation_id):
            return

        raw = gbytes.get_data() if gbytes else None
        if not raw:
            logger.error("DnD: Received empty data from drop stream")
            self._show_error_toast(_("No file data received from drop"), operation_id)
            return

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")

        # Parse text/uri-list: skip comment lines (#) and empty lines
        uris = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]

        if not uris:
            logger.error("DnD: No valid URIs found in drop data")
            self._show_error_toast(_("No valid file found in drop"), operation_id)
            return

        # Anura processes one image at a time — take the first URI
        gfile = Gio.File.new_for_uri(uris[0])
        local_path = gfile.get_path()

        if not local_path:
            logger.error(f"DnD: URI has no local path: {mask_url(uris[0])}")
            self._show_error_toast(_("Only local files can be dropped"), operation_id)
            return

        self._process_dropped_path(local_path, operation_id)

    def cancel_pending_drop(self) -> None:
        """Cancel an asynchronous URI-list read when another OCR request starts."""
        cancellable = self._drop_cancellable
        self._drop_cancellable = None
        if cancellable is not None:
            cancellable.cancel()

    def _is_drop_operation_current(self, operation_id: int | None) -> bool:
        """Reject late asynchronous DnD callbacks after a newer OCR request starts."""
        if operation_id is None:
            return True
        window = self.get_root()
        return bool(window and window._is_current_ocr_operation(operation_id))

    def _process_dropped_path(self, local_path: str, operation_id: int | None = None) -> None:
        """Common logic for processing a verified local path from any DnD format."""
        if not Path(local_path).exists():
            logger.error(f"DnD: File not accessible: {local_path}")
            self._show_error_toast(
                _("File not accessible. Ensure Anura has permission to access this location."), operation_id
            )
            return

        (mimetype, _encoding) = guess_type(local_path)
        logger.debug(f"DnD: Dropped file ({mimetype}): {local_path}")

        if not mimetype or not mimetype.startswith("image"):
            self._show_error_toast(_("Only images can be processed that way."), operation_id)
            return

        window = self.get_root()
        if not window or not hasattr(window, "dnd_controller"):
            logger.error("DnD: Root window missing process_dnd_file_sync")
            self._show_error_toast(_("Failed to process dropped file"), operation_id)
            return

        if not self._is_drop_operation_current(operation_id):
            return
        self._set_drop_area_processing_state(True)
        window.dnd_controller.process_dnd_file_sync(local_path, operation_id)

    def _show_error_toast(self, message: str, operation_id: int | None = None) -> None:
        """Show a DnD error without disturbing a newer operation's UI state."""
        if operation_id is not None and not self._is_drop_operation_current(operation_id):
            return
        window = self.get_root()
        if window and hasattr(window, "show_toast"):
            window.show_toast(message)
        if operation_id is not None and window and hasattr(window, "_finish_ocr_operation"):
            window._finish_ocr_operation(operation_id)
        elif operation_id is None:
            self._set_drop_area_processing_state(False)

    def _set_drop_area_processing_state(self, processing: bool) -> None:
        """Set the drop area visual state to indicate processing (OCR in progress)."""
        if processing:
            self.drop_area.add_css_class("drag-processing")
            if self.drop_area_label:
                self.drop_area_label.set_label(_("Processing..."))
            self.drop_area.update_property([Gtk.AccessibleProperty.LABEL], [_("Image drop zone: Processing...")])
        else:
            self.drop_area.remove_css_class("drag-processing")
            if self.drop_area_label:
                self.drop_area_label.set_label(_("Drop image file here"))
            self.drop_area.update_property([Gtk.AccessibleProperty.LABEL], [_("Image drop zone")])

    def reset_drop_area_visual_state(self) -> None:
        """Reset DnD visuals without taking ownership of the shared OCR spinner."""
        self._set_drop_area_processing_state(False)
        self.drop_revealer.set_reveal_child(False)
        self.drop_button.remove_css_class("suggested-action")
        self.drop_button.set_tooltip_text(_("Drop image here"))
        self.drop_button.update_state([Gtk.AccessibleState.EXPANDED], [False])
        self.drop_button.update_property([Gtk.AccessibleProperty.LABEL], [_("Drop image here")])
        self.welcome.set_description(_("Extract text from anywhere"))

    def reset_drop_area_state(self) -> None:
        """Backward-compatible full reset for callers that own OCR completion."""
        self.reset_drop_area_visual_state()
        self.hide_spinner()

    def set_status(self, status_msg: str) -> None:
        """Update the status label during processing."""
        if self.drop_area_label:
            self.drop_area_label.set_label(status_msg)

    def hide_spinner(self) -> None:
        """Stop and hide the spinner."""
        self.spinner.stop()
        self.spinner.set_visible(False)

    def show_spinner(self) -> None:
        """Start and show the spinner."""
        self.spinner.set_visible(True)
        self.spinner.start()

    def _update_lang_combo_accessibility(self, language_title: str) -> None:
        """Update tooltip and accessible label for lang_combo with active language context."""
        tooltip = _("OCR language: {language} (click to change)").format(language=language_title)
        if self.lang_combo:
            self.lang_combo.set_tooltip_text(tooltip)
            self.lang_combo.update_property([Gtk.AccessibleProperty.LABEL], [tooltip])

    def _on_language_changed(self, _: LanguagePopover, language: LanguageItem) -> None:
        self.lang_combo.set_label(language.title)
        self._update_lang_combo_accessibility(language.title)
        self.settings.set_string("active-language", language.code)

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        # BUG-041: Automated signal teardown via SignalManagerMixin
        self.teardown_all()

        # Cancel any in-flight drop operation
        drop_cancellable = getattr(self, "_drop_cancellable", None)
        if drop_cancellable:
            drop_cancellable.cancel()
            self._drop_cancellable = None

        # Remove key controller
        if hasattr(self, "_drop_key_ctrl") and self._drop_key_ctrl:
            self.drop_area.remove_controller(self._drop_key_ctrl)
            self._drop_key_ctrl = None

        # Remove drop target controller
        if hasattr(self, "_drop_target") and self._drop_target:
            self.remove_controller(self._drop_target)
            self._drop_target = None

        super().do_destroy()
