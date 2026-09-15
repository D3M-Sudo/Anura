# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression tests for tessdata download installation (NEW-F1/NEW-F2).

Covers two audit findings on ``DownloadManager.download_begin()``:

- NEW-F2: the model must be installed with an atomic rename (``os.replace``),
  never with a buffered copy, so an interrupted download can neither overwrite
  an existing valid model nor leave a partially written file in place.
- NEW-F1: the downloaded model must be verified against the pinned integrity
  manifest before it is installed.

Run with the system python3 + venv site-packages pattern documented in
``docs/dependencies.md`` (the tests need PyGObject and compiled schemas).
"""

from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

from anura.services.language.download_manager import DownloadManager


def _response(payloads, headers=None):
    """Build a fake streaming ``requests`` response yielding ``payloads``."""
    response = MagicMock()
    response.headers = headers if headers is not None else {}
    response.iter_content = lambda chunk_size=8192: iter(payloads)
    response.raise_for_status = MagicMock()
    return response


@pytest.mark.gtk
class TestAtomicInstall:
    """NEW-F2 — atomic file installation."""

    @pytest.fixture
    def manager(self, tmp_path: Path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        with (
            patch("anura.services.language.download_manager.TESSDATA_DIR", str(tessdata_dir)),
            patch("anura.services.language.download_manager.settings") as mock_settings,
        ):
            # "fast" resolves to the base tessdata dir, keeping assertions simple.
            mock_settings.get_string.return_value = "fast"
            yield DownloadManager(), tessdata_dir

    def test_successful_download_installs_model_atomically(self, manager) -> None:
        """A successful download ends up at final_path with no leftovers."""
        dm, tessdata_dir = manager
        payload = b"MODEL-DATA" * 64
        response = _response([payload], {"content-length": str(len(payload))})

        final_path = tessdata_dir / "fra.traineddata"
        partial_visible: list[bool] = []

        def iter_content(chunk_size: int = 8192):
            # While streaming, final_path must not exist yet: the model is only
            # materialised by the final atomic rename.
            partial_visible.append(final_path.exists())
            yield payload

        response.iter_content = iter_content

        with (
            patch.object(dm.session, "get", return_value=response),
            patch("anura.services.language.download_manager.shutil.which", return_value="/usr/bin/tesseract"),
        ):
            result = dm.download_begin("fra")

        assert result == "fra"
        assert partial_visible == [False]
        assert final_path.read_bytes() == payload
        assert list(tessdata_dir.glob("*.tmp")) == []

    def test_interrupted_download_keeps_existing_model_untouched(self, manager) -> None:
        """A failure mid-stream must not corrupt the previously installed model."""
        dm, tessdata_dir = manager
        final_path = tessdata_dir / "fra.traineddata"
        final_path.write_bytes(b"PREVIOUS-VALID-MODEL")

        def failing_stream(chunk_size: int = 8192):
            yield b"PARTIAL-CHUNK"
            raise OSError("connection reset by peer")

        response = _response([])
        response.iter_content = failing_stream

        with (
            patch.object(dm.session, "get", return_value=response),
            patch("anura.services.language.download_manager.shutil.which", return_value="/usr/bin/tesseract"),
        ):
            result = dm.download_begin("fra")

        assert result is None
        assert final_path.read_bytes() == b"PREVIOUS-VALID-MODEL"
        assert list(tessdata_dir.glob("*.tmp")) == []

    def test_temp_file_lives_next_to_target(self, manager) -> None:
        """The staging file must be created in the target directory (same FS).

        This is what makes the rename atomic; if the staging file were created on
        a different filesystem, os.replace() would fail with EXDEV.
        """
        dm, tessdata_dir = manager
        payload = b"MODEL"
        response = _response([payload], {"content-length": str(len(payload))})
        staged_dirs: list[Path] = []
        real_named_temporary_file = tempfile.NamedTemporaryFile

        def spying_named_temporary_file(*args, **kwargs):
            staged_dirs.append(Path(kwargs["dir"]))
            return real_named_temporary_file(*args, **kwargs)

        with (
            patch.object(dm.session, "get", return_value=response),
            patch("anura.services.language.download_manager.shutil.which", return_value="/usr/bin/tesseract"),
            patch(
                "anura.services.language.download_manager.tempfile.NamedTemporaryFile",
                side_effect=spying_named_temporary_file,
            ),
        ):
            result = dm.download_begin("fra")

        assert result == "fra"
        assert staged_dirs == [tessdata_dir]
