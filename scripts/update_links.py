#!/usr/bin/env python3

import json
import re
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict
from bs4 import BeautifulSoup
from github import Github
from atproto import Client, client_utils
import uuid
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()


class ImageInfo(TypedDict):
    """Represents an image with metadata"""

    src: str
    alt: Optional[str]


class Post(TypedDict):
    """Represents a post with metadata"""

    date: str
    text: str
    images: Optional[List[ImageInfo]]


# https://mastodon.social/api/v1/accounts/lookup?acct=kevinschaul
MASTODON_USER_ID = "112973733509746771"
BLUESKY_HANDLE = "kevinschaul.bsky.social"


def get_url_metadata(url: str) -> Dict[str, Optional[str]]:
    """Fetch metadata from a URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Try to get title in order of preference
        title = None

        # First try Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content")

        # Then try Twitter card title
        if not title:
            twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
            if twitter_title:
                title = twitter_title.get("content")

        # Finally fall back to HTML title tag
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.text.strip()

        return {"title": title}
    except Exception as e:
        print(f"Error fetching metadata for {url}: {e}")
        return {}


def process_issue_text(text: str) -> tuple[str, List[ImageInfo]]:
    """Extract images from text and return cleaned text and image info with alt text"""
    if not text:
        return text, []

    images = []
    cleaned_text = text

    # Process markdown image syntax: ![alt](url)
    markdown_pattern = r"!\[(.*?)\]\((https?://[^\s\)]+)\)"
    markdown_matches = re.findall(markdown_pattern, text)
    for alt_text, url in markdown_matches:
        images.append({"src": url, "alt": alt_text if alt_text else None})
    cleaned_text = re.sub(r"!\[.*?\]\([^\)]+\)", "", cleaned_text)

    # Process HTML img tags: extract both src and alt attributes
    # First extract all img tags
    img_tags = re.findall(r"<img[^>]*>", text, re.IGNORECASE)
    for img_tag in img_tags:
        # Extract src
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
        # Extract alt
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag, re.IGNORECASE)

        if src_match:
            src_url = src_match.group(1)
            alt_text = alt_match.group(1) if alt_match else None
            images.append({"src": src_url, "alt": alt_text})
    cleaned_text = re.sub(r"<img[^>]*>", "", cleaned_text, flags=re.IGNORECASE)

    # Process standalone GitHub asset URLs (not already in HTML tags)
    # These won't have alt text
    github_assets_pattern = (
        r'(?<!src=["\'])https://github\.com/user-attachments/assets/[^\s]+'
    )
    github_assets = re.findall(
        github_assets_pattern, cleaned_text
    )  # Use cleaned_text to avoid HTML duplicates
    for url in github_assets:
        images.append({"src": url, "alt": None})
    cleaned_text = re.sub(github_assets_pattern, "", cleaned_text)

    # Process standalone user-attachments URLs (not already in HTML tags)
    # These won't have alt text
    user_attachments_pattern = (
        r'(?<!src=["\'])https://user-images\.githubusercontent\.com/[^\s]+'
    )
    user_attachments = re.findall(
        user_attachments_pattern, cleaned_text
    )  # Use cleaned_text to avoid HTML duplicates
    for url in user_attachments:
        images.append({"src": url, "alt": None})
    cleaned_text = re.sub(user_attachments_pattern, "", cleaned_text)

    # Clean up extra whitespace and empty lines
    cleaned_text = re.sub(
        r"\n\s*\n", "\n\n", cleaned_text
    )  # Replace multiple newlines with double newlines
    cleaned_text = cleaned_text.strip()

    # Remove duplicate images based on src
    seen_srcs = set()
    unique_images = []
    for img in images:
        if img["src"] not in seen_srcs:
            unique_images.append(img)
            seen_srcs.add(img["src"])

    return cleaned_text, unique_images


def extract_images_from_issue(issue_body: str) -> List[str]:
    """Extract image URLs from GitHub issue markdown content (legacy function)"""
    _, images = process_issue_text(issue_body)
    return [img["src"] for img in images]


def remove_images_from_text(text: str) -> str:
    """Remove image HTML and markdown from text content (legacy function)"""
    cleaned_text, _ = process_issue_text(text)
    return cleaned_text


def download_image(image_url: str, dest_path: str) -> Optional[str]:
    """Download an image and save it to the specified path"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Authorization": (
                f"token {os.environ.get('GITHUB_TOKEN', '')}"
                if "github" in image_url
                else None
            ),
        }
        # Remove None values from headers
        headers = {k: v for k, v in headers.items() if v is not None}

        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Get file extension from URL or content type
        file_ext = ""
        if "." in image_url.split("/")[-1]:
            file_ext = "." + image_url.split("/")[-1].split(".")[-1].split("?")[0]
        elif response.headers.get("content-type"):
            content_type = response.headers["content-type"]
            if "jpeg" in content_type or "jpg" in content_type:
                file_ext = ".jpg"
            elif "png" in content_type:
                file_ext = ".png"
            elif "gif" in content_type:
                file_ext = ".gif"
            elif "webp" in content_type:
                file_ext = ".webp"

        if not file_ext:
            file_ext = ".jpg"  # Default fallback

        filename = f"{uuid.uuid4().hex}{file_ext}"
        full_path = os.path.join(dest_path, filename)

        with open(full_path, "wb") as f:
            f.write(response.content)

        return filename
    except Exception as e:
        print(f"Error downloading image {image_url}: {e}")
        return None


