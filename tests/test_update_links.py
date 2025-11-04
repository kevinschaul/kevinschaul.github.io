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
    extract_links_from_text,
    split_text_into_posts,
)


def test_slugify():
    """Test the slugify function handles various inputs correctly"""
    assert slugify("Hello World") == "hello_world"
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
    assert remove_images_from_text(None) is None


def test_process_issue_text():
    """Test that process_issue_text extracts images with alt text and cleans text efficiently"""
    # Test with our fixture data
    with open("tests/fixtures/github_issue_85.json", "r") as f:
        issue_data = json.load(f)

    cleaned_text, images = process_issue_text(issue_data["body"])

    # Should extract both images with alt text
    assert len(images) == 2

    # Check first image
    image1 = next(
        (img for img in images if "5b6a3d2d-4408-4f25-b3af-93fddee7deb1" in img["src"]),
        None,
    )
    assert image1 is not None
    assert (
        image1["src"]
        == "https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1"
    )
    assert image1["alt"] == "Image"

    # Check second image
    image2 = next(
        (img for img in images if "9264ebdb-8818-4b56-a51d-a9af0298b237" in img["src"]),
        None,
    )
    assert image2 is not None
    assert (
        image2["src"]
        == "https://github.com/user-attachments/assets/9264ebdb-8818-4b56-a51d-a9af0298b237"
    )
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
    assert cleaned_none is None
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
            {"src": "https://example.com/image3.gif", "alt": "Another image"},
        ],
        "hash": "85",
    }
    test_downloaded_images = [
        "local_image1.jpg",
        "local_image2.png",
        "local_image3.gif",
    ]

    markdown_with_images = generate_markdown_content(
        test_post_with_images, test_downloaded_images
    )
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
            {"src": "https://example.com/image2.png", "alt": None},
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
    assert (
        "https://github.com/user-attachments/assets/5b6a3d2d-4408-4f25-b3af-93fddee7deb1"
        in image_srcs
    )
    assert (
        "https://github.com/user-attachments/assets/9264ebdb-8818-4b56-a51d-a9af0298b237"
        in image_srcs
    )

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
    # process_github_issues now returns list of (issue, post) tuples
    results = process_github_issues(issues, for_social=False)

    # Should only process 2 issues (skip the one with do-not-post label)
    assert len(results) == 2

    # Verify first post - text should now be cleaned of images
    issue1, post1 = results[0]
    assert issue1 == mock_issue1
    assert post1["date"] == issue_data["createdAt"]
    assert (
        post1["text"]
        == 'I\'ve been asking LLMs "Who is Kevin Schaul?" and the results do not disappoint.'
    )
    assert post1["hash"] == str(issue_data["number"])
    assert "<img" not in post1["text"]  # Images should be removed

    # Verify second post (third issue)
    issue3, post3 = results[1]
    assert issue3 == mock_issue3
    assert post3["date"] == "2025-08-12T12:00:00Z"
    assert post3["text"] == "Third issue"
    assert post3["hash"] == "87"


