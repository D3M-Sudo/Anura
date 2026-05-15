import os
import re

# Pattern to find strings in common widgets NOT using _() or C_() or ngettext()
patterns = [
    # Gtk Template child properties
    r'label\s*[:=]\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    r'tooltip-text\s*[:=]\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    r'tooltip_text\s*[:=]\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    r'title\s*[:=]\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    r'description\s*[:=]\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    # Common GTK/Libadwaita methods
    r'set_title\s*\(\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    r'set_label\s*\(\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    r'set_text\s*\(\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    r'set_heading\s*\(\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    r'set_body\s*\(\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    r'add_response\s*\(\s*"[^"]+"\s*,\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    # App specific methods
    r'show_toast\s*\(\s*"(?!_\(|C_\(|ngettext\()([^"]+)"\)',
    r'show_notification\s*\(\s*[^)]*title\s*=\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    r'show_notification\s*\(\s*[^)]*body\s*=\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
    # Blueprint specific (title: "Text", etc)
    r'\b(title|label|description|tooltip-text|button-label)\s*:\s*"(?!_\(|C_\(|ngettext\()([^"]+)"',
]


def check_i18n(directory):
    found_issues = False
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".blp"):
                path = os.path.join(root, file)
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        # Skip comments
                        if line.strip().startswith("#") or line.strip().startswith("//"):
                            continue
                        for pattern in patterns:
                            match = re.search(pattern, line)
                            if match:
                                # For some patterns we want the second group if it exists
                                val = match.group(2) if len(match.groups()) > 1 and match.group(2) else match.group(1)
                                if (
                                    val
                                    and not val.startswith("/")
                                    and not val.startswith("com.github")
                                    and not val.endswith(".ui")
                                ):
                                    print(f"[!] Unmapped string in {path} (line {i}): {line.strip()}")
                                    found_issues = True
    return found_issues


if __name__ == "__main__":
    print("Checking 'anura' directory...")
    issues_anura = check_i18n("anura")
    print("\nChecking 'data/ui' directory...")
    issues_ui = check_i18n("data/ui")

    if not issues_anura and not issues_ui:
        print("\n[OK] All detected strings are correctly wrapped in _().")
    else:
        print("\n[ERROR] Some strings are still hardcoded. Please fix them.")
