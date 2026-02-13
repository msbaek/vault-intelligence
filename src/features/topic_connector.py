"""
Topic Connector - 주제별 문서 연결 오케스트레이터

주제(태그) 기반으로 MOC 생성과 관련 문서 링크 삽입을 결합하여
Obsidian graph view에서 문서 간 연결을 구축합니다.
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from src.features.tag_analyzer import TagAnalyzer
from src.features.moc_generator import MOCGenerator
from src.features.related_docs_finder import RelatedDocsFinder

logger = logging.getLogger(__name__)

PROGRESS_FILENAME = "WIP/graph-connect-progress.md"


@dataclass
class ConnectResult:
    """Result of a single topic connection run"""
    topic: str
    documents_found: int = 0
    moc_generated: bool = False
    moc_path: str = ""
    docs_with_links_added: int = 0
    docs_skipped: int = 0
    docs_failed: int = 0
    dry_run: bool = False
    errors: List[str] = field(default_factory=list)

    @property
    def total_new_links(self) -> int:
        return self.docs_with_links_added


@dataclass
class ConnectionStatus:
    """Overall graph connection status"""
    total_documents: int = 0
    tagged_documents: int = 0
    untagged_documents: int = 0
    completed_topics: List[Dict] = field(default_factory=list)
    pending_topics: List[Dict] = field(default_factory=list)
    in_progress_topics: List[Dict] = field(default_factory=list)


class TopicConnector:
    """Orchestrates per-topic MOC generation + related-doc linking."""

    def __init__(
        self,
        search_engine,
        vault_path: str,
        config: Dict = None,
    ):
        self.search_engine = search_engine
        self.vault_path = Path(vault_path)
        self.config = config or {}

        self.tag_analyzer = TagAnalyzer(vault_path)
        self.moc_generator = MOCGenerator(search_engine, config)
        self.related_finder = RelatedDocsFinder(search_engine, config)

    def connect_topic(
        self,
        topic: str,
        top_k: int = 50,
        related_k: int = 3,
        threshold: float = 0.3,
        skip_moc: bool = False,
        skip_related: bool = False,
        dry_run: bool = False,
        backup: bool = False,
    ) -> ConnectResult:
        """Connect documents for a single topic.

        Workflow:
        1. Collect documents with this tag
        2. Generate MOC (unless skip_moc)
        3. Add related doc links to each document (unless skip_related)
        4. Update progress file
        """
        result = ConnectResult(topic=topic, dry_run=dry_run)

        # 1. Collect documents with this tag
        tag_result = self.tag_analyzer.analyze(min_count=1)
        tagged_files = self._get_files_for_tag(topic)
        result.documents_found = len(tagged_files)

        if result.documents_found == 0:
            result.errors.append(f"No documents found with tag '{topic}'")
            return result

        print(f"  Found {result.documents_found} documents with tag '{topic}'")

        # 2. Generate MOC
        if not skip_moc:
            result = self._generate_moc_for_topic(
                topic, top_k, threshold, dry_run, result
            )

        # 3. Add related doc links
        if not skip_related:
            result = self._add_related_links(
                tagged_files, related_k, threshold, dry_run, backup, result
            )

        # 4. Update progress file
        if not dry_run:
            self._update_progress(result)

        return result

    def _get_files_for_tag(self, tag: str) -> List[Path]:
        """Get all vault files that have the given tag (exact or prefix match)."""
        files = []
        for md_file in sorted(self.vault_path.rglob("*.md")):
            parts = md_file.relative_to(self.vault_path).parts
            if any(p.startswith('.') for p in parts):
                continue

            tags = self.tag_analyzer._extract_tags_from_file(md_file)
            # Match exact tag or any tag that starts with topic/
            tag_lower = tag.lower()
            for t in tags:
                if t.lower() == tag_lower or t.lower().startswith(tag_lower + '/'):
                    files.append(md_file)
                    break
        return files

    def _generate_moc_for_topic(
        self,
        topic: str,
        top_k: int,
        threshold: float,
        dry_run: bool,
        result: ConnectResult,
    ) -> ConnectResult:
        """Generate MOC for the topic using existing MOCGenerator."""
        try:
            if dry_run:
                print(f"  [DRY-RUN] Would generate MOC for '{topic}'")
                result.moc_generated = True
                return result

            print(f"  Generating MOC for '{topic}'...")
            moc_data = self.moc_generator.generate_moc(
                topic=topic,
                top_k=top_k,
                threshold=threshold,
                include_orphans=False,
                use_expansion=True,
            )

            if moc_data and moc_data.total_documents > 0:
                result.moc_generated = True
                # MOC file path is determined by MOCGenerator
                if hasattr(moc_data, 'output_file') and moc_data.output_file:
                    result.moc_path = str(moc_data.output_file)
                print(f"  MOC generated: {moc_data.total_documents} documents organized")
            else:
                result.errors.append("MOC generation returned empty result")

        except Exception as e:
            msg = f"MOC generation failed: {e}"
            logger.exception(msg)
            result.errors.append(msg)

        return result

    def _add_related_links(
        self,
        files: List[Path],
        related_k: int,
        threshold: float,
        dry_run: bool,
        backup: bool,
        result: ConnectResult,
    ) -> ConnectResult:
        """Add related document links to each file."""
        total = len(files)
        for i, file_path in enumerate(files, 1):
            rel_path = str(file_path.relative_to(self.vault_path))
            try:
                if dry_run:
                    # Just check if related docs would be found
                    related = self.related_finder.find_related_docs(
                        str(file_path), top_k=related_k, threshold=threshold
                    )
                    if related:
                        result.docs_with_links_added += 1
                        if i <= 3:  # Show first 3 as preview
                            print(f"  [DRY-RUN] {rel_path} -> {len(related)} related docs")
                    else:
                        result.docs_skipped += 1
                    continue

                doc_result = self.related_finder.update_document(
                    file_path=str(file_path),
                    top_k=related_k,
                    threshold=threshold,
                    update_existing=True,
                    backup=backup,
                    dry_run=False,
                )

                if doc_result.success:
                    if doc_result.section_added or doc_result.existing_section_updated:
                        result.docs_with_links_added += 1
                    else:
                        result.docs_skipped += 1
                else:
                    result.docs_failed += 1
                    if doc_result.error_message:
                        result.errors.append(
                            f"{rel_path}: {doc_result.error_message}"
                        )

                # Progress indicator
                if i % 20 == 0 or i == total:
                    print(f"  Progress: {i}/{total} documents processed")

            except Exception as e:
                result.docs_failed += 1
                result.errors.append(f"{rel_path}: {e}")

        return result

    def get_status(self, detailed: bool = False) -> ConnectionStatus:
        """Get overall graph connection status."""
        tag_result = self.tag_analyzer.analyze(min_count=1)
        progress = self._read_progress()

        status = ConnectionStatus(
            total_documents=tag_result.total_documents,
            tagged_documents=tag_result.tagged_documents,
            untagged_documents=tag_result.untagged_documents,
        )

        completed_topics = set(progress.get('completed', []))
        in_progress_topics = set(progress.get('in_progress', []))

        # Build per-topic stats
        sorted_tags = sorted(
            tag_result.top_level_tags.items(),
            key=lambda x: x[1].count,
            reverse=True
        )

        for tag_name, tag_stat in sorted_tags:
            entry = {'name': tag_name, 'count': tag_stat.count}

            if tag_name in completed_topics:
                entry['completed_at'] = progress.get(
                    'completed_dates', {}
                ).get(tag_name, '')
                status.completed_topics.append(entry)
            elif tag_name in in_progress_topics:
                status.in_progress_topics.append(entry)
            else:
                status.pending_topics.append(entry)

        return status

    def format_status(self, status: ConnectionStatus, detailed: bool = False) -> str:
        """Format connection status for display."""
        lines = []
        lines.append("Graph Connection Status")
        lines.append("=" * 40)
        lines.append(f"Total documents:  {status.total_documents}")
        lines.append(f"Tagged:           {status.tagged_documents} "
                      f"({status.tagged_documents/max(status.total_documents,1)*100:.1f}%)")
        lines.append(f"Untagged:         {status.untagged_documents} "
                      f"({status.untagged_documents/max(status.total_documents,1)*100:.1f}%)")
        lines.append("")

        total_topics = (
            len(status.completed_topics) +
            len(status.in_progress_topics) +
            len(status.pending_topics)
        )
        lines.append(
            f"Topics Progress:  {len(status.completed_topics)}/{total_topics} completed"
        )
        lines.append("─" * 40)

        for t in status.completed_topics:
            date_str = f"  {t.get('completed_at', '')}" if t.get('completed_at') else ""
            lines.append(f"  ✅ {t['name']:<20} {t['count']:>4} docs{date_str}")

        for t in status.in_progress_topics:
            lines.append(f"  🔄 {t['name']:<20} {t['count']:>4} docs")

        if detailed:
            for t in status.pending_topics:
                lines.append(f"  ⬚  {t['name']:<20} {t['count']:>4} docs")
        else:
            pending_count = len(status.pending_topics)
            if pending_count > 0:
                lines.append(f"  ... {pending_count} more topics pending")

        if status.untagged_documents > 0:
            lines.append(f"  ⬚  {'(untagged)':<20} {status.untagged_documents:>4} docs")

        return "\n".join(lines)

    # --- Progress file management ---

    def _progress_path(self) -> Path:
        return self.vault_path / PROGRESS_FILENAME

    def _read_progress(self) -> Dict:
        """Read progress from the progress markdown file."""
        path = self._progress_path()
        if not path.exists():
            return {'completed': [], 'in_progress': [], 'completed_dates': {}}

        content = path.read_text(encoding='utf-8')
        progress: Dict = {
            'completed': [],
            'in_progress': [],
            'completed_dates': {},
        }

        for line in content.splitlines():
            line = line.strip()
            if line.startswith('- [x]'):
                # Extract topic name: "- [x] TDD (150 docs) — 2026-02-13"
                parts = line[5:].strip().split('(')
                topic_name = parts[0].strip()
                progress['completed'].append(topic_name)
                # Extract date if present
                if '—' in line:
                    date_part = line.split('—')[-1].strip()
                    progress['completed_dates'][topic_name] = date_part
            elif line.startswith('- [ ]') and 'In Progress' not in line:
                parts = line[5:].strip().split('(')
                topic_name = parts[0].strip()
                if topic_name not in progress['completed']:
                    # Check if in "In Progress" section
                    pass  # handled by section parsing

        return progress

    def _update_progress(self, result: ConnectResult):
        """Update the progress file after a topic connection run."""
        path = self._progress_path()
        path.parent.mkdir(parents=True, exist_ok=True)

        progress = self._read_progress()
        today = datetime.now().strftime("%Y-%m-%d")

        if result.documents_found > 0 and not result.dry_run:
            if result.topic not in progress['completed']:
                progress['completed'].append(result.topic)
                progress['completed_dates'][result.topic] = today
            if result.topic in progress.get('in_progress', []):
                progress['in_progress'].remove(result.topic)

        # Regenerate the full progress file
        self._write_progress_file(progress)

    def _write_progress_file(self, progress: Dict):
        """Write the progress markdown file."""
        path = self._progress_path()
        today = datetime.now().strftime("%Y-%m-%d")

        lines = ["# Graph Connect Progress", f"Last updated: {today}", ""]

        # Get current vault stats
        tag_result = self.tag_analyzer.analyze(min_count=1)
        lines.append("## Summary")
        lines.append(
            f"- Total: {tag_result.total_documents} docs | "
            f"Tagged: {tag_result.tagged_documents} | "
            f"Untagged: {tag_result.untagged_documents}"
        )
        lines.append("")

        # Completed topics
        lines.append("## Completed Topics")
        for topic in progress.get('completed', []):
            date = progress.get('completed_dates', {}).get(topic, '')
            count = tag_result.tag_counts.get(topic, 0)
            date_str = f" — {date}" if date else ""
            lines.append(f"- [x] {topic} ({count} docs){date_str}")
        if not progress.get('completed'):
            lines.append("(none yet)")
        lines.append("")

        # Pending topics
        lines.append("## Pending Topics")
        completed_set = set(progress.get('completed', []))
        pending = [
            (name, stat.count)
            for name, stat in tag_result.top_level_tags.items()
            if name not in completed_set
        ]
        pending.sort(key=lambda x: -x[1])
        for name, count in pending:
            lines.append(f"- [ ] {name} ({count} docs)")
        if not pending:
            lines.append("(all topics completed!)")
        lines.append("")

        # Final sweep
        lines.append("## Final Sweep")
        lines.append(
            f"- [ ] Tag untagged docs ({tag_result.untagged_documents} docs)"
        )
        lines.append("- [ ] Process remaining orphans")

        path.write_text("\n".join(lines), encoding='utf-8')
