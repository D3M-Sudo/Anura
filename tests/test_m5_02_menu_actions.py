# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_blueprint_menu_and_widget_actions_resolve_to_registered_scopes():
    """Every app./win. action referenced by the shipped page Blueprints is registered."""
    app_registry = (ROOT / "anura/core/action_registry.py").read_text(encoding="utf-8")
    window_source = (ROOT / "anura/window.py").read_text(encoding="utf-8")
    app_actions = set(re.findall(r'_create_action\("([^"]+)"', app_registry))
    window_actions = set(re.findall(r'Gio\.SimpleAction\.new\("([^"]+)"', window_source))

    blueprint_paths = (
        ROOT / "data/ui/welcome_page.blp",
        ROOT / "data/ui/extracted_page.blp",
    )
    references = {}
    for path in blueprint_paths:
        content = path.read_text(encoding="utf-8")
        for action in re.findall(r'\baction(?:-name)?:\s*"(app|win)\.([^"]+)"', content):
            references.setdefault(action[0], set()).add(action[1])

    assert references.get("app"), "No app-scoped actions were found in page Blueprints"
    assert references.get("win"), "No window-scoped actions were found in page Blueprints"
    assert references["app"] <= app_actions, (
        f"Unregistered app actions: {sorted(references['app'] - app_actions)}"
    )
    assert references["win"] <= window_actions, (
        f"Unregistered window actions: {sorted(references['win'] - window_actions)}"
    )