def test_extract_links_from_text():
    """Test that extract_links_from_text preserves formatting while extracting links"""

    # Test basic link extraction
    text1 = "Check out this cool article: https://example.com/article and let me know what you think!"
    text_without_links1, links1 = extract_links_from_text(text1)
    assert (
        text_without_links1
        == "Check out this cool article: and let me know what you think!"
    )
    assert links1 == ["https://example.com/article"]

    # Test formatting preservation with bullet points and line breaks
    text2 = """Key features:

- Fast performance: https://example.com/speed
- Easy to use
- Great documentation: https://docs.example.com

Overall very good!"""

    text_without_links2, links2 = extract_links_from_text(text2)
    expected_text2 = """Key features:

- Fast performance:
- Easy to use
- Great documentation:

Overall very good!"""
    assert text_without_links2 == expected_text2
    assert links2 == ["https://example.com/speed", "https://docs.example.com"]

    # Test punctuation removal from links
    text3 = "Check out https://example.com/path?param=value, it's great!"
    text_without_links3, links3 = extract_links_from_text(text3)
    assert text_without_links3 == "Check out it's great!"
    assert links3 == ["https://example.com/path?param=value"]  # Comma removed

    # Test multiple links on same line
    text4 = "Sites: https://one.com https://two.com and https://three.com are good"
    text_without_links4, links4 = extract_links_from_text(text4)
    assert text_without_links4 == "Sites: and are good"
    assert links4 == ["https://one.com", "https://two.com", "https://three.com"]

    # Test the real-world example that was broken
    text5 = """Lovely analysis of how Claude Code works. Highlights include:

- Runs on one loop. If task is complex, clones itself, with one loop.
- Uses its small model (Haiku) majority of the time
- System prompt includes a lot of "IMPORTANT" and "VERY IMPORTANT" instructions, which, lol

https://minusx.ai/blog/decoding-claude-code/"""

    text_without_links5, links5 = extract_links_from_text(text5)
    expected_text5 = """Lovely analysis of how Claude Code works. Highlights include:

- Runs on one loop. If task is complex, clones itself, with one loop.
- Uses its small model (Haiku) majority of the time
- System prompt includes a lot of "IMPORTANT" and "VERY IMPORTANT" instructions, which, lol"""

    assert text_without_links5 == expected_text5
    assert links5 == ["https://minusx.ai/blog/decoding-claude-code/"]

    # Test no links
    text6 = "This is just a normal post with no links at all."
    text_without_links6, links6 = extract_links_from_text(text6)
    assert text_without_links6 == "This is just a normal post with no links at all."
    assert links6 == []

    # Test various punctuation scenarios
    punctuation_tests = [
        ("Link: https://example.com.", ["https://example.com"]),
        ("Link: https://example.com!", ["https://example.com"]),
        ("Link: https://example.com?", ["https://example.com"]),
        ("Link: https://example.com;", ["https://example.com"]),
        ("Link: https://example.com:", ["https://example.com"]),
        ("Link: https://example.com,", ["https://example.com"]),
        ("Link: https://example.com...", ["https://example.com"]),
    ]

    for text, expected_links in punctuation_tests:
        _, extracted_links = extract_links_from_text(text)
        assert extracted_links == expected_links


# ============================================================================
# THREAD SUPPORT TESTS
# ============================================================================


class TestThreadParsing:
    """Tests for parsing GitHub issues into thread sections"""

    def test_parse_basic_thread(self):
        """Test parsing a simple thread with --- separators"""
        text = """First post in the thread.

---

Second post in the thread.

---

Third post in the thread."""

        from scripts.update_links import parse_thread_sections

        sections = parse_thread_sections(text)

        assert len(sections) == 3
        assert sections[0]["text"] == "First post in the thread."
        assert sections[1]["text"] == "Second post in the thread."
        assert sections[2]["text"] == "Third post in the thread."
        assert sections[0]["images"] == []
        assert sections[1]["images"] == []
        assert sections[2]["images"] == []

    def test_parse_thread_with_images(self):
        """Test parsing threads where each section has its own images"""
        with open("tests/fixtures/github_issue_109.json", "r") as f:
            issue_data = json.load(f)

        from scripts.update_links import parse_thread_sections

        sections = parse_thread_sections(issue_data["body"])

        # Should have 3 sections
        assert len(sections) == 3

        # First section - intro text, no images
        assert "I keep a running log" in sections[0]["text"]
        assert len(sections[0]["images"]) == 0

        # Second section - text about ChatGPT with one image
        assert "ChatGPT" in sections[1]["text"]
        assert "wayback machine" in sections[1]["text"]
        assert len(sections[1]["images"]) == 1
        assert "da5c35e4-14ee-4cb3-b769-245f1f66d23d" in sections[1]["images"][0]["src"]
        assert sections[1]["images"][0]["alt"] == "Image"

        # Third section - text about Gemini with one image
        assert "Gemini" in sections[2]["text"]
        assert len(sections[2]["images"]) == 1
        assert "e991f85f-76f8-410b-b293-f0bb4bc74795" in sections[2]["images"][0]["src"]
        assert sections[2]["images"][0]["alt"] == "Image"

    def test_parse_no_thread(self):
        """Test that posts without --- work normally"""
        with open("tests/fixtures/github_issue_no_thread.json", "r") as f:
            issue_data = json.load(f)

        from scripts.update_links import parse_thread_sections

        sections = parse_thread_sections(issue_data["body"])

        # Should have only 1 section
        assert len(sections) == 1
        assert "simple post without any thread separators" in sections[0]["text"]
        assert sections[0]["images"] == []

    def test_parse_alternate_separators(self):
        """Test parsing with different markdown separator formats"""
        from scripts.update_links import parse_thread_sections

        # Test with *** separator
        text_asterisks = "First post\n\n***\n\nSecond post"
        sections = parse_thread_sections(text_asterisks)
        assert len(sections) == 2
        assert sections[0]["text"] == "First post"
        assert sections[1]["text"] == "Second post"

        # Test with ___ separator
        text_underscores = "First post\n\n___\n\nSecond post"
        sections = parse_thread_sections(text_underscores)
        assert len(sections) == 2
        assert sections[0]["text"] == "First post"
        assert sections[1]["text"] == "Second post"


