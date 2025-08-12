import pytest
import os
import json
from unittest.mock import patch, MagicMock
from scripts.update_links import (
    get_url_metadata,
    slugify,
    extract_images_from_issue,
    get_post_directory_path,
    generate_markdown_content,
    download_post_images,
    should_skip_issue,
    convert_issue_to_post,
    process_github_issues,
    remove_images_from_text,
    process_issue_text,
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


def test_extract_images_from_issue():
    """Test image extraction from GitHub issue body"""
    # Load the fixture
    with open("tests/fixtures/github_issue_85.json", "r") as f:
        issue_data = json.load(f)

    images = extract_images_from_issue(issue_data["body"])
    assert len(images) == 2
    assert (
        "https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1"
        in images
    )
    assert (
        "https://github.com/user-attachments/assets/9264ebdb-8818-4b56-a51d-a9af0298b237"
        in images
    )


def test_remove_images_from_text():
    """Test that remove_images_from_text removes image content correctly"""
    # Test with HTML img tags
    html_text = """Some text before <img width="565" height="571" alt="Image" src="https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1" /> and some text after."""

    cleaned = remove_images_from_text(html_text)
    expected = "Some text before  and some text after."
    assert cleaned == expected

    # Test with markdown images
    markdown_text = (
        """Some text ![alt text](https://example.com/image.jpg) more text."""
    )
    cleaned = remove_images_from_text(markdown_text)
    expected = "Some text  more text."
    assert cleaned == expected

    # Test with GitHub assets URLs
    github_text = """Text with https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1 in it."""
    cleaned = remove_images_from_text(github_text)
    expected = "Text with  in it."
    assert cleaned == expected

    # Test with our fixture data
    with open("tests/fixtures/github_issue_85.json", "r") as f:
        issue_data = json.load(f)

    cleaned = remove_images_from_text(issue_data["body"])
    # Should not contain any image HTML
    assert "<img" not in cleaned
    assert "github.com/user-attachments/assets" not in cleaned
    # Should still contain the main text
    assert (
        'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.'
        in cleaned
    )

    # Test with empty/None input
    assert remove_images_from_text("") == ""
    assert remove_images_from_text(None) == None


def test_process_issue_text():
    """Test that process_issue_text extracts images with alt text and cleans text efficiently"""
    # Test with our fixture data
    with open("tests/fixtures/github_issue_85.json", "r") as f:
        issue_data = json.load(f)

    cleaned_text, images = process_issue_text(issue_data["body"])

    # Should extract both images with alt text
    assert len(images) == 2
    
    # Check first image
    image1 = next((img for img in images if "5b6a3d2d-4408-4f25-b3af-93fddee7deb1" in img["src"]), None)
    assert image1 is not None
    assert image1["src"] == "https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1"
    assert image1["alt"] == "Image"
    
    # Check second image
    image2 = next((img for img in images if "9264ebdb-8818-4b56-a51d-a9af0298b237" in img["src"]), None)
    assert image2 is not None
    assert image2["src"] == "https://github.com/user-attachments/assets/9264ebdb-8818-4b56-a51d-a9af0298b237"
    assert image2["alt"] == "Image"

    # Should clean the text
    assert "<img" not in cleaned_text
    assert "github.com/user-attachments/assets" not in cleaned_text
    assert (
        'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.'
        in cleaned_text
    )

    # Test with mixed content including alt text
    mixed_text = """Some text before <img alt="Test Image" src="https://example.com/image1.jpg" /> and ![alt text here](https://example.com/image2.png) more text.
    
    Also this URL: https://github.com/user-attachments/assets/test123"""

    cleaned, extracted = process_issue_text(mixed_text)

    assert len(extracted) == 3
    
    # Check HTML image with alt text
    html_img = next((img for img in extracted if "image1.jpg" in img["src"]), None)
    assert html_img is not None
    assert html_img["src"] == "https://example.com/image1.jpg"
    assert html_img["alt"] == "Test Image"
    
    # Check markdown image with alt text
    md_img = next((img for img in extracted if "image2.png" in img["src"]), None)
    assert md_img is not None
    assert md_img["src"] == "https://example.com/image2.png"
    assert md_img["alt"] == "alt text here"
    
    # Check standalone URL (no alt text)
    standalone_img = next((img for img in extracted if "test123" in img["src"]), None)
    assert standalone_img is not None
    assert standalone_img["src"] == "https://github.com/user-attachments/assets/test123"
    assert standalone_img["alt"] is None

    # Should remove all image content from text
    assert "<img" not in cleaned
    assert "![alt" not in cleaned
    assert "github.com/user-attachments/assets" not in cleaned
    assert "Some text before  and  more text." in cleaned

    # Test with empty input
    cleaned_empty, images_empty = process_issue_text("")
    assert cleaned_empty == ""
    assert images_empty == []

    # Test with None input
    cleaned_none, images_none = process_issue_text(None)
    assert cleaned_none == None
    assert images_none == []


def test_get_post_directory_path():
    """Test that get_post_directory_path generates the correct directory path"""
    test_post = {
        "date": "2025-08-11T21:10:27Z",
        "text": 'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.',
        "images": None,
        "hash": "85",
    }

    # Test with default content directory - should use just the date part (no timezone)
    date_part = test_post["date"].split("T")[0]  # "2025-08-11"
    expected_slug = slugify(f"{date_part}_{test_post['text'][:30]}")
    expected_path = os.path.join("./content", "link", expected_slug)
    actual_path = get_post_directory_path(test_post)
    assert actual_path == expected_path

    # Test with custom content directory
    custom_content_dir = "/tmp/test_content"
    expected_custom_path = os.path.join(custom_content_dir, "link", expected_slug)
    actual_custom_path = get_post_directory_path(test_post, custom_content_dir)
    assert actual_custom_path == expected_custom_path


def test_generate_markdown_content():
    """Test that generate_markdown_content creates correct markdown"""
    test_post = {
        "date": "2025-08-11T21:10:27Z",
        "text": 'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.',
        "images": None,
        "hash": "85",
    }

    # Test without images
    markdown = generate_markdown_content(test_post)
    expected_content = """---
date: 2025-08-11T21:10:27Z
---

I've been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint."""
    assert markdown == expected_content

    # Test with images including alt text
    test_post_with_images = {
        "date": "2025-08-11T21:10:27Z",
        "text": 'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.',
        "images": [
            {"src": "https://example.com/image1.jpg", "alt": "A test image"},
            {"src": "https://example.com/image2.png", "alt": None},
            {"src": "https://example.com/image3.gif", "alt": "Another image"}
        ],
        "hash": "85",
    }
    test_downloaded_images = ["local_image1.jpg", "local_image2.png", "local_image3.gif"]
    
    markdown_with_images = generate_markdown_content(test_post_with_images, test_downloaded_images)
    expected_with_images = """---
date: 2025-08-11T21:10:27Z
images:
  - src: local_image1.jpg
    alt: "A test image"
  - src: local_image2.png
  - src: local_image3.gif
    alt: "Another image"
---

I've been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint."""
    assert markdown_with_images == expected_with_images

    # Test backward compatibility with simple string list
    test_images = ["image1.jpg", "image2.png"]
    markdown_legacy = generate_markdown_content(test_post, test_images)
    expected_legacy = """---
date: 2025-08-11T21:10:27Z
images:
  - src: image1.jpg
  - src: image2.png
---

I've been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint."""
    assert markdown_legacy == expected_legacy


def test_download_post_images():
    """Test that download_post_images handles image downloading correctly"""
    # Test post without images
    test_post_no_images = {
        "date": "2025-08-11T21:10:27Z",
        "text": "Test post without images",
        "images": None,
        "hash": "85",
    }

    with patch("scripts.update_links.download_image") as mock_download:
        result = download_post_images(test_post_no_images, "/tmp/test")
        assert result == []
        mock_download.assert_not_called()

    # Test post with images (new format with alt text)
    test_post_with_images = {
        "date": "2025-08-11T21:10:27Z",
        "text": "Test post with images",
        "images": [
            {"src": "https://example.com/image1.jpg", "alt": "Test image 1"},
            {"src": "https://example.com/image2.png", "alt": None}
        ],
        "hash": "85",
    }

    with patch("scripts.update_links.download_image") as mock_download:
        # Mock successful downloads
        mock_download.side_effect = ["downloaded1.jpg", "downloaded2.png"]
        result = download_post_images(test_post_with_images, "/tmp/test")

        assert result == ["downloaded1.jpg", "downloaded2.png"]
        assert mock_download.call_count == 2
        mock_download.assert_any_call("https://example.com/image1.jpg", "/tmp/test")
        mock_download.assert_any_call("https://example.com/image2.png", "/tmp/test")


def test_should_skip_issue():
    """Test that should_skip_issue correctly identifies issues to skip"""
    # Create mock issue without do-not-post label
    mock_issue_ok = MagicMock()
    mock_label = MagicMock()
    mock_label.name = "bug"
    mock_issue_ok.labels = [mock_label]

    assert should_skip_issue(mock_issue_ok) is False

    # Create mock issue with do-not-post label
    mock_issue_skip = MagicMock()
    mock_label1 = MagicMock()
    mock_label1.name = "enhancement"
    mock_label2 = MagicMock()
    mock_label2.name = "do-not-post"
    mock_issue_skip.labels = [mock_label1, mock_label2]

    assert should_skip_issue(mock_issue_skip) is True

    # Create mock issue with no labels
    mock_issue_empty = MagicMock()
    mock_issue_empty.labels = []

    assert should_skip_issue(mock_issue_empty) is False


def test_convert_issue_to_post():
    """Test that convert_issue_to_post correctly converts GitHub issues to Posts"""
    # Load fixture data to get real issue body
    with open("tests/fixtures/github_issue_85.json", "r") as f:
        issue_data = json.load(f)

    # Create mock GitHub issue
    mock_issue = MagicMock()
    mock_issue.body = issue_data["body"]
    mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
    mock_issue.number = issue_data["number"]

    # Convert issue to post
    post = convert_issue_to_post(mock_issue)

    # Verify the post structure
    assert post["date"] == issue_data["createdAt"]
    # Text should now be cleaned of images
    assert (
        post["text"]
        == 'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.'
    )
    assert post["hash"] == str(issue_data["number"])
    assert len(post["images"]) == 2  # From our fixture
    
    # Check that images have alt text from the fixture
    image_srcs = [img["src"] for img in post["images"]]
    assert "https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1" in image_srcs
    assert "https://github.com/user-attachments/assets/9264ebdb-8818-4b56-a51d-a9af0298b237" in image_srcs
    
    # Check alt text is extracted
    for img in post["images"]:
        assert img["alt"] == "Image"  # From fixture
    
    # Verify images are not in the cleaned text
    assert "<img" not in post["text"]


def test_process_github_issues():
    """Test that process_github_issues correctly processes a list of issues"""
    # Load fixture data
    with open("tests/fixtures/github_issue_85.json", "r") as f:
        issue_data = json.load(f)

    # Create mock issues
    mock_issue1 = MagicMock()
    mock_issue1.body = issue_data["body"]
    mock_issue1.created_at.isoformat.return_value = issue_data["createdAt"]
    mock_issue1.number = issue_data["number"]
    mock_issue1.labels = []  # No labels, should be processed

    mock_issue2 = MagicMock()
    mock_issue2.body = "Another issue"
    mock_issue2.created_at.isoformat.return_value = "2025-08-12T10:00:00Z"
    mock_issue2.number = 86
    mock_label = MagicMock()
    mock_label.name = "do-not-post"
    mock_issue2.labels = [mock_label]  # Should be skipped

    mock_issue3 = MagicMock()
    mock_issue3.body = "Third issue"
    mock_issue3.created_at.isoformat.return_value = "2025-08-12T12:00:00Z"
    mock_issue3.number = 87
    mock_issue3.labels = []  # No labels, should be processed

    issues = [mock_issue1, mock_issue2, mock_issue3]
    posts = process_github_issues(issues)

    # Should only process 2 issues (skip the one with do-not-post label)
    assert len(posts) == 2

    # Verify first post - text should now be cleaned of images
    assert posts[0]["date"] == issue_data["createdAt"]
    assert (
        posts[0]["text"]
        == 'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.'
    )
    assert posts[0]["hash"] == str(issue_data["number"])
    assert "<img" not in posts[0]["text"]  # Images should be removed

    # Verify second post (third issue)
    assert posts[1]["date"] == "2025-08-12T12:00:00Z"
    assert posts[1]["text"] == "Third issue"
    assert posts[1]["hash"] == "87"
