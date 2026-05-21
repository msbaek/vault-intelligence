"""OFM (Obsidian Flavored Markdown) utilities for vis output.

SSOT: ~/.claude/commands/obsidian/ofm-rules.md
Wikilink rule: vault-relative path, no .md extension → [[folder/basename]]
Frontmatter timestamp rule: YYYY-MM-DD HH:MM (plain text, NOT wikilink).

Scope: only wikilink and frontmatter timestamp — what vis actually emits.
callout/embed helpers are NOT here (YAGNI).
"""

from datetime import datetime
from pathlib import Path


def to_wikilink(path: str, vault_path: str, alias: str = None) -> str:
    """Convert a file path to an Obsidian vault-relative wikilink.

    SSOT: ~/.claude/commands/obsidian/ofm-rules.md §1-Wikilink
    Input: absolute path or vault-relative path (with or without .md).
    Output: [[folder/basename]] or [[folder/basename|alias]].
    """
    p = Path(path)
    vault = Path(vault_path)

    # Strip vault root prefix if absolute path given
    try:
        rel = p.relative_to(vault)
    except ValueError:
        rel = p  # already relative — use as-is

    # Build wikilink path: strip .md suffix from final component
    parts = rel.parts
    stem = Path(parts[-1]).stem  # removes .md (or any extension)
    wikilink_path = "/".join(list(parts[:-1]) + [stem])

    if alias:
        return f"[[{wikilink_path}|{alias}]]"
    return f"[[{wikilink_path}]]"


def format_frontmatter_timestamp(dt: datetime = None) -> str:
    """Return a frontmatter-safe timestamp string.

    SSOT: ~/.claude/commands/obsidian/ofm-rules.md §2-Frontmatter
    Format: YYYY-MM-DD HH:MM  (plain text, NOT [[wikilink]]).
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M")
