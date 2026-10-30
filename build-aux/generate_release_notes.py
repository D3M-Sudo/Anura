#!/usr/bin/env python3
"""Generate _release_notes.py from CHANGELOG.md during build."""

import html
from pathlib import Path
import re
import sys


def parse_changelog(changelog_path: Path) -> dict:
    """Parse CHANGELOG.md and return a dict of version -> html notes."""
    try:
        content = changelog_path.read_text()
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"Error reading changelog file {changelog_path}: {e}", file=sys.stderr)
        return {}

    # Pattern to match version sections (supports 3 or 4 component versions like 0.1.4 or 0.1.4.1)
    # Content uses ".*?" with DOTALL so it can include sub-sections like "### Added"
    # whose lines start with "#"; the lookahead anchors the section end at the next
    # version header (or end of file) instead of stopping at the first "#".
    # Also handles optional {version-x.y.z} suffix at end of version line
    version_pattern = (
        r"^## \[(?P<version>\d{1,4}\.\d{1,4}\.\d{1,4}(?:\.\d{1,4})?)\] - "
        r"(?P<date>\d{4}-\d{2}-\d{2})(?:\s+\{version-[^}]+\})?\n+"
        r"(?P<content>.*?)(?=^## \[|\Z)"
    )

    releases = {}

    for match in re.finditer(version_pattern, content, re.MULTILINE | re.DOTALL):
        version = match.group("version")
        section_content = match.group("content")

        # Parse subsections (### Added, ### Fixed, etc.)
        sections = {}
        current_section = "Changes"

        for line in section_content.strip().split("\n"):
            line = line.strip()
            if line.startswith("### "):
                # New section header
                current_section = line[4:].strip()
                sections.setdefault(current_section, [])
            elif line.startswith("- "):
                # Remove the leading "- " first
                item_text = line[2:]
                # Escape HTML FIRST to prevent injection from markdown links [text](url)
                item_text = html.escape(item_text)
                # Then remove markdown syntax (now safe from HTML injection)
                item_text = (
                    item_text.replace("**", "").replace("__", "").replace("*", "").replace("_", "").replace("`", "")
                )
                sections.setdefault(current_section, []).append(item_text)

        if sections:
            # Build HTML with sections
            html_parts = []
            total_items = 0

            for section_name, items in sections.items():
                if items:
                    # Limit to 5 items per section
                    limited_items = items[:5]
                    total_items += len(limited_items)

                    html_parts.append(f"<p><em>{html.escape(section_name)}</em></p>")
                    html_items = "".join(f"<li>{item}</li>" for item in limited_items)
                    html_parts.append(f"<ul>{html_items}</ul>")

            # NOTE: Adw.AboutDialog's release notes use a restricted markup that
            # does not support <a> tags with 'href'.
            # Link is now handled via official add_link() in on_about().

            html_output = "".join(html_parts)
        else:
            html_output = "<p>No changes listed.</p>"
        releases[version] = html_output

    return releases


def markdown_release_notes(changelog_path: Path, version: str, date: str) -> str:
    """Return the GitHub release body for *version*, taken from CHANGELOG.md.

    The section is copied verbatim (headings and bullets), so the published
    release and the changelog cannot disagree (#489).
    """
    content = changelog_path.read_text(encoding="utf-8")
    pattern = (
        r"^## \[" + re.escape(version) + r"\] - \d{4}-\d{2}-\d{2}\n"
        r"(?P<content>.*?)(?=^## \[|\Z)"
    )
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    body = match.group("content").strip() if match else ""

    if not body:
        sys.exit(f"CHANGELOG.md has no [{version}] section: the release body would be empty")

    return f"## Anura v{version} — {date}\n\n{body}\n"


def _metainfo_sections(changelog_path: Path, version: str) -> dict[str, list[str]]:
    """Return the ``### Section -> [items]`` map of one CHANGELOG version.

    Unlike :func:`parse_changelog`, this keeps snake_case identifiers (the HTML
    variant strips every underscore, turning ``test_x.py`` into ``testx.py``).
    """
    content = changelog_path.read_text(encoding="utf-8")
    pattern = (
        r"^## \[" + re.escape(version) + r"\] - \d{4}-\d{2}-\d{2}\n"
        r"(?P<content>.*?)(?=^## \[|\Z)"
    )
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match is None:
        return {}

    sections: dict[str, list[str]] = {}
    current = "Changes"
    for raw_line in match.group("content").strip().splitlines():
        line = raw_line.strip()
        if line.startswith("### "):
            current = line[4:].strip()
            sections.setdefault(current, [])
        elif line.startswith("- "):
            item = html.escape(line[2:].replace("**", "").replace("`", ""))
            sections.setdefault(current, []).append(item)
    return {name: items for name, items in sections.items() if items}