class TestHugoPostGeneration:
    """Tests for Hugo blog post generation (merged threads)"""

    def test_convert_thread_for_hugo(self):
        """Test that Hugo posts merge all thread sections and strip ---"""
        with open("tests/fixtures/github_issue_109.json", "r") as f:
            issue_data = json.load(f)

        mock_issue = MagicMock()
        mock_issue.body = issue_data["body"]
        mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
        mock_issue.number = issue_data["number"]

        from scripts.update_links import convert_issue_to_post

        # For Hugo (for_social=False), should return single merged post
        post = convert_issue_to_post(mock_issue, for_social=False)

        # Should be a single post dict
        assert isinstance(post, dict)

        # Text should contain all sections merged (no ---)
        assert "I keep a running log" in post["text"]
        assert "ChatGPT" in post["text"]
        assert "Gemini" in post["text"]
        assert "---" not in post["text"]  # Separator should be removed

        # Should have all images from all sections
        assert len(post["images"]) == 2
        image_srcs = [img["src"] for img in post["images"]]
        assert any("da5c35e4" in src for src in image_srcs)
        assert any("e991f85f" in src for src in image_srcs)

    def test_convert_single_post_for_hugo(self):
        """Test that single posts work for Hugo"""
        with open("tests/fixtures/github_issue_no_thread.json", "r") as f:
            issue_data = json.load(f)

        mock_issue = MagicMock()
        mock_issue.body = issue_data["body"]
        mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
        mock_issue.number = issue_data["number"]

        from scripts.update_links import convert_issue_to_post

        hugo_post = convert_issue_to_post(mock_issue, for_social=False)
        assert isinstance(hugo_post, dict)
        assert "simple post" in hugo_post["text"]

    def test_generate_markdown_for_thread_issue(self):
        """Test that Hugo markdown generation works with thread issues (merged)"""
        with open("tests/fixtures/github_issue_109.json", "r") as f:
            issue_data = json.load(f)

        mock_issue = MagicMock()
        mock_issue.body = issue_data["body"]
        mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
        mock_issue.number = issue_data["number"]

        from scripts.update_links import (
            convert_issue_to_post,
            generate_markdown_content,
        )

        # Get Hugo post (merged)
        hugo_post = convert_issue_to_post(mock_issue, for_social=False)

        # Generate markdown
        markdown = generate_markdown_content(hugo_post, downloaded_images=[])

        # Should contain merged content
        assert "I keep a running log" in markdown
        assert "ChatGPT" in markdown
        assert "Gemini" in markdown

        # Should NOT contain --- separator
        # (The separator might appear in frontmatter as YAML, so check in the body)
        lines = markdown.split("\n")
        body_started = False
        body_lines = []
        for line in lines:
            if body_started:
                body_lines.append(line)
            elif line == "---" and body_lines:
                # Second ---, body starts after this
                body_started = True
            elif line == "---":
                # First ---, frontmatter starts
                body_lines.append(line)

        body = "\n".join(body_lines[1:])  # Skip the closing ---
        # Count occurrences of --- in body (should be 0)
        separator_count = body.count("\n---\n")
        assert separator_count == 0, (
            f"Found {separator_count} thread separators in body"
        )


