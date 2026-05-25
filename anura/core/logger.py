# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import sys
from loguru import logger
from anura.config import LOG_LEVEL

def setup_logging():
    """Configure logging with professional format and rotary settings."""
    logger.remove()  # Remove default handler

    # 1. Standard stderr logging for terminal visibility
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=LOG_LEVEL,
        colorize=True,
        catch=True,
    )

    # 2. Offline Rotary Logging (Zero-Telemetry)
    try:
        # Resolve log directory: XDG_STATE_HOME -> ~/.local/state/anura/logs
        state_home = os.environ.get("XDG_STATE_HOME")
        if not state_home:
            state_home = os.path.expanduser("~/.local/state")

        log_dir = os.path.join(state_home, "anura", "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "anura.log")

        # Add rotary handler: Max 5MB, 3 rotations, plain text
        logger.add(
            log_file,
            rotation="5 MB",
            retention=3,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=LOG_LEVEL,
            compression=None,  # No compression as requested
            catch=True,
            mode="a",
            encoding="utf-8",
        )
        logger.debug(f"Rotary logging initialized at: {log_file}")
    except Exception as e:
        # Fallback if filesystem is read-only or inaccessible
        logger.warning(f"Failed to initialize rotary file logging: {e}")

    logger.debug("Logging system fully initialized.")
