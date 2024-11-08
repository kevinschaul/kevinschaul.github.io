import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import os
from scripts.update_links import (
    get_url_metadata,
    slugify,
    search_similar_posts,
    get_links_from_github
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
    
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = html_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test OG title priority
        metadata = get_url_metadata("https://example.com")
        assert metadata["title"] == "OG Title"
        
        # Test fallback to HTML title
        html_content_no_meta = "<html><head><title>Only HTML Title</title></head></html>"
        mock_response.text = html_content_no_meta
        metadata = get_url_metadata("https://example.com")
        assert metadata["title"] == "Only HTML Title"

def test_search_similar_posts():
    """Test searching for similar posts"""
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"statuses": []}
        mock_get.return_value = mock_response
        
        story = {"story_permalink": "https://example.com"}
        result = search_similar_posts(story, "fake_token")
        assert result == False  # No similar posts found

        mock_response.json.return_value = {"statuses": ["post1"]}
        result = search_similar_posts(story, "fake_token")
        assert result == True  # Similar post found

def test_get_links_from_github():
    """Test GitHub links extraction"""
    with patch('github.Github') as mock_github:
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.title = "Test Issue"
        mock_issue.body = "https://example.com\nDescription"
        mock_issue.created_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_issue.number = 1
        
        mock_repo.get_issues.return_value = [mock_issue]
        mock_github.return_value.get_repo.return_value = mock_repo
        
        with patch.dict('os.environ', {
            'GITHUB_TOKEN': 'fake_token',
            'GITHUB_REPOSITORY': 'user/repo'
        }):
            links = get_links_from_github()
            assert len(links) == 1
            assert links[0]["url"] == "https://example.com"
            assert links[0]["title"] == "Test Issue"