class TestSocialMediaThreads:
    """Tests for social media thread generation"""

    def test_convert_thread_for_social(self):
        """Test that social media posts return list of posts (thread)"""
        with open("tests/fixtures/github_issue_109.json", "r") as f:
            issue_data = json.load(f)

        mock_issue = MagicMock()
        mock_issue.body = issue_data["body"]
        mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
        mock_issue.number = issue_data["number"]

        from scripts.update_links import convert_issue_to_post

        # For social (for_social=True), should return list of posts
        posts = convert_issue_to_post(mock_issue, for_social=True)

        # Should be a list
        assert isinstance(posts, list)
        assert len(posts) == 3

        # Each post should have thread metadata
        for i, post in enumerate(posts):
            assert post["thread_index"] == i
            assert post["thread_total"] == 3

        # First post - intro
        assert "I keep a running log" in posts[0]["text"]
        assert len(posts[0]["images"]) == 0

        # Second post - ChatGPT with image
        assert "ChatGPT" in posts[1]["text"]
        assert len(posts[1]["images"]) == 1

        # Third post - Gemini with image
        assert "Gemini" in posts[2]["text"]
        assert len(posts[2]["images"]) == 1

    def test_convert_single_post_for_social(self):
        """Test that single posts work for social media"""
        with open("tests/fixtures/github_issue_no_thread.json", "r") as f:
            issue_data = json.load(f)

        mock_issue = MagicMock()
        mock_issue.body = issue_data["body"]
        mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
        mock_issue.number = issue_data["number"]

        from scripts.update_links import convert_issue_to_post

        # Social version - should still be a list with one item
        social_posts = convert_issue_to_post(mock_issue, for_social=True)
        assert isinstance(social_posts, list)
        assert len(social_posts) == 1
        assert social_posts[0]["thread_index"] == 0
        assert social_posts[0]["thread_total"] == 1

    def test_thread_post_ordering(self):
        """Test that thread posts maintain correct order"""
        with open("tests/fixtures/github_issue_thread_simple.json", "r") as f:
            issue_data = json.load(f)

        mock_issue = MagicMock()
        mock_issue.body = issue_data["body"]
        mock_issue.created_at.isoformat.return_value = issue_data["createdAt"]
        mock_issue.number = issue_data["number"]

        from scripts.update_links import convert_issue_to_post

        posts = convert_issue_to_post(mock_issue, for_social=True)

        # Verify order is maintained
        assert "First post" in posts[0]["text"]
        assert "Second post" in posts[1]["text"]
        assert "Third post" in posts[2]["text"]

        # Verify thread indices
        assert posts[0]["thread_index"] == 0
        assert posts[1]["thread_index"] == 1
        assert posts[2]["thread_index"] == 2


class TestBlueskyLinkCards:
    """Tests for Bluesky external link card generation"""

    def test_create_link_card_with_metadata(self):
        """Test creating Bluesky external link embed"""
        from scripts.update_links import create_bluesky_link_card

        # Mock the metadata fetching
        with patch("scripts.update_links.get_url_metadata") as mock_get_metadata:
            mock_get_metadata.return_value = {
                "title": "Great Article About AI",
                "description": "An in-depth look at artificial intelligence",
            }

            card = create_bluesky_link_card("https://example.com/article")

            assert card is not None
            assert card["$type"] == "app.bsky.embed.external"
            assert card["external"]["uri"] == "https://example.com/article"
            assert card["external"]["title"] == "Great Article About AI"
            assert (
                card["external"]["description"]
                == "An in-depth look at artificial intelligence"
            )

    def test_create_link_card_no_title(self):
        """Test that link card returns None when no title is found"""
        from scripts.update_links import create_bluesky_link_card

        with patch("scripts.update_links.get_url_metadata") as mock_get_metadata:
            mock_get_metadata.return_value = {}

            card = create_bluesky_link_card("https://example.com/no-metadata")

            assert card is None

    def test_extract_first_url_for_link_card(self):
        """Test extracting first URL from post for link card"""
        text_with_urls = """Check out this article:

https://example.com/first-link

Also see: https://example.com/second-link"""

        import re

        urls = re.findall(r"https?://[^\s]+", text_with_urls)

        # Should extract URLs in order
        assert len(urls) == 2
        assert urls[0] == "https://example.com/first-link"

        # Link card should use the first URL
        from scripts.update_links import create_bluesky_link_card

        with patch("scripts.update_links.get_url_metadata") as mock_get_metadata:
            mock_get_metadata.return_value = {"title": "First Link"}

            card = create_bluesky_link_card(urls[0])
            assert card["external"]["uri"] == "https://example.com/first-link"


