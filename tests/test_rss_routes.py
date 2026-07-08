from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def test_rss_route_files_exist():
    routes = [
        "src/pages/index.xml.ts",
        "src/pages/post/index.xml.ts",
        "src/pages/link/index.xml.ts",
        "src/pages/project/index.xml.ts",
        "src/pages/til/index.xml.ts",
        "src/pages/tags/[tag]/index.xml.ts",
    ]

    assert [route for route in routes if not (ROOT / route).exists()] == []


def test_rss_routes_share_feed_options():
    routes = [
        "src/pages/index.xml.ts",
        "src/pages/post/index.xml.ts",
        "src/pages/link/index.xml.ts",
        "src/pages/project/index.xml.ts",
        "src/pages/til/index.xml.ts",
        "src/pages/tags/[tag]/index.xml.ts",
    ]

    offenders = [
        route
        for route in routes
        if "feedOptions(" not in read(route) or "@astrojs/rss" not in read(route)
    ]

    assert offenders == []


def test_archive_pages_advertise_their_specific_feed():
    expected = {
        "src/pages/post/index.astro": 'rssHref="/post/index.xml"',
        "src/pages/post/page/[page]/index.astro": 'rssHref="/post/index.xml"',
        "src/pages/link/index.astro": 'rssHref="/link/index.xml"',
        "src/pages/link/page/[page]/index.astro": 'rssHref="/link/index.xml"',
        "src/pages/project/index.astro": 'rssHref="/project/index.xml"',
        "src/pages/project/page/[page]/index.astro": 'rssHref="/project/index.xml"',
        "src/pages/til/index.astro": 'rssHref="/til/index.xml"',
        "src/pages/til/page/[page]/index.astro": 'rssHref="/til/index.xml"',
        "src/pages/tags/[tag]/index.astro": 'rssHref={`/tags/${Astro.params.tag}/index.xml`}',
        "src/pages/tags/[tag]/page/[page]/index.astro": 'rssHref={`/tags/${Astro.params.tag}/index.xml`}',
    }

    offenders = [
        f"{path} missing {snippet}"
        for path, snippet in expected.items()
        if snippet not in read(path)
    ]

    assert offenders == []


def test_site_layout_defaults_to_home_feed():
    layout = read("src/layouts/SiteLayout.astro")

    assert "rssHref?: string" in layout
    assert 'rssHref = "/index.xml"' in layout
    assert "rssHref={absoluteUrl(rssHref)}" in layout
