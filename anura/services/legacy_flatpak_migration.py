# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""One-time migration of persistent data from Anura's previous Flatpak ID."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import tempfile

from loguru import logger

from anura.config import XDG_DATA_HOME

OLD_APP_ID = "io.github.d3msudo.anura"
FLATPAK_INFO = Path("/.flatpak-info")
MIGRATION_MARKER = ".anura-legacy-flatpak-migration-v1.json"
PERSISTENT_SUBDIRECTORIES = ("history", "tessdata")


def _copy_file_without_overwrite(source: Path, destination: Path) -> bool:
    """Publish a complete copy atomically, never replacing an existing file."""
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if destination.exists() or destination.is_symlink():
        return False

    source_stat = source.lstat()
    if not stat.S_ISREG(source_stat.st_mode):
        return False

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.migration-",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, stat.S_IMODE(source_stat.st_mode) & 0o600 or 0o600)
        try:
            # A hard link is an atomic no-replace publication on the same
            # filesystem. If another process won the race, keep its file.
            os.link(temporary, destination)
        except FileExistsError:
            return False
        return True
    finally:
        temporary.unlink(missing_ok=True)


def _copy_tree_without_overwrite(source: Path, destination: Path) -> tuple[int, list[str]]:
    """Copy regular files recursively; ignore symlinks and transient downloads."""
    copied = 0
    errors: list[str] = []
    try:
        destination.mkdir(parents=True, exist_ok=True, mode=0o700)
        with os.scandir(source) as entries:
            for entry in entries:
                src = Path(entry.path)
                dst = destination / entry.name
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        child_count, child_errors = _copy_tree_without_overwrite(src, dst)
                        copied += child_count
                        errors.extend(child_errors)
                    elif entry.is_file(follow_symlinks=False):
                        # A .tmp file may belong to a download interrupted during
                        # the old installation; it is not a completed model.
                        if src.suffix == ".tmp":
                            continue
                        copied += int(_copy_file_without_overwrite(src, dst))
                except OSError as exc:
                    errors.append(f"{src}: {exc}")
    except OSError as exc:
        errors.append(f"{source}: {exc}")
    return copied, errors


def migrate_legacy_flatpak_data(
    *,
    old_data_dir: Path | str,
    new_data_home: Path | str | None = None,
    flatpak_info: Path | str = FLATPAK_INFO,
) -> bool:
    """Migrate data from the portal-authorized old Flatpak data directory.

    old_data_dir must be the directory returned by the GTK folder chooser.
    Returns True when migration is complete (or already completed), False when
    the source is invalid or a recoverable error occurred. The source is never
    modified or deleted.
    """
    if not Path(flatpak_info).is_file():
        return False

    destination_home = Path(new_data_home if new_data_home is not None else XDG_DATA_HOME)
    marker = destination_home / MIGRATION_MARKER
    if marker.is_file():
        return True

    source_home = Path(old_data_dir)
    source_app_data = source_home / "anura"
    if not source_app_data.is_dir():
        logger.info("Legacy Flatpak data directory not found; migration will be checked again on next launch.")
        return False

    total_copied = 0
    errors: list[str] = []
    for subdirectory in PERSISTENT_SUBDIRECTORIES:
        source = source_app_data / subdirectory
        if not source.exists():
            continue
        if source.is_symlink() or not source.is_dir():
            errors.append(f"{source}: expected a real directory")
            continue
        copied, copy_errors = _copy_tree_without_overwrite(
            source,
            destination_home / "anura" / subdirectory,
        )
        total_copied += copied
        errors.extend(copy_errors)

    if errors:
        for error in errors:
            logger.error(f"Legacy Flatpak data migration: {error}")
        logger.warning("Legacy Flatpak data migration incomplete; it will be retried on next launch.")
        return False

    destination_home.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker_payload = {
        "version": 1,
        "source_app_id": OLD_APP_ID,
        "copied_files": total_copied,
        "completed": True,
    }
    fd, temporary_name = tempfile.mkstemp(
        prefix=".anura-migration-marker-",
        suffix=".tmp",
        dir=destination_home,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as marker_file:
            json.dump(marker_payload, marker_file, sort_keys=True)
            marker_file.write("\n")
            marker_file.flush()
            os.fsync(marker_file.fileno())
        os.replace(temporary, marker)
    finally:
        temporary.unlink(missing_ok=True)

    logger.info(f"Legacy Flatpak data migration completed; {total_copied} file(s) copied.")
    return True
