"""Sphinx configuration for kevinschaul.github.io."""

import datetime

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
html_theme = "sphinx_kschaul_theme"
html_theme_path = ["."]

html_theme_options = {
    "tagline": "Visual journalist/hacker covering AI",
    "description": "Kevin Schaul — Visual journalist/hacker covering AI",
}

html_context = {
    "current_year": datetime.datetime.now().year,
    "nav_links": [
        {"name": "About", "url": "contact", "external": False},
        {"name": "LLM evals", "url": "https://kschaul.com/llm-evals/", "external": True},
        {"name": "Follow", "url": "follow", "external": False},
    ],
}

# ── Static files ──────────────────────────────────────────────────────────────
html_static_path = ["_static"]
html_favicon = "_static/favicon.ico"

# Copy Hugo static files (headshot, favicon, etc.) – these will be symlinked
# or copied into _static/ by the build process. See Makefile.

# ── Exclude patterns ──────────────────────────────────────────────────────────
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "README.md",
    # Python environment
    ".venv",
    # Keep Hugo source files out of Sphinx build
    "content",
    "layouts",
    "themes",
    "archetypes",
    "node_modules",
    # Scripts dir has no docs
    "scripts",
]

# ── Output options ────────────────────────────────────────────────────────────
html_show_sphinx = False
html_show_sourcelink = False
html_copy_source = False

# Suppress expected warnings:
# - toc.not_included: ABlog-managed posts don't need toctree entries
# - myst.header: older posts use H2/H3 as first headings (cosmetic only)
suppress_warnings = ["toc.not_included", "myst.header", "myst.xref_missing"]

# Use dirhtml builder by default (produces clean /path/ URLs)
# Run: make dirhtml
