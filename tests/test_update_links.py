import pytest
from unittest.mock import patch, MagicMock
from scripts.update_links import (
    get_url_metadata,
    slugify,
)


def test_slugify():
    """Test the slugify function handles various inputs correctly"""
    assert slugify("Hello World") == "Hello_World"
    assert slugify("https://example.com/path") == "example.com_path"
    assert slugify("test!@#$%^&*()") == "test"
    assert slugify("   spaces   ") == "spaces"

    with pytest.raises(Exception):
        slugify("")

    with pytest.raises(Exception):
        slugify(".")


def test_get_url_metadata():
    """Test URL metadata extraction"""
    html_content = """
    <html>
        <head>
            <title>HTML Title</title>
            <meta property="og:title" content="OG Title" />
            <meta name="twitter:title" content="Twitter Title" />
        </head>
    </html>
    """

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test OG title priority
        metadata = get_url_metadata("https://example.com")
        assert metadata["title"] == "OG Title"

        # Test fallback to HTML title
        html_content_no_meta = (
            "<html><head><title>Only HTML Title</title></head></html>"
        )
        mock_response.text = html_content_no_meta
        metadata = get_url_metadata("https://example.com")
        assert metadata["title"] == "Only HTML Title"
