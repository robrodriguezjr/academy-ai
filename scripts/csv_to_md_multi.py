#!/usr/bin/env python3
"""
csv_to_md_multi.py

Convert CSV exports to Markdown notes with YAML front matter.

Supports:
  --kind live     (Academy live sessions)
  --kind blog     (blog posts; requires --site cpa|rrjr)

Examples:
  Live sessions:
    python scripts/csv_to_md_multi.py \
      --kind live \
      --csv data/imports/Live-Sessions-Export-2025-August-23-1135.csv \
      --out data/raw/docs/sessions \
      --transcripts-dir data/raw/transcripts

  Creative Path Academy blog:
    python scripts/csv_to_md_multi.py \
      --kind blog --site cpa \
      --csv data/imports/cpa-posts.csv \
      --out data/raw/docs/blog/cpa

  robertrodriguezjr.com blog:
    python scripts/csv_to_md_multi.py \
      --kind blog --site rrjr \
      --csv data/imports/rrjr-posts.csv \
      --out data/raw/docs/blog/rrjr
"""

from __future__ import annotations
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ---------- optional HTML → Markdown ----------
try:
    from markdownify import markdownify as mdify  # pip install markdownify
except Exception:
    mdify = None
    print(
        "[warn] 'markdownify' not found. Install for best results:\n"
        "  python -m pip install markdownify\n",
        file=sys.stderr,
    )

WP_COMMENT_PATTERN = re.compile(r"<!--\s*\/?wp:[^>]*-->\s*", re.IGNORECASE)
TAG_STRIP_PATTERN = re.compile(r"</?(div|span)[^>]*>", re.IGNORECASE)

