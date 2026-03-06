#!/usr/bin/env python3
"""
Migrate Hugo content to Sphinx + ABlog format.

Usage:
    uv run scripts/migrate_hugo.py [--dry-run]

What it does:
  - Reads content/post/, content/til/, content/link/, content/project/
  - Converts Hugo front matter to ABlog/MyST front matter
  - Writes output files preserving URL structure:
      Hugo:   /post/2025/05/19/my-slug/
      Sphinx: post/2025/05/19/my-slug/index.md  (built with dirhtml)
  - Copies associated image/asset files alongside the index.md
  - Rewrites the one known Hugo shortcode: {{< youtube ID >}}
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
CONTENT_ROOT = REPO_ROOT / "content"


# ── Front-matter helpers ──────────────────────────────────────────────────────

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
YOUTUBE_RE = re.compile(r'\{\{<\s*youtube\s+([A-Za-z0-9_-]+)\s*>\}\}')


def parse_hugo_file(path: Path) -> tuple[dict, str]:
    """Return (front_matter_dict, body_text) for a Hugo markdown file."""
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    body = text[m.end():]
    return fm, body


def parse_date(value) -> datetime | None:
    """Parse Hugo date values into a datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    # Try common formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value).split("+")[0].strip(), fmt)
        except ValueError:
            continue
    return None


def tags_to_list(tags_value) -> list[str]:
    """Normalise Hugo tag values (list, string, or None) to a list."""
    if tags_value is None:
        return []
    if isinstance(tags_value, list):
        # Filter out the literal 'link' tag that Hugo uses for content type
        return [str(t) for t in tags_value if str(t).lower() != "link"]
    return [str(tags_value)]


def rewrite_shortcodes(body: str) -> str:
    """Replace Hugo shortcodes with MyST equivalents."""
    # {{< youtube VIDEO_ID >}} → raw HTML embed
    body = YOUTUBE_RE.sub(
        lambda m: (
            "```{raw} html\n"
            f'<iframe width="560" height="315" '
            f'src="https://www.youtube.com/embed/{m.group(1)}" '
            'title="YouTube video" frameborder="0" allowfullscreen></iframe>\n'
            "```"
        ),
        body,
    )
    return body


# ── Per-content-type converters ───────────────────────────────────────────────

def build_ablog_front_matter(
    *,
    title: str,
    date: datetime,
    tags: list[str],
    category: str,
    author: str = "Kevin Schaul",
    slug: str | None = None,
    external_url: str | None = None,
    draft: bool = False,
) -> dict:
    fm: dict = {
        "blogpost": True,
        "date": date.strftime("%Y-%m-%d"),
        "author": author,
        "category": category,
    }
    if title:
        fm["title"] = title
    if tags:
        fm["tags"] = ", ".join(tags)
    if slug:
        fm["slug"] = slug
    if external_url:
        fm["external_url"] = external_url
    if draft:
        fm["draft"] = True
    return fm


def write_sphinx_file(
    dest: Path,
    front_matter: dict,
    body: str,
    dry_run: bool = False,
) -> None:
    """Write a MyST markdown file with YAML front matter."""
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
    content = "---\n" + yaml.dump(front_matter, allow_unicode=True, sort_keys=False) + "---\n\n" + body.lstrip()
    if dry_run:
        print(f"  [DRY RUN] Would write {dest}")
    else:
        dest.write_text(content, encoding="utf-8")


