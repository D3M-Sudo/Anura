# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os

from loguru import logger


def boot_audit():
    """Perform boot-time capability audit."""
    os.environ.setdefault("NO_AT_BRIDGE", "1")
    os.environ.setdefault("GTK_A11Y", "none")

    from anura.types.context import get_app_context

    get_app_context()
    logger.debug("Boot audit completed.")
