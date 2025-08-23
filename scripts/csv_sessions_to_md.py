#!/usr/bin/env python3
"""
csv_sessions_to_md.py

Convert a CSV export of live sessions into Markdown files with YAML front matter,
ready for your Academy KB indexer.

- Uses 'markdownify' to convert WordPress/Gutenberg HTML to clean Markdown (recommended).
- Falls back to a simple tag stripper if markdownify isn't installed (you'll get plain text).
- Flexible header mapping (content can live in "Content", "Description", etc.).
- Auto-creates slugs, normalizes tags/topics, and optionally links matching transcripts.

Usage:
  python scripts/csv_sessions_to_md.py \
    --csv /path/to/Live-Sessions-Export.csv \
    --out data/raw/docs/sessions \
    --transcripts-dir data/raw/transcripts

Tip:
  Ensure markdownify is installed for best results:
    python3 -m pip install markdownify
"""

from __future__ import annotations
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ---------- Config you can tweak ----------
DEFAULT_TAGS = ["live-session"]

HEADER_ALIASES = {
    "session_id": {"session id", "id", "session_id", "sid", "code"},
    "title": {"title", "name, ", "session title", "post title", "lesson title", "event"},
    "date": {"date", "session date", "event date", "published", "publish date"},
    # include "content" so your CSV body is recognized
    "description": {"description", "desc", "abstract", "blurb", "summary", "content"},
    "topics": {"topics", "topic list", "keywords"},
    "tags": {"tags", "labels"},
    "url": {"url", "page url", "link", "permalink"},
    "video_url": {"video url", "recording url", "youtube", "vimeo"},
    "duration": {"duration", "length"},
    "speakers": {"speakers", "presenter", "host", "instructor"},
}
TRANSCRIPT_EXTS = {".md", ".txt"}  # add ".pdf" if you want to link PDFs too
# -----------------------------------------

# ---------- HTML → Markdown cleanup ----------
try:
    from markdownify import markdownify as mdify  # pip install markdownify
except Exception:
    mdify = None
    print(
        "[warn] python package 'markdownify' not found. "
        "Falling back to plain text (no headings/lists). "
        "Install with: python3 -m pip install markdownify",
        file=sys.stderr,
    )

WP_COMMENT_PATTERN = re.compile(r"<!--\s*\/?wp:[^>]*-->\s*", re.IGNORECASE)
TAG_STRIP_PATTERN = re.compile(r"</?(div|span)[^>]*>", re.IGNORECASE)

def html_to_md(s: str) -> str:
    """Convert Gutenberg/HTML-rich content to clean Markdown."""
    if not s:
        return ""
    # Remove Gutenberg comment markers and non-semantic wrappers
    s = WP_COMMENT_PATTERN.sub("", s)
    s = TAG_STRIP_PATTERN.sub("", s)
    # Normalize common breaks before conversion
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)

    if mdify:
        # ATX headings (#) and * bullets render nicely in Obsidian
        s = mdify(s, heading_style="ATX", bullets="*")
    else:
        # Fallback: strip tags → plain text
        s = re.sub(r"<[^>]+>", "", s)

    # Compact extra blank lines
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s
# --------------------------------------------


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("&", " and ").replace("’", "").replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "untitled"


def parse_date(s: str) -> Optional[str]:
    """Return YYYY-MM-DD if recognizable, else None."""
    s = (s or "").strip()
    if not s:
        return None
    fmts = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%b %d %Y", "%B %d %Y"]
    for f in fmts:
        try:
            return dt.datetime.strptime(s, f).date().isoformat()
        except ValueError:
            continue
    m = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return None


def split_list_field(s: str) -> List[str]:
    """Split a comma/semicolon/pipe-separated string into clean, lowercase tags."""
    if not s:
        return []
    parts = re.split(r"[;,|]", s)
    cleaned = []
    for p in parts:
        t = p.strip().lower()
        if not t:
            continue
        t = t.replace(" ", "-")
        cleaned.append(t)
    # de-dup preserving order
    seen = set()
    out = []
    for t in cleaned:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def normalize_headers(row_keys: List[str]) -> Dict[str, str]:
    """Map discovered CSV headers to canonical field names using HEADER_ALIASES."""
    key_map: Dict[str, str] = {}
    lower_map = {k.lower().strip(): k for k in row_keys}
    for canon, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_map:
                key_map[canon] = lower_map[alias.lower()]
                break
    return key_map


