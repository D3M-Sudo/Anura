# gobject_worker.py
#
# MIT License
#
# Copyright (c) 2020 Andrey Maksimov <meamka@ya.ru>
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#

import logging
import threading
import traceback
from typing import Callable, Tuple

from gi.repository import GLib


class GObjectWorker:
    """
    Asynchronous task execution utility for Anura.
    Offloads blocking operations to a background thread and returns
    execution to the GLib main loop via idle_add.
    """

    @staticmethod
    def call(command: Callable, args: Tuple = (), callback: Callable = None, errorback: Callable = None):
        """
        Executes a command in a separate thread.

        Args:
            command: The function to execute.
            args: Arguments for the command.
            callback: Function to call on the main thread upon success.
            errorback: Function to call on the main thread upon failure.
        """
        def run(data):
            cmd, cmd_args, cb, eb = data
            try:
                # Execute the heavy task
                result = cmd(*cmd_args)
                # Return result to the UI thread safely
                if cb:
                    GLib.idle_add(cb, result)
            except Exception as e:
                # Capture full traceback for technical debugging
                tb_str = traceback.format_exc()
                # Wrap exception with traceback info in a safe way
                # (errorback is always set to _default_errorback if not provided)
                GLib.idle_add(eb, e, tb_str)

        # Use default error handler if none provided
        if errorback is None:
            errorback = GObjectWorker._default_errorback

        thread_data = (command, args, callback, errorback)
        worker_thread = threading.Thread(target=run, args=(thread_data,))

        # Set as daemon so it doesn't prevent app exit
        worker_thread.daemon = True
        worker_thread.start()

    @staticmethod
    def _default_errorback(error: Exception, traceback_str: str = None):
        """
        Standardized error logging for worker thread failures.
        """
        tb = traceback_str or getattr(error, '__traceback__', None)
        if tb:
            logging.error("Anura Worker Error: Unhandled exception in background thread:\n%s", tb)