class TestPlatformExclusion:
    """Tests for platform exclusion based on labels"""

    def test_get_excluded_platforms_no_labels(self):
        """Test that no platforms are excluded when no labels present"""
        from scripts.update_links import get_excluded_platforms

        mock_issue = MagicMock()
        mock_issue.labels = []

        excluded = get_excluded_platforms(mock_issue)
        assert excluded == []

    def test_get_excluded_platforms_single_exclusion(self):
        """Test excluding a single platform"""
        from scripts.update_links import get_excluded_platforms

        mock_issue = MagicMock()
        mock_label = MagicMock()
        mock_label.name = "exclude-blog"
        mock_issue.labels = [mock_label]

        excluded = get_excluded_platforms(mock_issue)
        assert excluded == ["blog"]

    def test_get_excluded_platforms_multiple_exclusions(self):
        """Test excluding multiple platforms"""
        from scripts.update_links import get_excluded_platforms

        mock_issue = MagicMock()

        label1 = MagicMock()
        label1.name = "exclude-blog"

        label2 = MagicMock()
        label2.name = "exclude-mastodon"

        label3 = MagicMock()
        label3.name = "exclude-x"

        mock_issue.labels = [label1, label2, label3]

        excluded = get_excluded_platforms(mock_issue)
        assert "blog" in excluded
        assert "mastodon" in excluded
        assert "x" in excluded
        assert len(excluded) == 3

    def test_get_excluded_platforms_all_platforms(self):
        """Test excluding all platforms"""
        from scripts.update_links import get_excluded_platforms

        mock_issue = MagicMock()

        labels = []
        for label_name in [
            "exclude-blog",
            "exclude-mastodon",
            "exclude-x",
            "exclude-bluesky",
        ]:
            label = MagicMock()
            label.name = label_name
            labels.append(label)

        mock_issue.labels = labels

        excluded = get_excluded_platforms(mock_issue)
        assert "blog" in excluded
        assert "mastodon" in excluded
        assert "x" in excluded
        assert "bluesky" in excluded
        assert len(excluded) == 4

    def test_get_excluded_platforms_mixed_labels(self):
        """Test that only exclude-* labels are recognized"""
        from scripts.update_links import get_excluded_platforms

        mock_issue = MagicMock()

        label1 = MagicMock()
        label1.name = "exclude-blog"

        label2 = MagicMock()
        label2.name = "some-other-label"

        label3 = MagicMock()
        label3.name = "do-not-post"

        mock_issue.labels = [label1, label2, label3]

        excluded = get_excluded_platforms(mock_issue)
        assert excluded == ["blog"]


class TestXTwitterSpecialHandling:
    """Tests for X/Twitter specific link handling"""

    def test_links_always_in_separate_posts(self):
        """Test that X/Twitter always puts links in separate posts"""
        # Even for a single post with a link, X should create a second post
        single_post_with_link = {
            "date": "2024-10-01T10:00:00Z",
            "text": "Check out this article: https://example.com/article",
            "images": [],
            "thread_index": 0,
            "thread_total": 1,
            "hash": "100",
        }

        # When preparing for X, we should:
        # 1. Extract the link from the text
        # 2. Create main post without link
        # 3. Create a second post with just the link as a reply

        text_without_links, links = extract_links_from_text(
            single_post_with_link["text"]
        )

        assert text_without_links == "Check out this article:"
        assert len(links) == 1
        assert links[0] == "https://example.com/article"

        # This means even a "single" post becomes a 2-post thread on X:
        # Post 1: "Check out this article:"
        # Post 2 (reply): "https://example.com/article"

    def test_multiple_thread_posts_with_links(self):
        """Test X handling for thread with multiple posts containing links"""
        # Thread posts with links
        thread_posts = [
            {
                "text": "First post intro: https://example.com/1",
                "images": [],
                "thread_index": 0,
                "thread_total": 2,
            },
            {
                "text": "Second post: https://example.com/2",
                "images": [],
                "thread_index": 1,
                "thread_total": 2,
            },
        ]

        # For X, the NEW structure should be:
        # Post 1: "First post intro:" (link extracted)
        # Post 2 (reply): "Second post: https://example.com/2" (link kept in thread post)
        # Post 3 (reply): "https://example.com/1" (link from first post only)

        # Extract links only from the first post
        is_thread = len(thread_posts) > 1
        all_links = []

        for post_index, post in enumerate(thread_posts):
            if post_index == 0:
                # First post - extract links
                _, links = extract_links_from_text(post["text"])
                all_links.extend(links)
            elif is_thread:
                # Thread posts after first - keep links in text
                # No links extracted
                pass

        # Only the first post's link should be extracted
        assert len(all_links) == 1
        assert all_links[0] == "https://example.com/1"

        # Second post should keep its link
        second_post_text = thread_posts[1]["text"]
        assert "https://example.com/2" in second_post_text


