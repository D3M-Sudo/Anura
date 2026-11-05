from __future__ import annotations

import json
from pathlib import Path

from anura.services.legacy_flatpak_migration import (
    MIGRATION_MARKER,
    migrate_legacy_flatpak_data,
)


def _layout(tmp_path: Path):
    old = tmp_path / "old-app" / "data"
    new = tmp_path / "new-app" / "data"
    flatpak_info = tmp_path / ".flatpak-info"
    flatpak_info.write_text("[Application]\nname=io.github.d3m_sudo.anura\n", encoding="utf-8")
    return old, new, flatpak_info


def test_migrates_history_and_all_model_profiles(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    (old / "anura/history").mkdir(parents=True)
    (old / "anura/history/history.json").write_text('[{"text":"old"}]', encoding="utf-8")
    (old / "anura/history/history.json.corrupt-1").write_text("damaged", encoding="utf-8")
    for profile in ("tessdata", "tessdata_fast", "tessdata_best"):
        directory = old / "anura/tessdata" / profile
        directory.mkdir(parents=True)
        (directory / "ita.traineddata").write_bytes(profile.encode())

    assert migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)

    assert (new / "anura/history/history.json").read_text(encoding="utf-8") == '[{"text":"old"}]'
    assert (new / "anura/history/history.json.corrupt-1").read_text(encoding="utf-8") == "damaged"
    for profile in ("tessdata", "tessdata_fast", "tessdata_best"):
        assert (new / "anura/tessdata" / profile / "ita.traineddata").read_bytes() == profile.encode()
    assert (old / "anura/history/history.json").exists()
    marker = json.loads((new / MIGRATION_MARKER).read_text(encoding="utf-8"))
    assert marker["completed"] is True
    assert marker["copied_files"] == 5


def test_does_not_overwrite_existing_destination_files(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    source = old / "anura/history/history.json"
    source.parent.mkdir(parents=True)
    source.write_text("legacy", encoding="utf-8")
    destination = new / "anura/history/history.json"
    destination.parent.mkdir(parents=True)
    destination.write_text("new-install", encoding="utf-8")

    assert migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    assert destination.read_text(encoding="utf-8") == "new-install"
    assert source.read_text(encoding="utf-8") == "legacy"


def test_is_idempotent_and_marker_prevents_second_copy(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    source = old / "anura/history/history.json"
    source.parent.mkdir(parents=True)
    source.write_text("legacy", encoding="utf-8")

    assert migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    destination = new / "anura/history/history.json"
    destination.write_text("user-edited", encoding="utf-8")
    assert migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    assert destination.read_text(encoding="utf-8") == "user-edited"


def test_skips_symlinks_and_temporary_downloads(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    source_dir = old / "anura/tessdata/tessdata_fast"
    source_dir.mkdir(parents=True)
    (source_dir / "ita.traineddata").write_bytes(b"model")
    (source_dir / "unfinished.traineddata.tmp").write_bytes(b"partial")
    outside = tmp_path / "outside"
    outside.write_text("do not copy", encoding="utf-8")
    (source_dir / "linked.traineddata").symlink_to(outside)

    assert migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    target = new / "anura/tessdata/tessdata_fast"
    assert (target / "ita.traineddata").read_bytes() == b"model"
    assert not (target / "unfinished.traineddata.tmp").exists()
    assert not (target / "linked.traineddata").exists()


def test_does_not_run_outside_flatpak(tmp_path):
    old, new, _ = _layout(tmp_path)
    source = old / "anura/history/history.json"
    source.parent.mkdir(parents=True)
    source.write_text("legacy", encoding="utf-8")

    assert not migrate_legacy_flatpak_data(
        old_data_dir=old, new_data_home=new, flatpak_info=tmp_path / "missing-flatpak-info"
    )
    assert not (new / MIGRATION_MARKER).exists()


def test_missing_legacy_directory_is_not_marked_complete(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    assert not migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    assert not (new / MIGRATION_MARKER).exists()



def test_rejects_a_selected_directory_without_legacy_data(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    (old / "anura").mkdir(parents=True)

    assert not migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    assert not (new / MIGRATION_MARKER).exists()


def test_rejects_symlinked_source_root(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    real_source = tmp_path / "real-source"
    (real_source / "anura/history").mkdir(parents=True)
    (real_source / "anura/history/history.json").write_text("legacy", encoding="utf-8")
    old.symlink_to(real_source, target_is_directory=True)

    assert not migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    assert not (new / MIGRATION_MARKER).exists()


def test_rejects_symlinked_destination_tree(tmp_path):
    old, new, flatpak_info = _layout(tmp_path)
    source = old / "anura/history/history.json"
    source.parent.mkdir(parents=True)
    source.write_text("legacy", encoding="utf-8")

    outside = tmp_path / "outside"
    outside.mkdir()
    (new / "anura").parent.mkdir(parents=True, exist_ok=True)
    (new / "anura").symlink_to(outside, target_is_directory=True)

    assert not migrate_legacy_flatpak_data(old_data_dir=old, new_data_home=new, flatpak_info=flatpak_info)
    assert not (outside / "history/history.json").exists()
    assert not (new / MIGRATION_MARKER).exists()
