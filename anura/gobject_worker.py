# gobject_worker.py
#
# MIT License
#
# Copyright (c) 2020 Andrey Maksimov <meamka@ya.ru>
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import threading
import traceback
from typing import Callable, Any, Tuple

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
                e.traceback = traceback.format_exc()
                if eb:
                    GLib.idle_add(eb, e)

        # Use default error handler if none provided
        if errorback is None:
            errorback = GObjectWorker._default_errorback

        thread_data = (command, args, callback, errorback)
        worker_thread = threading.Thread(target=run, args=(thread_data,))
        
        # Set as daemon so it doesn't prevent app exit
        worker_thread.daemon = True
        worker_thread.start()

    @staticmethod
    def _default_errorback(error: Exception):
        """
        Standardized error logging for worker thread failures.
        """
        logging.error("Anura Worker Error: Unhandled exception in background thread:\n%s", error.traceback)