def test_split_text_into_posts():
    """Test that split_text_into_posts creates proper thread posts"""

    # Test short text (should not be split)
    short_text = "This is a short text that should not be split."
    result = split_text_into_posts(short_text, 280)
    assert result == [short_text]

    # Test long text that needs splitting
    long_text = """This is a very long text that should be split into multiple posts. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.

This should definitely create multiple posts when posted to X with its 280 character limit."""

    result = split_text_into_posts(long_text, 280)

    # Should be split into multiple posts
    assert len(result) > 1

    # Each post should have thread indicators
    for i, post in enumerate(result):
        assert post.startswith(f"({i + 1}/{len(result)})")
        assert len(post) <= 280  # Respect character limit

    # Test with different character limits
    # Mastodon (500 chars)
    mastodon_result = split_text_into_posts(long_text, 500)
    assert len(mastodon_result) < len(result)  # Should need fewer posts

    # Bluesky (300 chars)
    bluesky_result = split_text_into_posts(long_text, 300)
    assert len(bluesky_result) >= len(result)  # Might need same or more posts

    # Test paragraph splitting behavior
    paragraph_text = """First paragraph is here.

Second paragraph is longer and contains more content that might need to be split depending on the character limits.

Third paragraph is short."""

    paragraph_result = split_text_into_posts(paragraph_text, 150)
    assert len(paragraph_result) > 1
    for post in paragraph_result:
        assert len(post) <= 150

    # Test edge case: very long single word (should force split)
    long_word = "a" * 300
    word_result = split_text_into_posts(long_word, 280)
    assert len(word_result) > 1
    for post in word_result:
        assert len(post) <= 280


def test_process_issue_text_for_blog():
    """Test that blog posts keep images inline"""
    from scripts.update_links import process_issue_text_for_blog

    # Test with HTML img tag
    text = """Some text before <img src="https://example.com/image1.jpg" alt="Test Image" /> and text after.

More content here."""

    url_to_filename = {
        "https://example.com/image1.jpg": "local_image1.jpg",
    }

    result = process_issue_text_for_blog(text, url_to_filename)

    # Should replace URL with local filename, keeping HTML format
    assert '<img src="local_image1.jpg" alt="Test Image" />' in result
    assert "https://example.com/image1.jpg" not in result
    assert "Some text before" in result
    assert "and text after" in result

    # Test with markdown image
    text2 = """Check this out:

![My Image](https://example.com/image2.png)

Pretty cool!"""

    url_to_filename2 = {
        "https://example.com/image2.png": "local_image2.png",
    }

    result2 = process_issue_text_for_blog(text2, url_to_filename2)

    assert "![My Image](local_image2.png)" in result2
    assert "example.com" not in result2

    # Test with standalone GitHub URL
    text3 = """Here's a screenshot:

https://github.com/user-attachments/assets/abc123

What do you think?"""

    url_to_filename3 = {
        "https://github.com/user-attachments/assets/abc123": "screenshot.jpg",
    }

    result3 = process_issue_text_for_blog(text3, url_to_filename3)

    # Should replace URL with local filename
    assert "screenshot.jpg" in result3
    assert "github.com/user-attachments" not in result3


def test_generate_markdown_content_inline():
    """Test that inline markdown content is generated correctly"""
    from scripts.update_links import generate_markdown_content_inline

    post = {
        "date": "2025-08-11T21:10:27Z",
        "text": "Original text (not used)",
        "hash": "123",
        "images": [{"src": "https://example.com/image.jpg", "alt": "Test Image"}],
    }

    markdown_text = """Here is my post with an image:

![Test Image](local_image.jpg)

Pretty neat!"""

    url_to_filename = {"https://example.com/image.jpg": "local_image.jpg"}

    result = generate_markdown_content_inline(post, markdown_text, url_to_filename)

    # Should have frontmatter
    assert "---" in result
    assert "date: 2025-08-11T21:10:27Z" in result

    # Should have inline image in body
    assert "![Test Image](local_image.jpg)" in result
    assert "Pretty neat!" in result

    # Should ALSO have images in frontmatter for Hugo template on index page
    assert "images:" in result
    assert "- src: local_image.jpg" in result
    assert 'alt: "Test Image"' in result


