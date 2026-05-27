# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
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
        state_home_path = Path(state_home) if state_home else Path.home() / ".local" / "state"

        log_dir = state_home_path / "anura" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "anura.log"

        # Add rotary handler: Max 5MB, 5 rotations, compressed plain text
        logger.add(
            log_file,
            rotation="5 MB",
            retention=5,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=LOG_LEVEL,
            compression="gz",  # Enable compression for better retention
            catch=True,
            mode="a",
            encoding="utf-8",
        )
        logger.debug(f"Rotary logging initialized at: {log_file}")
    except (OSError, RuntimeError) as e:
        # Fallback if filesystem is read-only or inaccessible
        logger.warning(f"Failed to initialize rotary file logging: {e}")

    logger.debug("Logging system fully initialized.")
