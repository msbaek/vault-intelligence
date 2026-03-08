"""Obsidian wikilink parser for knowledge graph."""

import re
from pathlib import Path

WIKILINK_RE = re.compile(r'\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*?)?\]\]')


class WikilinkParser:
    """Extract and resolve Obsidian wikilinks from markdown files."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)

    def extract_from_content(self, content: str) -> list[str]:
        """Extract wikilink targets from markdown content."""
        return list(dict.fromkeys(m.group(1).strip() for m in WIKILINK_RE.finditer(content)))

    def extract_from_file(self, file_path: str) -> list[str]:
        """Extract wikilinks from a file."""
        try:
            full = self.vault_path / file_path
            content = full.read_text(encoding='utf-8')
            return self.extract_from_content(content)
        except (OSError, UnicodeDecodeError):
            return []

    def resolve_link(self, link_name: str) -> str | None:
        """Resolve a wikilink name to a vault-relative file path."""
        # Exact match first
        for md in self.vault_path.rglob(f"{link_name}.md"):
            return str(md.relative_to(self.vault_path))
        # Case-insensitive fallback
        lower = link_name.lower()
        for md in self.vault_path.rglob("*.md"):
            if md.stem.lower() == lower:
                return str(md.relative_to(self.vault_path))
        return None