def test_x_twitter_formatting_preservation():
    """Test that X/Twitter posting preserves formatting correctly"""

    # Use the real-world example that was previously broken
    original_text = """Lovely analysis of how Claude Code works. Highlights include:

- Runs on one loop. If task is complex, clones itself, with one loop.
- Uses its small model (Haiku) majority of the time
- System prompt includes a lot of "IMPORTANT" and "VERY IMPORTANT" instructions, which, lol

https://minusx.ai/blog/decoding-claude-code/"""

    # Extract links (as X posting would do)
    text_without_links, links = extract_links_from_text(original_text)

    # Split into posts (as X posting would do)
    x_posts = split_text_into_posts(text_without_links, 280)

    # Verify formatting is preserved
    assert len(x_posts) == 1  # Should fit in one post without the link
    main_post = x_posts[0]

    # Should preserve line breaks and bullet points
    assert "\n" in main_post
    assert "- Runs on one loop" in main_post
    assert "- Uses its small model" in main_post
    assert "- System prompt includes" in main_post

    # Should not contain the link
    assert "https://" not in main_post

    # Link should be extracted separately
    assert len(links) == 1
    assert links[0] == "https://minusx.ai/blog/decoding-claude-code/"

    # Test another formatting example
    formatted_text = """Analysis of tools:

1. Architecture
   - Single loop design
   - Self-cloning: https://example.com/architecture

2. Performance
   - Uses small model: https://anthropic.com/haiku
   - Fast execution

Check it out: https://claude.ai"""

    text_clean, extracted_links = extract_links_from_text(formatted_text)
    posts = split_text_into_posts(text_clean, 280)

    # Should preserve numbered lists and indentation
    full_text = " ".join(posts) if len(posts) > 1 else posts[0]
    assert "1. Architecture" in full_text
    assert "2. Performance" in full_text
    assert "- Single loop design" in full_text
    assert "- Uses small model" in full_text

    # Should extract all links
    assert len(extracted_links) == 3
    expected_links = [
        "https://example.com/architecture",
        "https://anthropic.com/haiku",
        "https://claude.ai",
    ]
    assert extracted_links == expected_links


def test_blog_post_with_inline_img_tags():
    """Test that blog posts remove inline img tags and keep images only in frontmatter"""
    from scripts.update_links import (
        convert_issue_to_post,
        generate_markdown_content_inline,
        process_issue_text,
    )

    # Issue body with inline img tags (like GitHub issue #111)
    issue_body = """Must-read story on Common Crawl.

https://www.theatlantic.com/technology/article.html

<img width="678" height="200" alt="Screenshot 1" src="https://github.com/user-attachments/assets/image1.png" />

<img width="679" height="306" alt="Screenshot 2" src="https://github.com/user-attachments/assets/image2.png" />"""

    # Simulate the save_post flow
    # Step 1: Clean the text (remove img tags)
    markdown_text, extracted_images = process_issue_text(issue_body)

    # Step 2: Create url_to_filename mapping (simulating downloaded images)
    url_to_filename = {
        "https://github.com/user-attachments/assets/image1.png": "local1.png",
        "https://github.com/user-attachments/assets/image2.png": "local2.png",
    }

    # Step 3: Create post dict
    post = {
        "date": "2025-11-04T14:52:59+00:00",
        "text": "unused",
        "images": extracted_images,
        "hash": "111",
    }

    # Step 4: Generate markdown content
    markdown_content = generate_markdown_content_inline(
        post, markdown_text, url_to_filename
    )

    # Verify: No inline img tags in the body
    assert "<img" not in markdown_content
    assert "github.com/user-attachments/assets" not in markdown_content

    # Verify: Images are in frontmatter
    assert "images:" in markdown_content
    assert "- src: local1.png" in markdown_content
    assert 'alt: "Screenshot 1"' in markdown_content
    assert "- src: local2.png" in markdown_content
    assert 'alt: "Screenshot 2"' in markdown_content

    # Verify: Link is preserved in body
    assert "https://www.theatlantic.com/technology/article.html" in markdown_content
    assert "Must-read story on Common Crawl." in markdown_content

    # Verify: Text is after frontmatter delimiter
    lines = markdown_content.split("\n")
    # Find where frontmatter ends (second ---)
    frontmatter_end = 0
    dash_count = 0
    for i, line in enumerate(lines):
        if line == "---":
            dash_count += 1
            if dash_count == 2:
                frontmatter_end = i
                break

    body = "\n".join(lines[frontmatter_end + 1 :])
    assert "Must-read story on Common Crawl." in body
    assert "https://www.theatlantic.com/technology/article.html" in body
    assert "<img" not in body