def should_skip_issue(issue) -> bool:
    """Check if an issue should be skipped based on labels"""
    label_names = [label.name for label in issue.labels]
    return "do-not-post" in label_names


def convert_issue_to_post(issue) -> Post:
    """Convert a GitHub issue to a Post object"""
    body = issue.body

    # Process text once to get both cleaned text and images
    text, images = process_issue_text(body)

    if images:
        print(f"Found {len(images)} images: {images}")

    return {
        "date": issue.created_at.isoformat(),
        "text": text,
        "images": images,
        "hash": f"{issue.number}",
    }


def process_github_issues(issues) -> List[Post]:
    """Process a list of GitHub issues and return Posts"""
    posts = []

    for issue in issues:
        if should_skip_issue(issue):
            continue

        post = convert_issue_to_post(issue)
        posts.append(post)

        # Close the issue since it's been processed
        issue.edit(state="closed")

    return posts


def get_posts_from_github() -> List[Post]:
    """Fetch posts from GitHub issues"""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])
    repo_owner = repo.owner.login

    issues = repo.get_issues(state="open", creator=repo_owner)
    return process_github_issues(issues)


def slugify(name: str) -> str:
    """
    Returns a valid filename by removing illegal characters
    https://github.com/django/django/blob/main/django/utils/text.py
    """
    s = str(name).strip().replace(" ", "_")
    s = s.replace("https://", "")
    s = s.replace("http://", "")
    s = s.replace("/", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise Exception("Could not derive file name from '%s'" % name)
    return s


def get_post_directory_path(post: Post, content_dir: str = "./content") -> str:
    """Generate the directory path for a post based on its content"""
    # Extract just the date part (YYYY-MM-DD) from the ISO timestamp
    date_part = post["date"].split("T")[0]
    slug = slugify(f"{date_part}_{post['text'][:30]}")
    return os.path.join(content_dir, "link", slug)


def generate_markdown_content(post: Post, downloaded_images: List[str] = None) -> str:
    """Generate the markdown content for a post"""
    content = ["---"]
    content.append(f"date: {post['date']}")

    if downloaded_images and post.get("images"):
        content.append("images:")
        # Create a mapping from original src to downloaded filename
        src_to_filename = {}
        if post["images"] and downloaded_images:
            # Match downloaded filenames to original srcs by order
            for i, downloaded_filename in enumerate(downloaded_images):
                if i < len(post["images"]):
                    src_to_filename[post["images"][i]["src"]] = downloaded_filename

        for image_info in post["images"]:
            downloaded_filename = src_to_filename.get(
                image_info["src"], image_info["src"]
            )
            content.append(f"  - src: {downloaded_filename}")
            if image_info.get("alt"):
                content.append(f"    alt: \"{image_info['alt']}\"")
    elif downloaded_images:
        # Fallback for backward compatibility when images is just a list of strings
        content.append("images:")
        for image in downloaded_images:
            content.append(f"  - src: {image}")

    content.append("---")
    content.append("")
    content.append(post["text"])

    return "\n".join(content)


def download_post_images(post: Post, dest_path: str) -> List[str]:
    """Download all images for a post and return the list of downloaded filenames"""
    downloaded_images = []
    if post.get("images"):
        for image_info in post["images"]:
            image_url = image_info["src"]
            downloaded_filename = download_image(image_url, dest_path)
            if downloaded_filename:
                downloaded_images.append(downloaded_filename)
                print(f"Downloaded image: {downloaded_filename}")
    return downloaded_images


def save_post(post: Post) -> None:
    print(f"Saving post: {json.dumps(post)}")

    post_dir = get_post_directory_path(post)

    # Save the post if it does not already exist
    if not os.path.isdir(post_dir):
        os.makedirs(post_dir)

        # Download images if any
        downloaded_images = download_post_images(post, post_dir)

        # Generate and write markdown content
        markdown_content = generate_markdown_content(post, downloaded_images)

        with open(os.path.join(post_dir, "index.md"), "w", encoding="utf-8") as f:
            f.write(markdown_content)

        post_to_mastodon(post, post_dir)
        post_to_bluesky(post, post_dir)


def search_similar_posts_mastodon(post: Post, token: str) -> bool:
    search_term = post["text"][:30]
    headers = {
        "Authorization": f"Bearer {token}",
    }

    try:
        statuses_url = (
            f"https://mastodon.social/api/v1/accounts/{MASTODON_USER_ID}/statuses"
        )
        params = {
            "limit": 20,
            "exclude_replies": True,
            "exclude_reblogs": True,
        }

        response = requests.get(
            statuses_url, headers=headers, params=params, timeout=10
        )
        response.raise_for_status()
        statuses = response.json()

        for status in statuses:
            import re

            plain_text = re.sub("<[^<]+?>", "", status.get("content", "")).lower()

            if search_term.lower() in plain_text:
                return True

        return False

    except requests.exceptions.RequestException as e:
        print(f"Error searching Mastodon for similar posts: {str(e)}")
        return True


def search_similar_posts_bluesky(post: Post, client: Client) -> bool:
    search_term = post["text"][:30]

    try:
        response = client.app.bsky.feed.get_author_feed(
            {"actor": BLUESKY_HANDLE, "limit": 20}
        )

        for feed_post in response.feed:
            if search_term.lower() in feed_post.post.record.text.lower():
                return True

        return False

    except Exception as e:
        print(f"Error searching Bluesky for similar posts: {str(e)}")
        return True  # Err on the side of caution


def upload_media_to_mastodon(
    image_path: str, token: str, alt_text: Optional[str] = None
) -> Optional[str]:
    """Upload an image to Mastodon and return the media ID"""
    url = "https://mastodon.social/api/v2/media"

    try:
        headers = {
            "Authorization": f"Bearer {token}",
        }

        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            data = {}
            if alt_text:
                data["description"] = alt_text

            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()

            media_data = response.json()
            return media_data.get("id")
    except Exception as e:
        print(f"Error uploading image {image_path} to Mastodon: {e}")
        return None


def post_to_mastodon(post: Post, post_dir: Optional[str] = None) -> None:
    url = "https://mastodon.social/api/v1/statuses"

    try:
        token = os.environ["MASTODON_ACCESS_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
        }

        # Check for similar posts
        if search_similar_posts_mastodon(post, token):
            print(
                f"Similar Mastodon post already exists for {post['text'][30:]}. Skipping."
            )
            return

        status = post["text"]
        media_ids = []

        # Upload images if they exist and we have a post directory
        if post.get("images") and post_dir and os.path.isdir(post_dir):
            # Get all downloaded image files
            image_files = [
                f
                for f in os.listdir(post_dir)
                if f.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
            ]

            # Upload each image (match by order since we download in order)
            for i, image_info in enumerate(post["images"]):
                if i < len(image_files):
                    image_path = os.path.join(post_dir, image_files[i])
                    media_id = upload_media_to_mastodon(
                        image_path, token, image_info.get("alt")
                    )
                    if media_id:
                        media_ids.append(media_id)

        data = {"status": status}
        if media_ids:
            data["media_ids[]"] = media_ids

        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        print(f"Successfully posted to Mastodon: {post['text']}")
        if media_ids:
            print(f"  with {len(media_ids)} images")
    except KeyError as e:
        print("Warning: Missing MASTODON_ACCESS_TOKEN, so not posting to Mastodon")
        print(e)
    except Exception as e:
        print(f"An error occurred while posting to Mastodon: {str(e)}")


def post_to_bluesky(post: Post, post_dir: Optional[str] = None) -> None:
    try:
        client = Client()
        client.login(BLUESKY_HANDLE, os.environ["BLUESKY_APP_PASSWORD"])

        # Check for similar posts
        if search_similar_posts_bluesky(post, client):
            print(f"Similar Bluesky post already exists for {post['text']}. Skipping.")
            return

        # Build text with clickable links
        tb = client_utils.TextBuilder()
        text = post["text"]
        url_pattern = r"https?://[^\s]+"

        # Split text by URLs and rebuild with proper links
        last_end = 0
        for match in re.finditer(url_pattern, text):
            # Add text before the URL
            if match.start() > last_end:
                tb.text(text[last_end : match.start()])

            # Add the URL as a link
            url = match.group()
            tb.link(url, url)
            last_end = match.end()

        # Add any remaining text after the last URL
        if last_end < len(text):
            tb.text(text[last_end:])

        # Upload images if they exist and we have a post directory
        images_to_embed = []
        if post.get("images") and post_dir and os.path.isdir(post_dir):
            # Get all downloaded image files
            image_files = [
                f
                for f in os.listdir(post_dir)
                if f.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
            ]

            # Upload each image (match by order since we download in order)
            for i, image_info in enumerate(post["images"]):
                if i < len(image_files):
                    image_path = os.path.join(post_dir, image_files[i])
                    try:
                        with open(image_path, "rb") as image_file:
                            image_data = image_file.read()

                        # Get image dimensions for aspect ratio
                        with Image.open(io.BytesIO(image_data)) as img:
                            width, height = img.size
                            aspect_ratio = {"width": width, "height": height}

                        # Upload the image to Bluesky
                        upload_response = client.upload_blob(image_data)

                        # Create image embed with alt text and aspect ratio
                        image_embed = {
                            "alt": image_info.get("alt", ""),
                            "image": upload_response.blob,
                            "aspectRatio": aspect_ratio,
                        }
                        images_to_embed.append(image_embed)
                    except Exception as e:
                        print(f"Error uploading image {image_path} to Bluesky: {e}")

        # Send the post with embedded images
        if images_to_embed:
            client.send_post(
                tb, embed={"$type": "app.bsky.embed.images", "images": images_to_embed}
            )
        else:
            client.send_post(tb)

        print(f"Successfully posted to Bluesky: {post['text']}")
        if images_to_embed:
            print(f"  with {len(images_to_embed)} images")
    except KeyError as e:
        print("Warning: Missing BLUESKY_APP_PASSWORD, so not posting to Bluesky")
        print(e)
    except Exception as e:
        print(f"An error occurred while posting to Bluesky: {str(e)}")


def main() -> None:
    posts = get_posts_from_github()
    print(f"Found {len(posts)} posts.")
    for post in posts:
        save_post(post)


if __name__ == "__main__":
    main()
