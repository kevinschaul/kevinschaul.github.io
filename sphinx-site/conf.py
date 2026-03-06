"""Sphinx configuration for kevinschaul.github.io."""

import datetime
import glob
import os
import shutil

# ── Project info ──────────────────────────────────────────────────────────────
project = "Kevin Schaul"
author = "Kevin Schaul"
html_title = "Kevin Schaul"
html_baseurl = "https://www.kschaul.com"
language = "en"

# ── Extensions ────────────────────────────────────────────────────────────────
extensions = [
    "ablog",
    "myst_parser",
]

# ── MyST settings ─────────────────────────────────────────────────────────────
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]

# Allow raw HTML in markdown (needed for YouTube embeds etc.)
myst_fence_as_directive = ["code"]

# ── ABlog settings ────────────────────────────────────────────────────────────
blog_title = "Kevin Schaul"
blog_baseurl = "https://www.kschaul.com"
blog_path = "blog"  # URL for the main blog index

# All blog post directories (post, til, link are blog posts; project is a page)
blog_post_pattern = [
    "post/**/*.md",
    "til/**/*.md",
    "link/**/*.md",
]

blog_feed_fulltext = True
blog_feed_length = 10
blog_authors = {
    "Kevin Schaul": ("Kevin Schaul", "https://www.kschaul.com"),
}

# ── Theme ─────────────────────────────────────────────────────────────────────
# Theme lives at sphinx-site/sphinx_kschaul_theme/ — "." resolves relative
# to conf.py, so this works whether you run sphinx-build from the repo root
# or from within sphinx-site/.
html_theme = "sphinx_kschaul_theme"
html_theme_path = ["."]

html_theme_options = {
    "tagline": "Visual journalist/hacker covering AI",
    "description": "Kevin Schaul — Visual journalist/hacker covering AI",
}

_srcdir = os.path.dirname(__file__)
_project_slugs_with_images = {
    os.path.basename(os.path.dirname(p))
    for p in glob.glob(os.path.join(_srcdir, "project", "*", "tease.png"))
}

html_context = {
    "current_year": datetime.datetime.now().year,
    "nav_links": [
        {"name": "About", "url": "contact", "external": False},
        {"name": "LLM evals", "url": "https://kschaul.com/llm-evals/", "external": True},
        {"name": "Follow", "url": "follow", "external": False},
    ],
    "project_slugs_with_images": _project_slugs_with_images,
}

# ── Templates ─────────────────────────────────────────────────────────────────
templates_path = ["_templates"]

# ── Static files ──────────────────────────────────────────────────────────────
html_static_path = ["_static"]
html_favicon = "_static/favicon.ico"

# ── Exclude patterns ──────────────────────────────────────────────────────────
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]

# ── Output options ────────────────────────────────────────────────────────────
html_show_sphinx = False
html_show_sourcelink = False
html_copy_source = False

# Suppress expected warnings:
# - toc.not_included: ABlog-managed posts don't need toctree entries
# - myst.header: older posts use H2/H3 as first headings (cosmetic only)
# - myst.xref_missing: in-page anchor links treated as cross-references
suppress_warnings = ["toc.not_included", "myst.header", "myst.xref_missing"]

# Use dirhtml builder by default (produces clean /path/ URLs)
# Run: sphinx-build -b dirhtml sphinx-site _build/dirhtml


def _copy_tease_images(app, exception):
    """Copy project tease.png files to the output directory."""
    if exception:
        return
    for src in glob.glob(os.path.join(app.srcdir, "project", "*", "tease.png")):
        slug = os.path.basename(os.path.dirname(src))
        dst_dir = os.path.join(app.outdir, "project", slug)
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(dst_dir, "tease.png"))


def setup(app):
    app.connect("build-finished", _copy_tease_images)
