"""
Tag Analyzer - Vault 태그 분석 및 집계 모듈

Vault 전체 .md 파일의 frontmatter tags 필드를 파싱하여
태그별 문서 수를 집계하고 계층적 태그 구조를 분석합니다.
"""

import re
import logging
from pathlib import Path
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


@dataclass
class TagStats:
    """Tag analysis result"""
    tag: str
    count: int
    children: Dict[str, 'TagStats'] = field(default_factory=dict)

    @property
    def depth(self) -> int:
        return self.tag.count('/') + 1


@dataclass
class TagAnalysisResult:
    """Overall tag analysis result"""
    total_documents: int
    tagged_documents: int
    untagged_documents: int
    tag_counts: Dict[str, int]  # flat tag -> count
    top_level_tags: Dict[str, TagStats]  # hierarchical tree
    untagged_files: List[str]


class TagAnalyzer:
    """Vault frontmatter tag analyzer"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)

    def analyze(self, min_count: int = 1, depth: int = 0) -> TagAnalysisResult:
        """Analyze all tags in the vault.

        Args:
            min_count: Minimum document count to include a tag.
            depth: Max hierarchy depth to display (0 = all).

        Returns:
            TagAnalysisResult with aggregated tag statistics.
        """
        tag_counter: Counter = Counter()
        total_docs = 0
        tagged_docs = 0
        untagged_files: List[str] = []

        for md_file in sorted(self.vault_path.rglob("*.md")):
            # Skip hidden directories and common non-content dirs
            parts = md_file.relative_to(self.vault_path).parts
            if any(p.startswith('.') for p in parts):
                continue

            total_docs += 1
            tags = self._extract_tags_from_file(md_file)

            if tags:
                tagged_docs += 1
                tag_counter.update(tags)
            else:
                rel_path = str(md_file.relative_to(self.vault_path))
                untagged_files.append(rel_path)

        # Filter by min_count
        filtered_counts = {
            tag: count for tag, count in tag_counter.items()
            if count >= min_count
        }

        # Build hierarchical tree
        tree = self._build_tag_tree(filtered_counts, depth)

        return TagAnalysisResult(
            total_documents=total_docs,
            tagged_documents=tagged_docs,
            untagged_documents=total_docs - tagged_docs,
            tag_counts=filtered_counts,
            top_level_tags=tree,
            untagged_files=untagged_files,
        )

    def _extract_tags_from_file(self, file_path: Path) -> List[str]:
        """Extract tags from a single markdown file's frontmatter."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return []

        frontmatter = self._parse_frontmatter(content)
        if not frontmatter or 'tags' not in frontmatter:
            return []

        fm_tags = frontmatter['tags']
        if isinstance(fm_tags, list):
            return [str(t).strip() for t in fm_tags if t]
        elif isinstance(fm_tags, str):
            return [fm_tags.strip()] if fm_tags.strip() else []
        return []

    def _parse_frontmatter(self, content: str) -> Optional[Dict]:
        """Parse YAML frontmatter from markdown content."""
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return None
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return None

    def _build_tag_tree(
        self, tag_counts: Dict[str, int], max_depth: int
    ) -> Dict[str, TagStats]:
        """Build hierarchical tag tree from flat tag counts.

        Tags like 'tdd/philosophy' are nested under 'tdd'.
        """
        tree: Dict[str, TagStats] = {}

        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
            parts = tag.split('/')

            # Apply depth filter
            if max_depth > 0 and len(parts) > max_depth:
                continue

            if len(parts) == 1:
                # Top-level tag
                if tag not in tree:
                    tree[tag] = TagStats(tag=tag, count=count)
                else:
                    tree[tag].count = count
            else:
                # Hierarchical tag: ensure parent exists
                root = parts[0]
                if root not in tree:
                    # Parent may not have its own count
                    tree[root] = TagStats(
                        tag=root, count=tag_counts.get(root, 0)
                    )
                tree[root].children[tag] = TagStats(tag=tag, count=count)

        return tree

    def format_table(
        self, result: TagAnalysisResult, depth: int = 0
    ) -> str:
        """Format analysis result as a human-readable table."""
        lines = []
        lines.append(f"{'Tag':<40} {'Documents':>10}")
        lines.append("─" * 52)

        # Sort by count descending
        sorted_tags = sorted(
            result.top_level_tags.values(),
            key=lambda t: t.count,
            reverse=True
        )

        for tag_stat in sorted_tags:
            lines.append(f"{tag_stat.tag:<40} {tag_stat.count:>10}")

            if tag_stat.children and (depth == 0 or depth >= 2):
                sorted_children = sorted(
                    tag_stat.children.values(),
                    key=lambda t: t.count,
                    reverse=True
                )
                for child in sorted_children:
                    lines.append(f"  {child.tag:<38} {child.count:>10}")

        lines.append("─" * 52)
        top_count = len(result.top_level_tags)
        lines.append(
            f"Total: {top_count} top-level tags, "
            f"{result.total_documents} documents "
            f"({result.tagged_documents} tagged, "
            f"{result.untagged_documents} untagged)"
        )

        return "\n".join(lines)

    def format_markdown(self, result: TagAnalysisResult) -> str:
        """Format analysis result as markdown."""
        lines = ["# Vault Tag Analysis", ""]
        lines.append(f"- Total documents: {result.total_documents}")
        lines.append(f"- Tagged: {result.tagged_documents}")
        lines.append(f"- Untagged: {result.untagged_documents}")
        lines.append("")
        lines.append("## Tags")
        lines.append("")
        lines.append("| Tag | Documents |")
        lines.append("|-----|-----------|")

        sorted_tags = sorted(
            result.top_level_tags.values(),
            key=lambda t: t.count,
            reverse=True
        )

        for tag_stat in sorted_tags:
            lines.append(f"| {tag_stat.tag} | {tag_stat.count} |")
            for child in sorted(
                tag_stat.children.values(),
                key=lambda t: t.count,
                reverse=True
            ):
                lines.append(f"| &nbsp;&nbsp;{child.tag} | {child.count} |")

        if result.untagged_files:
            lines.append("")
            lines.append(f"## Untagged Documents ({len(result.untagged_files)})")
            lines.append("")
            for f in result.untagged_files[:50]:
                lines.append(f"- {f}")
            if len(result.untagged_files) > 50:
                lines.append(
                    f"- ... and {len(result.untagged_files) - 50} more"
                )

        return "\n".join(lines)