def copy_assets(src_dir: Path, dest_dir: Path, dry_run: bool = False) -> None:
    """Copy non-markdown assets (images, etc.) from src_dir to dest_dir."""
    for asset in src_dir.iterdir():
        if asset.name in ("index.md", "index.html") or asset.is_dir():
            continue
        dest = dest_dir / asset.name
        if dry_run:
            print(f"  [DRY RUN] Would copy {asset.name} → {dest}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, dest)


# ── Post migration ─────────────────────────────────────────────────────────────

def migrate_post(src_dir: Path, dry_run: bool = False) -> Path | None:
    """Migrate a single post from content/post/YYYY-MM-DD-slug/."""
    index_md = src_dir / "index.md"
    if not index_md.exists():
        return None

    hugo_fm, body = parse_hugo_file(index_md)
    date = parse_date(hugo_fm.get("date"))
    if date is None:
        print(f"  WARNING: no date in {index_md}, skipping", file=sys.stderr)
        return None

    title = str(hugo_fm.get("title", src_dir.name))
    slug = str(hugo_fm.get("slug", src_dir.name))
    tags = tags_to_list(hugo_fm.get("tags"))

    # Output path: post/YYYY/MM/DD/slug/index.md
    dest_dir = REPO_ROOT / "post" / date.strftime("%Y/%m/%d") / slug
    dest = dest_dir / "index.md"

    fm = build_ablog_front_matter(
        title=title,
        date=date,
        tags=tags,
        category="blog",
        slug=slug,
    )

    body = rewrite_shortcodes(body)
    print(f"  post: {src_dir.name} → post/{date.strftime('%Y/%m/%d')}/{slug}/")
    write_sphinx_file(dest, fm, body, dry_run=dry_run)
    copy_assets(src_dir, dest_dir, dry_run=dry_run)
    return dest


def migrate_til(src_dir: Path, dry_run: bool = False) -> Path | None:
    """Migrate a single TIL from content/til/YYYY-MM-DD-slug/."""
    index_md = src_dir / "index.md"
    if not index_md.exists():
        return None

    hugo_fm, body = parse_hugo_file(index_md)
    date = parse_date(hugo_fm.get("date"))
    if date is None:
        print(f"  WARNING: no date in {index_md}, skipping", file=sys.stderr)
        return None

    title = str(hugo_fm.get("title", src_dir.name))
    slug = str(hugo_fm.get("slug", src_dir.name))
    tags = tags_to_list(hugo_fm.get("tags"))

    # Output path: til/YYYY/MM/DD/slug/index.md
    dest_dir = REPO_ROOT / "til" / date.strftime("%Y/%m/%d") / slug
    dest = dest_dir / "index.md"

    fm = build_ablog_front_matter(
        title=title,
        date=date,
        tags=tags,
        category="til",
        slug=slug,
    )

    body = rewrite_shortcodes(body)
    print(f"  til:  {src_dir.name} → til/{date.strftime('%Y/%m/%d')}/{slug}/")
    write_sphinx_file(dest, fm, body, dry_run=dry_run)
    copy_assets(src_dir, dest_dir, dry_run=dry_run)
    return dest


def migrate_link(src_dir: Path, dry_run: bool = False) -> Path | None:
    """Migrate a single link post from content/link/slug/."""
    index_md = src_dir / "index.md"
    if not index_md.exists():
        return None

    hugo_fm, body = parse_hugo_file(index_md)
    date = parse_date(hugo_fm.get("date"))
    if date is None:
        print(f"  WARNING: no date in {index_md}, skipping", file=sys.stderr)
        return None

    # Link post titles often double as the linked page title; keep as-is
    title = str(hugo_fm.get("title", src_dir.name))
    slug = src_dir.name  # Hugo link slugs are URL-derived
    tags = tags_to_list(hugo_fm.get("tags"))

    # Output path: link/slug/index.md (preserve existing Hugo URL pattern)
    dest_dir = REPO_ROOT / "link" / slug
    dest = dest_dir / "index.md"

    fm = build_ablog_front_matter(
        title=title,
        date=date,
        tags=tags,
        category="link",
        slug=slug,
    )

    body = rewrite_shortcodes(body)
    print(f"  link: {src_dir.name} → link/{slug}/")
    write_sphinx_file(dest, fm, body, dry_run=dry_run)
    copy_assets(src_dir, dest_dir, dry_run=dry_run)
    return dest


def migrate_project(src_dir: Path, dry_run: bool = False) -> Path | None:
    """Migrate a single project from content/project/slug/."""
    index_md = src_dir / "index.md"
    if not index_md.exists():
        return None

    hugo_fm, body = parse_hugo_file(index_md)
    date = parse_date(hugo_fm.get("date"))
    if date is None:
        print(f"  WARNING: no date in {index_md}, skipping", file=sys.stderr)
        return None

    title = str(hugo_fm.get("title", src_dir.name))
    slug = str(hugo_fm.get("slug", src_dir.name))
    tags = tags_to_list(hugo_fm.get("tags"))
    external_url = hugo_fm.get("external_url")

    # Output path: project/slug/index.md
    dest_dir = REPO_ROOT / "project" / slug
    dest = dest_dir / "index.md"

    fm = build_ablog_front_matter(
        title=title,
        date=date,
        tags=tags,
        category="project",
        slug=slug,
        external_url=external_url,
    )

    # For projects with external URLs, add a redirect note in the body
    if external_url and not body.strip():
        body = f"Redirecting to [{external_url}]({external_url}) …\n"

    body = rewrite_shortcodes(body)
    print(f"  proj: {src_dir.name} → project/{slug}/")
    write_sphinx_file(dest, fm, body, dry_run=dry_run)
    copy_assets(src_dir, dest_dir, dry_run=dry_run)
    return dest


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Hugo content to Sphinx/ABlog.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen, don't write files.")
    args = parser.parse_args()
    dry_run = args.dry_run

    if dry_run:
        print("DRY RUN — no files will be written.\n")

    counts = {"post": 0, "til": 0, "link": 0, "project": 0, "skipped": 0}

    # Migrate posts
    post_src = CONTENT_ROOT / "post"
    if post_src.is_dir():
        print(f"\n=== Posts ({post_src}) ===")
        for d in sorted(post_src.iterdir()):
            if d.is_dir() and (d / "index.md").exists():
                result = migrate_post(d, dry_run=dry_run)
                if result:
                    counts["post"] += 1
                else:
                    counts["skipped"] += 1

    # Migrate TILs
    til_src = CONTENT_ROOT / "til"
    if til_src.is_dir():
        print(f"\n=== TIL ({til_src}) ===")
        for d in sorted(til_src.iterdir()):
            if d.is_dir() and (d / "index.md").exists():
                result = migrate_til(d, dry_run=dry_run)
                if result:
                    counts["til"] += 1
                else:
                    counts["skipped"] += 1

    # Migrate links
    link_src = CONTENT_ROOT / "link"
    if link_src.is_dir():
        print(f"\n=== Links ({link_src}) ===")
        for d in sorted(link_src.iterdir()):
            if d.is_dir() and (d / "index.md").exists():
                result = migrate_link(d, dry_run=dry_run)
                if result:
                    counts["link"] += 1
                else:
                    counts["skipped"] += 1

    # Migrate projects
    project_src = CONTENT_ROOT / "project"
    if project_src.is_dir():
        print(f"\n=== Projects ({project_src}) ===")
        for d in sorted(project_src.iterdir()):
            if d.is_dir() and (d / "index.md").exists():
                result = migrate_project(d, dry_run=dry_run)
                if result:
                    counts["project"] += 1
                else:
                    counts["skipped"] += 1

    print(f"\n=== Done ===")
    print(f"  Posts:    {counts['post']}")
    print(f"  TIL:      {counts['til']}")
    print(f"  Links:    {counts['link']}")
    print(f"  Projects: {counts['project']}")
    print(f"  Skipped:  {counts['skipped']}")
    print()
    if not dry_run:
        print("Note: The link update script (scripts/update_links.py) writes to")
        print("content/link/. Update it to write to link/ after verifying the migration.")


if __name__ == "__main__":
    main()