def html_to_md(s: str) -> str:
    """Convert Gutenberg/HTML to clean Markdown; fallback to plain text."""
    if not s:
        return ""
    s = WP_COMMENT_PATTERN.sub("", s)
    s = TAG_STRIP_PATTERN.sub("", s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    if mdify:
        s = mdify(s, heading_style="ATX", bullets="*")
    else:
        s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s

URL_RE = re.compile(r"https?://[^\s)>\"]+", re.IGNORECASE)
VIDEO_HOSTS = ("youtube.com","youtu.be","vimeo.com","player.vimeo.com","wistia.com","fast.wistia.net","prestoplayer","presto-player")

def extract_urls(text: str) -> list[str]:
    return URL_RE.findall(text or "")

def pick_video_url(urls: list[str]) -> Optional[str]:
    for u in urls or []:
        lu = u.lower()
        if any(h in lu for h in VIDEO_HOSTS):
            return u
    return (urls or [None])[0]

# ---------- utils ----------
def slugify(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.replace("&", " and ").replace("’", "").replace("'", "")
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "untitled"

def parse_date(s: str) -> Optional[str]:
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
    if not s:
        return []
    parts = re.split(r"[;,|]", s)
    out, seen = [], set()
    for p in parts:
        t = p.strip()
        if not t:
            continue
        # normalize to kebab-case for tags/categories/topics
        norm = re.sub(r"\s+", "-", t.lower())
        if norm not in seen:
            out.append(norm); seen.add(norm)
    return out

def yaml_kv(k: str, v: Optional[str]) -> str:
    if not v:
        return ""
    # quote values with colon unless URL-ish
    if ":" in v and not v.startswith("http"):
        return f'{k}: "{v}"'
    return f"{k}: {v}"

def yaml_list_line(key: str, values: List[str]) -> str:
    if not values:
        return ""
    return f"{key}: [{', '.join(values)}]"

def safe_write_unique(path: Path, content: str) -> Path:
    """Avoid overwriting existing files by suffixing -1, -2, ..."""
    path.parent.mkdir(parents=True, exist_ok=True)
    p = path
    i = 1
    while p.exists():
        if p.suffix:
            p = p.with_name(f"{p.stem}-{i}{p.suffix}")
        else:
            p = Path(str(p) + f"-{i}")
        i += 1
    p.write_text(content, encoding="utf-8")
    return p

# ---------- header mapping helpers ----------
LIVE_ALIASES = {
    "session_id": {"session id", "id", "session_id", "sid", "code"},
    "title": {"title", "session title", "post title", "lesson title", "event"},
    "date": {"date", "session date", "event date", "published", "publish date"},
    "description": {"content", "description", "desc", "abstract", "blurb", "summary"},
    "topics": {"topics", "topic list", "keywords"},
    "tags": {"tags", "labels"},
    "categories": {"categories"},
    "url": {"url", "page url", "link", "permalink"},
    "video_url": {"video url", "recording url", "youtube", "vimeo"},
    "duration": {"duration", "length"},
    "speakers": {"speakers", "presenter", "host", "instructor"},
}

BLOG_ALIASES = {
    "title": {"title"},
    "date": {"date", "published", "publish date"},
    "description": {"content", "body", "html", "post", "article"},
    "excerpt": {"excerpt", "summary"},
    "tags": {"tags", "labels"},
    "categories": {"categories"},
    "topics": {"topics", "keywords"},
    "url": {"url", "permalink", "link"},
    "author": {"author"},
}

def normalize_headers(aliases: Dict[str, set], row_keys: List[str]) -> Dict[str, str]:
    key_map: Dict[str, str] = {}
    lower_map = {k.lower().strip(): k for k in row_keys}
    for canon, names in aliases.items():
        for alias in names:
            if alias.lower() in lower_map:
                key_map[canon] = lower_map[alias.lower()]
                break
    return key_map

# ---------- builders ----------
def build_yaml(
    meta: Dict[str, Optional[str]],
    tags: List[str],
    categories: List[str],
    topics: List[str],
    source: str
) -> str:
    lines = ["---"]
    order = [
        "title", "date", "session_id", "author", "url",
        "video_url", "duration", "speakers", "site"
    ]
    for k in order:
        v = meta.get(k)
        if v:
            lines.append(yaml_kv(k, v))
    if topics:
        lines.append(yaml_list_line("topics", topics))
    if tags:
        lines.append(yaml_list_line("tags", tags))
    if categories:
        lines.append(yaml_list_line("categories", categories))
    lines.append(f"source: {source}")
    lines.append(f"last_updated: {dt.date.today().isoformat()}")
    lines.append("---")
    return "\n".join([l for l in lines if l])

def build_body(description_md: str, topics: List[str]) -> str:
    body = []
    if description_md:
        body.append(description_md.strip())
        body.append("")
    if topics:
        body.append("key topics")
        body.append("")
        for t in topics:
            body.append(f"- {t}")
        body.append("")
    body.append("notes")
    body.append("")
    body.append("_add session-specific notes, links, or highlights here_")
    return "\n".join(body) + "\n"

# ---------- kind: live ----------
def process_live(csv_path: Path, out_dir: Path, transcripts_dir: Optional[Path]) -> int:
    count = 0
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("No headers found in the live sessions CSV.")
        h = normalize_headers(LIVE_ALIASES, reader.fieldnames)

        for row in reader:
            title = (row.get(h.get("title",""), "") or "Untitled Session").strip()
            session_id = (row.get(h.get("session_id",""), "") or "").strip()
            date_raw = (row.get(h.get("date",""), "") or "").strip()
            desc_html = (row.get(h.get("description",""), "") or "")
            topics = split_list_field(row.get(h.get("topics",""), ""))
            tags = split_list_field(row.get(h.get("tags",""), "")) or ["live-session"]
            categories = split_list_field(row.get(h.get("categories",""), ""))
            url = (row.get(h.get("url",""), "") or "").strip()
            video_url = (row.get(h.get("video_url",""), "") or "").strip()
            if not video_url:
                cand = extract_urls(desc_html)
                video_url = pick_video_url(cand) or ""
            duration = (row.get(h.get("duration",""), "") or "").strip()
            speakers = (row.get(h.get("speakers",""), "") or "").strip()

            date_iso = parse_date(date_raw) or ""
            base = title if title.lower() != "untitled session" else (session_id or title)
            slug = slugify(base or "session")

            # add session_id as tag for filtering
            if session_id:
                sid_tag = slugify(session_id)
                if sid_tag not in tags:
                    tags.append(sid_tag)

            # optional transcript linking by heuristic (sid or slug inside filename)
            related_transcript = None
            if transcripts_dir and transcripts_dir.exists():
                for p in transcripts_dir.rglob("*"):
                    if p.is_file() and p.suffix.lower() in {".md",".txt"}:
                        name = p.name.lower()
                        if (session_id and session_id.lower() in name) or (slug in name):
                            related_transcript = str(p).replace("\\","/")
                            break

            body_md = html_to_md(desc_html)

            meta = {
                "title": title,
                "date": date_iso,
                "session_id": session_id or None,
                "url": url or None,
                "video_url": video_url or None,
                "duration": duration or None,
                "speakers": speakers or None,
                "site": "academy",
            }

            yaml = build_yaml(meta, tags, categories, topics, source="live-session")
            md = f"{yaml}\n\n{build_body(body_md, topics)}"

            fname = f"{date_iso+'-' if date_iso else ''}{slug}.md"
            out_path = out_dir / fname
            safe_write_unique(out_path, md)
            count += 1

    return count

# ---------- kind: blog ----------
def process_blog(csv_path: Path, out_dir: Path, site: str) -> int:
    """
    site: 'cpa' or 'rrjr'
    """
    count = 0
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit("No headers found in the blog CSV.")
        h = normalize_headers(BLOG_ALIASES, reader.fieldnames)

        for row in reader:
            title = (row.get(h.get("title",""), "") or "Untitled").strip()
            date_iso = parse_date(row.get(h.get("date",""), "")) or ""
            url = (row.get(h.get("url",""), "") or "").strip()
            author = (row.get(h.get("author",""), "") or "").strip()
            desc_html = (row.get(h.get("description",""), "") or "")
            excerpt_html = (row.get(h.get("excerpt",""), "") or "")
            tags = split_list_field(row.get(h.get("tags",""), ""))
            categories = split_list_field(row.get(h.get("categories",""), ""))
            topics = split_list_field(row.get(h.get("topics",""), ""))

            # Prefer description, fall back to excerpt
            html = desc_html if desc_html.strip() else excerpt_html
            body_md = html_to_md(html)

            meta = {
                "title": title,
                "date": date_iso,
                "author": author or None,
                "url": url or None,
                "site": "cpa" if site == "cpa" else "rrjr",
            }
            src = "blog-cpa" if site == "cpa" else "blog-rrjr"
            yaml = build_yaml(meta, tags, categories, topics, source=src)
            md = f"{yaml}\n\n{build_body(body_md, topics)}"

            slug = slugify(title)
            fname = f"{date_iso+'-' if date_iso else ''}{slug}.md"
            out_path = out_dir / fname
            safe_write_unique(out_path, md)
            count += 1

    return count

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="Convert CSVs to Markdown for Academy AI KB.")
    ap.add_argument("--kind", required=True, choices=["live","blog"])
    ap.add_argument("--site", choices=["cpa","rrjr"], help="Required for --kind blog")
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--transcripts-dir", type=Path, default=None, help="(live only) optional transcript folder")
    args = ap.parse_args()

    if args.kind == "blog" and not args.site:
        ap.error("--site cpa|rrjr is required for --kind blog")

    args.out.mkdir(parents=True, exist_ok=True)

    if args.kind == "live":
        n = process_live(args.csv, args.out, args.transcripts_dir)
        print(f"Created {n} live session Markdown files in: {args.out}")
    else:
        n = process_blog(args.csv, args.out, args.site)
        print(f"Created {n} blog Markdown files in: {args.out}")

if __name__ == "__main__":
    main()