def find_transcript_path(transcripts_dir: Optional[Path], session_id: str, slug: str) -> Optional[str]:
    if not transcripts_dir or not transcripts_dir.exists():
        return None
    sid = (session_id or "").lower()
    for p in transcripts_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in TRANSCRIPT_EXTS:
            name = p.name.lower()
            if (sid and sid in name) or (slug and slug in name):
                return str(p).replace("\\", "/")
    return None


def build_yaml(meta: Dict[str, Optional[str]], tags: List[str], topics: List[str]) -> str:
    lines = ["---"]
    for k in ["title", "date", "session_id", "url", "video_url", "duration", "speakers", "related_transcript"]:
        v = meta.get(k)
        if v:
            lines.append(f"{k}: {v}")
    if topics:
        lines.append(f"topics: [{', '.join(topics)}]")
    if tags:
        lines.append(f"tags: [{', '.join(tags)}]")
    lines.append("source: live-session")
    lines.append(f"last_updated: {dt.date.today().isoformat()}")
    lines.append("---")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Convert sessions CSV to Markdown notes with YAML.")
    ap.add_argument("--csv", required=True, type=Path, help="Path to sessions CSV export")
    ap.add_argument("--out", required=True, type=Path, help="Output directory for Markdown notes (e.g., data/raw/docs/sessions)")
    ap.add_argument("--transcripts-dir", type=Path, default=None, help="Optional: directory where transcript files live (to auto-link)")
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    with args.csv.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("No headers found in the CSV.")
        header_map = normalize_headers(reader.fieldnames)

        count = 0
        for row in reader:
            title = row.get(header_map.get("title", ""), "") or "Untitled Session"
            session_id = row.get(header_map.get("session_id", ""), "")
            date_raw = row.get(header_map.get("date", ""), "")
            raw_desc = row.get(header_map.get("description", ""), "")  # includes "Content"
            url = row.get(header_map.get("url", ""), "")
            video_url = row.get(header_map.get("video_url", ""), "")
            duration = row.get(header_map.get("duration", ""), "")
            speakers = row.get(header_map.get("speakers", ""), "")

            topics = split_list_field(row.get(header_map.get("topics", ""), ""))
            tags = split_list_field(row.get(header_map.get("tags", ""), "")) or DEFAULT_TAGS[:]

            # Derived
            nice_date = parse_date(date_raw) or ""
            slug_base = title if title and title.lower() != "untitled session" else (session_id or title)
            slug = slugify(slug_base or "session")
            if session_id:
                tags = list(dict.fromkeys(tags + [slugify(session_id)]))  # add session_id as tag

            rel_transcript = find_transcript_path(args.transcripts_dir, session_id, slug)

            meta = {
                "title": title,
                "date": nice_date,
                "session_id": session_id or None,
                "url": url or None,
                "video_url": video_url or None,
                "duration": duration or None,
                "speakers": speakers or None,
                "related_transcript": rel_transcript,
            }

            # HTML → Markdown for body
            description = html_to_md(raw_desc)

            yaml = build_yaml(meta, tags, topics)

            body_lines = []
            if description:
                body_lines.append(description)
                body_lines.append("")
            if topics:
                body_lines.append("key topics")
                body_lines.append("")
                for t in topics:
                    body_lines.append(f"- {t}")
                body_lines.append("")
            body_lines.append("notes")
            body_lines.append("")
            body_lines.append("_add session-specific notes, links, or highlights here_")

            md = f"{yaml}\n\n" + "\n".join(body_lines) + "\n"

            # Write file (avoid overwriting your edits)
            out_path = args.out / f"{slug}.md"
            final_path = out_path
            suffix = 1
            while final_path.exists():
                final_path = args.out / f"{slug}-{suffix}.md"
                suffix += 1
            final_path.write_text(md, encoding="utf-8")
            count += 1

    print(f"Created {count} Markdown session files in: {args.out}")


if __name__ == "__main__":
    main()
