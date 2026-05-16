# gobject_worker.py
#
# MIT License
#
# Copyright (c) 2020 Andrey Maksimov <meamka@ya.ru>
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#

from collections.abc import Callable
import logging
import threading
import traceback

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")

from gi.repository import GLib  # noqa: E402


class GObjectWorker:
    """
    Asynchronous task execution utility for Anura.
    Offloads blocking operations to a background thread and returns
    execution to the GLib main loop via idle_add.
    """

    @staticmethod
    def call(
        command: Callable,
        args: tuple = (),
        callback: Callable | None = None,
        errorback: Callable | None = None,
    ) -> None:
        """
        Executes a command in a separate thread.

        Args:
            command: The function to execute.
            args: Arguments for the command.
            callback: Function to call on the main thread upon success.
            errorback: Function to call on the main thread upon failure.
        """

        def run(data: tuple) -> None:
            cmd, cmd_args, cb, eb = data
            try:
                # Execute the heavy task
                result = cmd(*cmd_args)
                # Return result to the UI thread safely
                if cb:
                    # Use a wrapper that ensures False is returned to GLib.idle_add
                    # while passing the result to the actual callback.
                    def cb_wrapper(res):
                        try:
                            cb(res)
                        except Exception:
                            logging.exception("Unhandled error in GObjectWorker success callback")
                        return GLib.SOURCE_REMOVE

                    GLib.idle_add(cb_wrapper, result, priority=GLib.PRIORITY_DEFAULT)
            except (KeyboardInterrupt, SystemExit):
                # Re-raise to allow clean shutdown
                raise
            except (OSError, ValueError, RuntimeError) as e:
                # Handle expected operational errors (file I/O, invalid values, runtime issues)
                tb_str = traceback.format_exc()

                def eb_wrapper(error, tb):
                    try:
                        eb(error, tb)
                    except Exception:
                        logging.exception("Unhandled error in GObjectWorker error callback")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(eb_wrapper, e, tb_str, priority=GLib.PRIORITY_DEFAULT)
            except Exception as e:
                # Handle truly unexpected errors (logical errors, system failures)
                tb_str = traceback.format_exc()
                logging.error(f"Unexpected error in GObjectWorker: {e}")

                def eb_wrapper(error, tb):
                    try:
                        eb(error, tb)
                    except Exception:
                        logging.exception("Unhandled error in GObjectWorker fallback error callback")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(eb_wrapper, e, tb_str, priority=GLib.PRIORITY_DEFAULT)

        # Use default error handler if none provided
        if errorback is None:
            errorback = GObjectWorker._default_errorback

        thread_data = (command, args, callback, errorback)
        worker_thread = threading.Thread(target=run, args=(thread_data,))

        # Set as daemon so it doesn't prevent app exit
        worker_thread.daemon = True
        worker_thread.start()

    @staticmethod
    def _default_errorback(error: Exception, traceback_str: str | None = None) -> None:
        """
        Standardized error logging for worker thread failures.
        """
        tb = traceback_str or getattr(error, "__traceback__", None)
        if tb:
            logging.error("Anura Worker Error: Unhandled exception in background thread:\n%s", tb)
