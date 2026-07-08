from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def markdown_files():
    return sorted([*CONTENT.rglob("*.md"), *CONTENT.rglob("*.markdown")])


def test_no_hugo_shortcodes_remain():
    offenders = []
    for path in markdown_files():
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if "{{<" in line:
                offenders.append(f"{path.relative_to(ROOT)}:{line_number}")

    assert offenders == []


def test_no_liquid_highlight_blocks_remain():
    offenders = []
    for path in markdown_files():
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            if "{% highlight" in line or "{% endhighlight" in line:
                offenders.append(f"{path.relative_to(ROOT)}:{line_number}")

    assert offenders == []


def test_markdown_code_fences_have_languages():
    offenders = []
    for path in markdown_files():
        in_fence = False
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if not stripped.startswith("```"):
                continue

            if not in_fence:
                info = stripped[3:].strip()
                if not info:
                    offenders.append(f"{path.relative_to(ROOT)}:{line_number}")
                in_fence = True
            else:
                in_fence = False

    assert offenders == []


def test_no_generated_html_content_files_remain():
    assert sorted(path for path in CONTENT.rglob("*.html") if path.is_file()) == []


def test_hugo_shortcode_remark_plugin_removed():
    assert not (ROOT / "src/lib/remark-hugo-shortcodes.mjs").exists()
    assert "remarkHugoShortcodes" not in (ROOT / "astro.config.mjs").read_text()