def metainfo_release_entry(changelog_path: Path, version: str, date: str) -> str:
    """Return the AppStream <release> block for *version* from CHANGELOG.md.

    Fails instead of writing a placeholder: a release must never publish
    "TODO" or a bare "Release x.y.z." description (#485).
    """
    sections = _metainfo_sections(changelog_path, version)
    if not sections:
        sys.exit(f"CHANGELOG.md has no [{version}] section with entries: add the release notes before releasing")

    lines = [f'    <release version="{version}" type="stable" date="{date}">', "      <description>"]
    for name, items in sections.items():
        lines.append(f"        <p><em>{html.escape(name)}</em></p>")
        lines.append("        <ul>")
        lines.extend(f"          <li>{item}</li>" for item in items[:5])
        lines.append("        </ul>")
    lines.extend(["      </description>", "    </release>"])
    return "\n".join(lines)


def generate_release_notes_py(changelog_path: Path, output_path: Path, current_version: str) -> None:
    """Generate the _release_notes.py file."""
    releases = parse_changelog(changelog_path)

    current_notes = releases.get(current_version, "Bug fixes and improvements.")

    # Build the Python file content
    lines = [
        "# Auto-generated file. Do not edit manually.",
        "# Generated from CHANGELOG.md during build.",
        "",
        "RELEASE_NOTES = {",
    ]

    for version, html_content in releases.items():
        # Use repr() to safely escape the content and avoid triple-quote issues
        lines.append(f'    "{version}": {html_content!r},')

    lines.extend(
        [
            "}",
            "",
            f'CURRENT_VERSION = "{current_version}"',
            "",
            # Use repr() to safely escape current_notes
            f"CURRENT_NOTES = {current_notes!r}",
            "",
            "def get_release_notes(version: str = None) -> str:",
            '    """Get release notes for a specific version or current version."""',
            "    if version is None:",
            "        return CURRENT_NOTES",
            '    return RELEASE_NOTES.get(version, "Bug fixes and improvements.")',
            "",
        ]
    )

    try:
        output_path.write_text("\n".join(lines))
    except (PermissionError, OSError) as e:
        print(f"Error writing output file {output_path}: {e}", file=sys.stderr)
        sys.exit(1)


def validate_version(version: str) -> bool:
    """Validate version string format (e.g., '0.1.4' or '0.1.4.1')."""
    return bool(re.match(r"^[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?$", version))


if __name__ == "__main__":
    arguments = sys.argv[1:]

    # Release helper: print the AppStream entry for the version being released.
    #   generate_release_notes.py --metainfo <changelog.md> <version> <date>
    if arguments and arguments[0] == "--markdown":
        if len(arguments) != 4:
            print(
                f"Usage: {sys.argv[0]} --markdown <changelog.md> <version> <YYYY-MM-DD>",
                file=sys.stderr,
            )
            sys.exit(1)
        changelog, version, date = Path(arguments[1]), arguments[2], arguments[3]
        if not validate_version(version):
            sys.exit(f"Error: Invalid version format: {version}")
        print(markdown_release_notes(changelog, version, date))
        sys.exit(0)

    if arguments and arguments[0] == "--metainfo":
        if len(arguments) != 4:
            print(
                f"Usage: {sys.argv[0]} --metainfo <changelog.md> <version> <YYYY-MM-DD>",
                file=sys.stderr,
            )
            sys.exit(1)
        changelog, version, date = Path(arguments[1]), arguments[2], arguments[3]
        if not validate_version(version):
            sys.exit(f"Error: Invalid version format: {version}")
        print(metainfo_release_entry(changelog, version, date))
        sys.exit(0)

    if len(arguments) != 3:
        print(f"Usage: {sys.argv[0]} <changelog.md> <output.py> <version>", file=sys.stderr)
        sys.exit(1)

    changelog = Path(arguments[0])
    output = Path(arguments[1])
    version = arguments[2]

    if not validate_version(version):
        print(f"Error: Invalid version format: {version}", file=sys.stderr)
        print("Expected format: MAJOR.MINOR.PATCH[.PATCH2] (e.g., 0.1.4 or 0.1.4.1)", file=sys.stderr)
        sys.exit(1)

    generate_release_notes_py(changelog, output, version)
    print(f"Generated {output} with release notes for version {version}")
