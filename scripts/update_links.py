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
import tweepy
import argparse

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

# Character limits for social networks
MASTODON_CHAR_LIMIT = 500
BLUESKY_CHAR_LIMIT = 300
X_CHAR_LIMIT = 280


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


def get_posts_from_github(issue_id: Optional[int] = None) -> List[Post]:
    """Fetch posts from GitHub issues"""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])
    repo_owner = repo.owner.login

    if issue_id:
        # Get specific issue by ID
        try:
            issue = repo.get_issue(issue_id)
            if issue.user.login == repo_owner:
                return process_github_issues([issue])
            else:
                print(f"Issue #{issue_id} was not created by repo owner {repo_owner}")
                return []
        except Exception as e:
            print(f"Error fetching issue #{issue_id}: {e}")
            return []
    else:
        # Get all open issues
        issues = repo.get_issues(state="open", creator=repo_owner)
        return process_github_issues(issues)


def get_post_url(post: Post) -> str:
    """Generate the URL for a post on kschaul.com"""
    # Extract just the date part (YYYY-MM-DD) from the ISO timestamp
    date_part = post["date"].split("T")[0]
    slug = slugify(f"{date_part}_{post['text'][:30]}")
    return f"https://www.kschaul.com/link/{slug}/"


def slugify(name: str) -> str:
    """
    Returns a valid filename by removing illegal characters
    https://github.com/django/django/blob/main/django/utils/text.py
    """
    s = str(name).strip().replace(" ", "_").lower()
    s = s.replace("https://", "")
    s = s.replace("http://", "")
    s = s.replace("/", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise Exception("Could not derive file name from '%s'" % name)
    return s


def truncate_text_for_platform(post: Post, char_limit: int) -> str:
    """Truncate post text to fit platform character limit, adding link if needed"""
    text = post["text"]
    post_url = get_post_url(post)

    # If text fits within limit, return as-is
    if len(text) <= char_limit:
        return text

    # Calculate space needed for "... " + URL
    link_suffix = f"... {post_url}"
    available_chars = char_limit - len(link_suffix)

    # Find a good break point (prefer word boundaries)
    if available_chars > 0:
        truncated = text[:available_chars]
        # Try to break at word boundary
        last_space = truncated.rfind(' ')
        if last_space > available_chars * 0.7:  # Only use word boundary if it's not too short
            truncated = truncated[:last_space]

        return truncated + link_suffix

    # If even the URL is too long, just return the URL
    return post_url


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


def save_post(post: Post, platforms: List[str] = None, test_mode: bool = False, force: bool = False, specific_issue: bool = False) -> None:
    print(f"Saving post: {json.dumps(post)}")

    post_dir = get_post_directory_path(post)

    # Save the post if it does not already exist, if force is True, or if specific issue was requested
    post_exists = os.path.isdir(post_dir)
    should_post = not post_exists or force or specific_issue

    if should_post:
        if not post_exists:
            os.makedirs(post_dir)

            # Download images if any
            downloaded_images = download_post_images(post, post_dir)

            # Generate and write markdown content
            markdown_content = generate_markdown_content(post, downloaded_images)

            with open(os.path.join(post_dir, "index.md"), "w", encoding="utf-8") as f:
                f.write(markdown_content)
        else:
            if force:
                print(f"Post directory already exists, but force=True so posting anyway...")
            elif specific_issue:
                print(f"Post directory already exists, but specific issue requested so posting anyway...")

        # Post to selected platforms
        platforms = platforms or ["mastodon", "x", "bluesky"]

        if test_mode:
            print(f"TEST MODE: Would post to platforms: {platforms}")
            print(f"Post content: {post['text'][:100]}...")
            return

        if "mastodon" in platforms:
            post_to_mastodon(post, post_dir)
        if "x" in platforms:
            post_to_x(post, post_dir)
        if "bluesky" in platforms:
            post_to_bluesky(post, post_dir)
    else:
        print(f"Post already exists at {post_dir}. Use --force to repost.")


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


def search_similar_posts_x_v2(post: Post, client: tweepy.Client, user_id: str) -> bool:
    """Check if a similar post already exists on X/Twitter using v2 API"""
    search_term = post["text"][:30]

    try:
        # Get recent tweets from the user
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=20,
            exclude=['retweets', 'replies']
        )

        if tweets.data:
            for tweet in tweets.data:
                if search_term.lower() in tweet.text.lower():
                    return True

        return False

    except Exception as e:
        print(f"Error searching X for similar posts: {str(e)}")
        # If it's an auth error, don't skip posting - let the main post function handle auth
        if "401" in str(e) or "Unauthorized" in str(e):
            print("Authentication issue in search - proceeding with post attempt")
            return False
        return True  # Err on the side of caution for other errors


