# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Headless regression tests for the Model Quality selector (VM bug #2).

Selecting a different Tesseract model quality must invalidate the
LanguageManager cache *before* the installed-language list is reloaded.
CacheManager only rescans its directory when its cache is invalidated
(download/remove did that, the quality switch did not), so without this the
list keeps showing the scan of the previously selected quality.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock


def _make_page(monkeypatch):
    """Import the page lazily and wire a fake LanguageManager."""
    import anura.widgets.preferences_languages_page as page_mod

    manager = MagicMock()
    monkeypatch.setattr(page_mod, "get_language_manager", lambda: manager)
    fake_self = SimpleNamespace(settings=MagicMock(), load_languages=MagicMock())
    return page_mod, manager, fake_self


def test_quality_change_invalidates_cache_before_reload(monkeypatch, headless_gi_mocks):
    """The cache must be invalidated, then the list reloaded, in that order."""
    page_mod, manager, fake_self = _make_page(monkeypatch)

    order: list[str] = []
    manager.invalidate_cache.side_effect = lambda: order.append("invalidate")
    fake_self.load_languages.side_effect = lambda: order.append("reload")

    combo = MagicMock()
    combo.get_selected.return_value = 2  # 0=Fast, 1=Standard, 2=Best

    page_mod.PreferencesLanguagesPage._on_model_quality_changed(fake_self, combo, None)

    fake_self.settings.set_string.assert_called_once_with("tessdata-model", "best")
    manager.invalidate_cache.assert_called_once()
    fake_self.load_languages.assert_called_once()
    assert order == ["invalidate", "reload"]


def test_quality_change_maps_every_index(monkeypatch, headless_gi_mocks):
    """Every combo index maps to the expected tessdata-model value."""
    page_mod, _manager, fake_self = _make_page(monkeypatch)
    handler = page_mod.PreferencesLanguagesPage._on_model_quality_changed

    for index, expected in ((0, "fast"), (1, "standard"), (2, "best")):
        fake_self.settings.reset_mock()
        combo = MagicMock()
        combo.get_selected.return_value = index

        handler(fake_self, combo, None)

        fake_self.settings.set_string.assert_called_once_with("tessdata-model", expected)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
