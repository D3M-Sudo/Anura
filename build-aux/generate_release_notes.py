#!/usr/bin/env python3
"""Generate _release_notes.py from CHANGELOG.md during build."""

import html
import re
import sys
from pathlib import Path


def parse_changelog(changelog_path: Path) -> dict:
    """Parse CHANGELOG.md and return a dict of version -> html notes."""
    content = changelog_path.read_text()

    # Pattern to match version sections (supports 3 or 4 component versions like 0.1.4 or 0.1.4.1)
    # Uses atomic-like grouping and limited repetition to prevent catastrophic backtracking
    version_pattern = (
        r'^## \[(?P<version>\d{1,4}\.\d{1,4}\.\d{1,4}(?:\.\d{1,4})?)\] - (?P<date>\d{4}-\d{2}-\d{2})\n+'
        r'(?P<content>[^#]*?)(?=^## \[|\Z)'
    )

    releases = {}

    for match in re.finditer(version_pattern, content, re.MULTILINE | re.DOTALL):
        version = match.group('version')
        section_content = match.group('content')

        # Parse subsections (### Added, ### Fixed, etc.)
        sections = {}
        current_section = "Changes"

        for line in section_content.strip().split('\n'):
            line = line.strip()
            if line.startswith('### '):
                # New section header
                current_section = line[4:].strip()
                sections.setdefault(current_section, [])
            elif line.startswith('- '):
                # Remove the leading "- " first
                item_text = line[2:]
                # Escape HTML FIRST to prevent injection from markdown links [text](url)
                item_text = html.escape(item_text)
                # Then remove markdown syntax (now safe from HTML injection)
                item_text = (item_text
                    .replace('**', '')
                    .replace('__', '')
                    .replace('*', '')
                    .replace('_', '')
                    .replace('`', ''))
                sections.setdefault(current_section, []).append(item_text)

        if sections:
            # Build HTML with sections
            html_parts = []
            for section_name, items in sections.items():
                if items:
                    html_parts.append(f'<b>{html.escape(section_name)}</b>')
                    html_items = ''.join(f'<li>{item}</li>' for item in items)
                    html_parts.append(f'<ul>{html_items}</ul>')
            html_output = ''.join(html_parts)
        else:
            html_output = '<p>No changes listed.</p>'
        releases[version] = html_output

    return releases


def generate_release_notes_py(changelog_path: Path, output_path: Path, current_version: str):
    """Generate the _release_notes.py file."""
    releases = parse_changelog(changelog_path)

    current_notes = releases.get(current_version, 'Bug fixes and improvements.')

    # Build the Python file content
    lines = [
        '# Auto-generated file. Do not edit manually.',
        '# Generated from CHANGELOG.md during build.',
        '',
        'RELEASE_NOTES = {',
    ]

    for version, html_content in releases.items():
        # Use repr() to safely escape the content and avoid triple-quote issues
        lines.append(f'    "{version}": {repr(html_content)},')

    lines.extend([
        '}',
        '',
        f'CURRENT_VERSION = "{current_version}"',
        '',
        # Use repr() to safely escape current_notes
        f'CURRENT_NOTES = {repr(current_notes)}',
        '',
        'def get_release_notes(version: str = None) -> str:',
        '    """Get release notes for a specific version or current version."""',
        '    if version is None:',
        '        return CURRENT_NOTES',
        '    return RELEASE_NOTES.get(version, "Bug fixes and improvements.")',
        '',
    ])

    output_path.write_text('\n'.join(lines))


def validate_version(version: str) -> bool:
    """Validate version string format (e.g., '0.1.4' or '0.1.4.1')."""
    return bool(re.match(r'^[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?$', version))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f'Usage: {sys.argv[0]} <changelog.md> <output.py> <version>', file=sys.stderr)
        sys.exit(1)

    changelog = Path(sys.argv[1])
    output = Path(sys.argv[2])
    version = sys.argv[3]

    if not validate_version(version):
        print(f'Error: Invalid version format: {version}', file=sys.stderr)
        print('Expected format: MAJOR.MINOR.PATCH[.PATCH2] (e.g., 0.1.4 or 0.1.4.1)', file=sys.stderr)
        sys.exit(1)

    generate_release_notes_py(changelog, output, version)
    print(f'Generated {output} with release notes for version {version}')