def search_similar_posts_x(post: Post, api: tweepy.API) -> bool:
    """Check if a similar post already exists on X/Twitter"""
    search_term = post["text"][:30]

    try:
        # Search for recent tweets from the authenticated user
        tweets = api.user_timeline(count=20, exclude_replies=True, include_rts=False)

        for tweet in tweets:
            if search_term.lower() in tweet.text.lower():
                return True

        return False

    except Exception as e:
        print(f"Error searching X for similar posts: {str(e)}")
        return True  # Err on the side of caution


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


def upload_media_to_x(
    image_path: str, api: tweepy.API, alt_text: Optional[str] = None
) -> Optional[str]:
    """Upload an image to X/Twitter using OAuth 1.0a and return the media ID"""
    try:
        # Upload media using the v1.1 API
        media = api.media_upload(image_path)

        # Add alt text if provided
        if alt_text:
            api.create_media_metadata(
                media_id=media.media_id,
                alt_text=alt_text
            )

        return str(media.media_id)
    except Exception as e:
        print(f"Error uploading image {image_path} to X: {e}")
        return None


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

        status = truncate_text_for_platform(post, MASTODON_CHAR_LIMIT)
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


def post_to_x(post: Post, post_dir: Optional[str] = None) -> None:
    """Post to X/Twitter"""
    try:
        # Set up X API client with OAuth 1.0a User Context
        client = tweepy.Client(
            consumer_key=os.environ["X_CONSUMER_KEY"],
            consumer_secret=os.environ["X_CONSUMER_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
            wait_on_rate_limit=True
        )

        # Set up v1.1 API for media uploads
        auth = tweepy.OAuthHandler(
            os.environ["X_CONSUMER_KEY"],
            os.environ["X_CONSUMER_SECRET"]
        )
        auth.set_access_token(
            os.environ["X_ACCESS_TOKEN"],
            os.environ["X_ACCESS_TOKEN_SECRET"]
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)

        # Skip duplicate checking for X (requires paid API access)

        status = truncate_text_for_platform(post, X_CHAR_LIMIT)
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
                if i < len(image_files) and len(media_ids) < 4:  # X allows max 4 images
                    image_path = os.path.join(post_dir, image_files[i])
                    media_id = upload_media_to_x(image_path, api, image_info.get("alt"))
                    if media_id:
                        media_ids.append(media_id)

        # Post the tweet using v2 API
        if media_ids:
            client.create_tweet(text=status, media_ids=media_ids)
        else:
            client.create_tweet(text=status)

        print(f"Successfully posted to X: {post['text']}")
        if media_ids:
            print(f"  with {len(media_ids)} images")
    except KeyError as e:
        print("Warning: Missing X API credentials, so not posting to X")
        print(e)
    except Exception as e:
        print(f"An error occurred while posting to X: {str(e)}")


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
        text = truncate_text_for_platform(post, BLUESKY_CHAR_LIMIT)
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


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Post GitHub issues to social media platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Post all open issues to all platforms
  python scripts/update_links.py

  # Test mode - don't actually post anything
  python scripts/update_links.py --test

  # Post only to X
  python scripts/update_links.py --platforms x

  # Post specific issue to X and Mastodon
  python scripts/update_links.py --issue 123 --platforms x mastodon

  # Test posting specific issue to X only
  python scripts/update_links.py --issue 123 --platforms x --test
        """
    )

    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["mastodon", "x", "bluesky"],
        default=["mastodon", "x", "bluesky"],
        help="Platforms to post to (default: all platforms)"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - show what would be posted without actually posting"
    )

    parser.add_argument(
        "--issue",
        type=int,
        help="Post specific GitHub issue by ID"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reposting even if post already exists"
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    posts = get_posts_from_github(issue_id=args.issue)
    print(f"Found {len(posts)} posts.")

    for post in posts:
        save_post(
            post,
            platforms=args.platforms,
            test_mode=args.test,
            force=args.force,
            specific_issue=args.issue is not None
        )


if __name__ == "__main__":
    main()
