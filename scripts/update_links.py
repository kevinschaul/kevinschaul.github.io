#!/usr/bin/env python3

import re
import os
import requests
import time
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

MASTODON_CHAR_LIMIT = 500
BLUESKY_CHAR_LIMIT = 300
X_CHAR_LIMIT = 280


def get_url_metadata(url: str) -> Dict[str, Optional[str]]:
    """Fetch metadata from a URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        def find_meta(property=None, name=None):
            tag = (
                soup.find("meta", property=property)
                if property
                else soup.find("meta", attrs={"name": name})
            )
            return tag.get("content") if tag else None

        # Get title: og:title -> twitter:title -> <title>
        title = (
            find_meta(property="og:title")
            or find_meta(name="twitter:title")
            or (soup.find("title").text.strip() if soup.find("title") else None)
        )

        # Get description: og:description -> twitter:description -> description
        description = (
            find_meta(property="og:description")
            or find_meta(name="twitter:description")
            or find_meta(name="description")
        )

        return {"title": title, "description": description}
    except Exception as e:
        print(f"Error fetching metadata for {url}: {e}")
        return {}


def create_bluesky_link_card(url: str) -> Optional[Dict]:
    """Create a Bluesky external link embed from URL metadata"""
    metadata = get_url_metadata(url)
    if not metadata.get("title"):
        return None

    return {
        "$type": "app.bsky.embed.external",
        "external": {
            "uri": url,
            "title": metadata["title"],
            "description": metadata.get("description", ""),
        },
    }


def download_images_for_post(post: Post, post_dir: str) -> List[str]:
    """Download images for a post and return list of local paths"""
    if not post.get("images"):
        return []

    os.makedirs(post_dir, exist_ok=True)
    image_paths = []

    for image_info in post["images"]:
        filename = download_image(image_info["src"], post_dir)
        if filename:
            image_paths.append(os.path.join(post_dir, filename))

    return image_paths


def build_bluesky_text_with_links(
    text: str,
) -> tuple[client_utils.TextBuilder, Optional[str]]:
    """
    Build Bluesky TextBuilder with clickable links

    Returns:
        (TextBuilder with text and links, first URL found or None)
    """
    tb = client_utils.TextBuilder()
    url_pattern = r"https?://[^\s]+"
    first_url = None
    last_end = 0

    for match in re.finditer(url_pattern, text):
        if first_url is None:
            first_url = match.group()

        if match.start() > last_end:
            tb.text(text[last_end : match.start()])

        url = match.group()
        tb.link(url, url)
        last_end = match.end()

    if last_end < len(text):
        tb.text(text[last_end:])

    return tb, first_url


def parse_thread_sections(text: str) -> List[Dict]:
    """
    Split issue body by markdown horizontal rules (---, ***, ___) into thread sections.

    Returns:
        List of dicts with 'text' and 'images' keys for each section
    """
    if not text:
        return [{"text": "", "images": []}]

    import re

    separator_pattern = r"\n(?:---+|\*\*\*+|___+)\n"
    sections_text = re.split(separator_pattern, text)

    sections = []
    for section_text in sections_text:
        cleaned_text, images = process_issue_text(section_text)
        sections.append({"text": cleaned_text, "images": images})

    return sections


def process_issue_text(text: str) -> tuple[str, List[ImageInfo]]:
    """Extract images from text and return cleaned text and image info with alt text"""
    if not text:
        return text, []

    images = []
    cleaned_text = text

    markdown_pattern = r"!\[(.*?)\]\((https?://[^\s\)]+)\)"
    markdown_matches = re.findall(markdown_pattern, text)
    for alt_text, url in markdown_matches:
        images.append({"src": url, "alt": alt_text if alt_text else None})
    cleaned_text = re.sub(r"!\[.*?\]\([^\)]+\)", "", cleaned_text)

    img_tags = re.findall(r"<img[^>]*>", text, re.IGNORECASE)
    for img_tag in img_tags:
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag, re.IGNORECASE)
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag, re.IGNORECASE)

        if src_match:
            src_url = src_match.group(1)
            alt_text = alt_match.group(1) if alt_match else None
            images.append({"src": src_url, "alt": alt_text})
    cleaned_text = re.sub(r"<img[^>]*>", "", cleaned_text, flags=re.IGNORECASE)

    github_assets_pattern = (
        r'(?<!src=["\'])https://github\.com/user-attachments/assets/[^\s]+'
    )
    github_assets = re.findall(github_assets_pattern, cleaned_text)
    for url in github_assets:
        images.append({"src": url, "alt": None})
    cleaned_text = re.sub(github_assets_pattern, "", cleaned_text)

    user_attachments_pattern = (
        r'(?<!src=["\'])https://user-images\.githubusercontent\.com/[^\s]+'
    )
    user_attachments = re.findall(user_attachments_pattern, cleaned_text)
    for url in user_attachments:
        images.append({"src": url, "alt": None})
    cleaned_text = re.sub(user_attachments_pattern, "", cleaned_text)

    cleaned_text = re.sub(r"\n\s*\n", "\n\n", cleaned_text)
    cleaned_text = cleaned_text.strip()

    seen_srcs = set()
    unique_images = []
    for img in images:
        if img["src"] not in seen_srcs:
            unique_images.append(img)
            seen_srcs.add(img["src"])

    return cleaned_text, unique_images


def process_issue_text_for_blog(text: str, url_to_filename: Dict[str, str]) -> str:
    """Replace image URLs with local filenames and convert plain URLs to titled links in blog text"""
    if not text:
        return text

    result = text

    # Replace image URLs with local filenames
    for url, local_filename in url_to_filename.items():
        result = result.replace(url, local_filename)

    # Convert plain URLs to titled links for blog posts
    # Match URLs that aren't already in markdown link format
    url_pattern = r'(?<!\]\()https?://[^\s)]+(?!\))'

    def replace_with_titled_link(match):
        url = match.group(0)
        # Clean up any trailing punctuation
        url = re.sub(r'[.,;:!?]+$', '', url)

        # Fetch metadata for the URL
        metadata = get_url_metadata(url)
        title = metadata.get('title')

        if title:
            return f"\n\n[{title}]({url})"
        else:
            # If we can't get a title, keep the plain URL
            return url

    result = re.sub(url_pattern, replace_with_titled_link, result)
    return result


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
        headers = {k: v for k, v in headers.items() if v is not None}

        response = requests.get(image_url, headers=headers, timeout=30)
        response.raise_for_status()

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
            file_ext = ".jpg"

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


def get_excluded_platforms(issue) -> List[str]:
    """
    Get list of platforms to exclude based on issue labels

    Labels:
    - exclude-blog: Skip Hugo blog
    - exclude-mastodon: Skip Mastodon
    - exclude-x: Skip X/Twitter
    - exclude-bluesky: Skip Bluesky

    Returns:
        List of platform names to exclude
    """
    label_names = [label.name for label in issue.labels]
    excluded = []

    platform_labels = {
        "exclude-blog": "blog",
        "exclude-mastodon": "mastodon",
        "exclude-x": "x",
        "exclude-bluesky": "bluesky",
    }

    for label, platform in platform_labels.items():
        if label in label_names:
            excluded.append(platform)

    return excluded


def convert_issue_to_post(issue, for_social: bool = False):
    """
    Convert a GitHub issue to Post object(s)

    Args:
        issue: GitHub issue object
        for_social: If True, return list of posts for threading on social media
                   If False, return single merged post for Hugo blog

    Returns:
        If for_social=True: List[Post] with thread metadata
        If for_social=False: Single Post dict with merged content
    """
    body = issue.body
    sections = parse_thread_sections(body)

    if not for_social:
        all_text = "\n\n".join(section["text"] for section in sections)
        all_images = []
        for section in sections:
            all_images.extend(section["images"])

        if all_images:
            print(f"Found {len(all_images)} images: {all_images}")

        original_body = re.sub(r"\n(?:---+|\*\*\*+|___+)\n", "\n\n", body)

        return {
            "date": issue.created_at.isoformat(),
            "text": all_text,
            "images": all_images,
            "hash": f"{issue.number}",
            "original_body": original_body,
        }
    else:
        posts = []
        for i, section in enumerate(sections):
            if section["images"]:
                print(
                    f"Section {i + 1}: Found {len(section['images'])} images: {section['images']}"
                )

            posts.append(
                {
                    "date": issue.created_at.isoformat(),
                    "text": section["text"],
                    "images": section["images"],
                    "hash": f"{issue.number}",
                    "thread_index": i,
                    "thread_total": len(sections),
                }
            )

        return posts


def process_github_issues(issues, for_social: bool = False):
    """
    Process a list of GitHub issues and return Posts

    Args:
        issues: List of GitHub issue objects
        for_social: If True, return thread posts for social media
                   If False, return merged posts for Hugo blog

    Returns:
        List of Post dicts (or list of list of Posts if for_social=True)
    """
    results = []

    for issue in issues:
        if should_skip_issue(issue):
            continue

        post_or_posts = convert_issue_to_post(issue, for_social=for_social)
        results.append((issue, post_or_posts))

    return results


def get_issues_from_github(issue_id: Optional[int] = None):
    """Fetch issues from GitHub"""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])
    repo_owner = repo.owner.login

    if issue_id:
        try:
            issue = repo.get_issue(issue_id)
            if issue.user.login == repo_owner:
                return [issue]
            else:
                print(f"Issue #{issue_id} was not created by repo owner {repo_owner}")
                return []
        except Exception as e:
            print(f"Error fetching issue #{issue_id}: {e}")
            return []
    else:
        issues = list(repo.get_issues(state="open", creator=repo_owner))
        return issues


def get_post_url(post: Post) -> str:
    """Generate the URL for a post on kschaul.com"""
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

    if len(text) <= char_limit:
        return text

    link_suffix = f"... {post_url}"
    available_chars = char_limit - len(link_suffix)

    if available_chars > 0:
        truncated = text[:available_chars]
        last_space = truncated.rfind(" ")
        if last_space > available_chars * 0.7:
            truncated = truncated[:last_space]

        return truncated + link_suffix

    return post_url


def extract_links_from_text(text: str) -> tuple[str, List[str]]:
    """Extract URLs from text and return (text_without_links, list_of_links)"""
    url_pattern = r"https?://[^\s]+"
    raw_links = re.findall(url_pattern, text)

    links = []
    for link in raw_links:
        cleaned_link = re.sub(r"[.,;:!?]+$", "", link)
        links.append(cleaned_link)

    text_without_links = re.sub(url_pattern, "", text)
    text_without_links = re.sub(r"[ \t]+", " ", text_without_links)
    text_without_links = re.sub(r" *\n *", "\n", text_without_links)
    text_without_links = re.sub(r"\n{3,}", "\n\n", text_without_links)
    text_without_links = text_without_links.strip()

    return text_without_links, links


def split_text_into_posts(text: str, char_limit: int) -> List[str]:
    """Split long text into multiple posts for threading"""
    if len(text) <= char_limit:
        return [text]

    thread_indicator_space = 7
    effective_limit = char_limit - thread_indicator_space

    paragraphs = text.split("\n\n")
    posts = []
    current_post = ""

    for paragraph in paragraphs:
        if current_post and len(current_post + "\n\n" + paragraph) > effective_limit:
            posts.append(current_post.strip())
            current_post = paragraph
        elif not current_post:
            current_post = paragraph
        else:
            current_post += "\n\n" + paragraph

        if len(current_post) > effective_limit:
            if posts or len(current_post.split("\n\n")) > 1:
                parts = current_post.split("\n\n")
                if len(parts) > 1:
                    current_post = "\n\n".join(parts[:-1])
                    posts.append(current_post.strip())
                    oversized_paragraph = parts[-1]
                else:
                    oversized_paragraph = current_post
                    current_post = ""
            else:
                oversized_paragraph = current_post
                current_post = ""

            sentences = re.split(r"(?<=[.!?])\s+", oversized_paragraph)
            temp_post = ""

            for sentence in sentences:
                if temp_post and len(temp_post + " " + sentence) > effective_limit:
                    posts.append(temp_post.strip())
                    temp_post = sentence
                elif not temp_post:
                    temp_post = sentence
                else:
                    temp_post += " " + sentence

                if len(temp_post) > effective_limit:
                    words = temp_post.split()
                    if len(words) > 1:
                        posts.append(" ".join(words[:-1]))
                        temp_post = words[-1]
                    else:
                        posts.append(temp_post[:effective_limit])
                        temp_post = temp_post[effective_limit:]

            current_post = temp_post

    if current_post.strip():
        posts.append(current_post.strip())

    if len(posts) > 1:
        total_posts = len(posts)
        for i in range(len(posts)):
            posts[i] = f"({i + 1}/{total_posts}) {posts[i]}"

    return posts


def get_post_directory_path(post: Post, content_dir: str = "./content") -> str:
    """Generate the directory path for a post based on its content"""
    date_part = post["date"].split("T")[0]
    slug = slugify(f"{date_part}_{post['text'][:30]}")
    return os.path.join(content_dir, "link", slug)


def generate_markdown_content(post: Post, downloaded_images: List[str] = None) -> str:
    """Generate the markdown content for a post (legacy with images in frontmatter)"""
    content = ["---"]
    content.append(f"date: {post['date']}")

    if downloaded_images and post.get("images"):
        src_to_filename = {}
        if post["images"] and downloaded_images:
            for i, downloaded_filename in enumerate(downloaded_images):
                if i < len(post["images"]):
                    src_to_filename[post["images"][i]["src"]] = downloaded_filename

        content.append("images:")
        for image_info in post["images"]:
            downloaded_filename = src_to_filename.get(
                image_info["src"], image_info["src"]
            )
            content.append(f"  - {downloaded_filename}")

        resources = []
        for image_info in post["images"]:
            downloaded_filename = src_to_filename.get(
                image_info["src"], image_info["src"]
            )
            if image_info.get("alt"):
                resources.append((downloaded_filename, image_info["alt"]))
        if resources:
            content.append("resources:")
            for filename, alt in resources:
                content.append(f"  - src: {filename}")
                content.append(f"    params:")
                content.append(f'      alt: "{alt}"')
    elif downloaded_images:
        content.append("images:")
        for image in downloaded_images:
            content.append(f"  - {image}")

    content.append("---")
    content.append("")
    content.append(post["text"])

    return "\n".join(content)


def generate_markdown_content_inline(
    post: Post, markdown_text: str, url_to_filename: Dict[str, str]
) -> str:
    """Generate markdown with inline images and frontmatter images for Hugo template"""
    content = ["---"]
    content.append(f"date: {post['date']}")

    if post.get("images") and url_to_filename:
        content.append("images:")
        for image_info in post["images"]:
            local_filename = url_to_filename.get(image_info["src"])
            if local_filename:
                content.append(f"  - {local_filename}")

        resources = []
        for image_info in post["images"]:
            local_filename = url_to_filename.get(image_info["src"])
            if local_filename and image_info.get("alt"):
                resources.append((local_filename, image_info["alt"]))
        if resources:
            content.append("resources:")
            for filename, alt in resources:
                content.append(f"  - src: {filename}")
                content.append(f"    params:")
                content.append(f'      alt: "{alt}"')

    content.append("---")
    content.append("")
    content.append(markdown_text)

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


def save_post(
    post: Post,
    test_mode: bool = False,
    force: bool = False,
    specific_issue: bool = False,
) -> str:
    """
    Save post to Hugo blog

    Returns:
        Path to the post directory
    """
    print("Saving blog post...")

    post_dir = get_post_directory_path(post)

    post_exists = os.path.isdir(post_dir)
    should_save = not post_exists or force or specific_issue

    if should_save:
        if not test_mode:
            if not post_exists:
                os.makedirs(post_dir)
            else:
                if force:
                    print(
                        f"Post directory already exists at {post_dir}, but force=True so reposting..."
                    )
                elif specific_issue:
                    print(
                        f"Post directory already exists at {post_dir}, but specific issue requested so reposting..."
                    )

            url_to_filename = {}
            if post.get("images"):
                for image_info in post["images"]:
                    image_url = image_info["src"]
                    downloaded_filename = download_image(image_url, post_dir)
                    if downloaded_filename:
                        url_to_filename[image_url] = downloaded_filename
                        print(f"Downloaded image: {downloaded_filename}")

            if post.get("original_body"):
                # First clean the text (remove img tags, etc) but keep links
                markdown_text, _ = process_issue_text(post["original_body"])
                # Convert plain URLs to titled links for blog posts
                markdown_text = process_issue_text_for_blog(markdown_text, {})
                markdown_content = generate_markdown_content_inline(
                    post, markdown_text, url_to_filename
                )
            else:
                downloaded_images = list(url_to_filename.values())
                markdown_content = generate_markdown_content(post, downloaded_images)

            with open(os.path.join(post_dir, "index.md"), "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print(f"✓ Saved blog post to {post_dir}")
        else:
            print(f"TEST MODE: Would save blog post to {post_dir}")
    else:
        print(f"Blog post already exists at {post_dir}. Use --force to overwrite.")

    return post_dir


def post_to_social_media(
    posts: List[Post],
    platforms: List[str],
    test_mode: bool = False,
    force: bool = False,
    specific_issue: bool = False,
) -> None:
    """
    Post a list of posts (thread) to social media platforms

    Args:
        posts: List of Post dicts with thread metadata
        platforms: List of platform names to post to
        test_mode: If True, only print what would be posted
        force: If True, post even if similar posts exist
        specific_issue: If True, specific issue was requested
    """
    if not posts:
        return

    first_post = posts[0]
    post_dir = get_post_directory_path(first_post)

    print(f"\nPosting thread ({len(posts)} post(s)) to social media...")

    if test_mode:
        print(f"TEST MODE: Would post to platforms: {platforms}")
        print(f"Thread has {len(posts)} posts")
        print()

        for i, post in enumerate(posts):
            print(f"--- Thread Post {i + 1}/{len(posts)} ---")
            print(f"Text: {post['text'][:100]}...")
            if post.get("images"):
                print(f"Images: {len(post['images'])} image(s)")
            print()

        return

    first_platform = True
    if "mastodon" in platforms:
        if not first_platform:
            print("Waiting 10 seconds before posting to next platform...")
            time.sleep(10)
        post_to_mastodon(posts, post_dir)
        first_platform = False
    if "x" in platforms:
        if not first_platform:
            print("Waiting 10 seconds before posting to next platform...")
            time.sleep(10)
        post_to_x(posts, post_dir)
        first_platform = False
    if "bluesky" in platforms:
        if not first_platform:
            print("Waiting 10 seconds before posting to next platform...")
            time.sleep(10)
        post_to_bluesky(posts, post_dir)
        first_platform = False


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
        tweets = client.get_users_tweets(
            id=user_id, max_results=20, exclude=["retweets", "replies"]
        )

        if tweets.data:
            for tweet in tweets.data:
                if search_term.lower() in tweet.text.lower():
                    return True

        return False

    except Exception as e:
        print(f"Error searching X for similar posts: {str(e)}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("Authentication issue in search - proceeding with post attempt")
            return False
        return True


def search_similar_posts_x(post: Post, api: tweepy.API) -> bool:
    """Check if a similar post already exists on X/Twitter"""
    search_term = post["text"][:30]

    try:
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
        media = api.media_upload(image_path)

        if alt_text:
            api.create_media_metadata(media_id=media.media_id, alt_text=alt_text)

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


def post_to_mastodon(posts: List[Post], post_dir: Optional[str] = None) -> None:
    """Post a thread to Mastodon"""
    try:
        token = os.environ["MASTODON_ACCESS_TOKEN"]
        headers = {"Authorization": f"Bearer {token}"}

        if posts and search_similar_posts_mastodon(posts[0], token):
            print("Similar Mastodon post already exists. Skipping.")
            return

        if post_dir:
            os.makedirs(post_dir, exist_ok=True)

        in_reply_to_id = None
        total_posted = 0

        for post in posts:
            media_ids = []
            image_paths = download_images_for_post(post, post_dir)
            for i, image_path in enumerate(image_paths):
                alt_text = (
                    post["images"][i].get("alt")
                    if i < len(post.get("images", []))
                    else None
                )
                media_id = upload_media_to_mastodon(image_path, token, alt_text)
                if media_id:
                    media_ids.append(media_id)

            for i, status_text in enumerate(
                split_text_into_posts(post["text"], MASTODON_CHAR_LIMIT)
            ):
                if total_posted > 0:
                    print("  Waiting 10 seconds before next post...")
                    time.sleep(10)

                data = {"status": status_text}
                if i == 0 and media_ids:
                    data["media_ids[]"] = media_ids
                if in_reply_to_id:
                    data["in_reply_to_id"] = in_reply_to_id

                response = requests.post(
                    "https://mastodon.social/api/v1/statuses",
                    headers=headers,
                    data=data,
                )
                response.raise_for_status()
                in_reply_to_id = response.json()["id"]
                total_posted += 1

        print(
            f"✓ Successfully posted to Mastodon as {total_posted} post(s) in a thread"
        )
    except KeyError:
        print("Warning: Missing MASTODON_ACCESS_TOKEN, so not posting to Mastodon")
    except Exception as e:
        print(f"An error occurred while posting to Mastodon: {str(e)}")


def post_to_x(posts: List[Post], post_dir: Optional[str] = None) -> None:
    """Post thread to X/Twitter - links from first post in replies, threads can have links in 2nd+ posts"""
    try:
        client = tweepy.Client(
            consumer_key=os.environ["X_CONSUMER_KEY"],
            consumer_secret=os.environ["X_CONSUMER_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
            wait_on_rate_limit=True,
        )
        auth = tweepy.OAuthHandler(
            os.environ["X_CONSUMER_KEY"], os.environ["X_CONSUMER_SECRET"]
        )
        auth.set_access_token(
            os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_TOKEN_SECRET"]
        )
        api = tweepy.API(auth, wait_on_rate_limit=True)

        if post_dir:
            os.makedirs(post_dir, exist_ok=True)

        all_links = []
        in_reply_to_tweet_id = None
        text_posts_count = 0
        is_thread = len(posts) > 1

        for post_index, post in enumerate(posts):
            if post_index == 0:
                text_to_post, links = extract_links_from_text(post["text"])
                all_links.extend(links)
            elif is_thread:
                text_to_post = post["text"]
            else:
                text_to_post, links = extract_links_from_text(post["text"])
                all_links.extend(links)

            media_ids = []
            image_paths = download_images_for_post(post, post_dir)[:4]
            for i, image_path in enumerate(image_paths):
                alt_text = (
                    post["images"][i].get("alt")
                    if i < len(post.get("images", []))
                    else None
                )
                media_id = upload_media_to_x(image_path, api, alt_text)
                if media_id:
                    media_ids.append(media_id)

            for i, status_text in enumerate(
                split_text_into_posts(text_to_post, X_CHAR_LIMIT)
            ):
                if text_posts_count > 0:
                    print("  Waiting 10 seconds before next post...")
                    time.sleep(10)

                kwargs = {"text": status_text}
                if i == 0 and media_ids:
                    kwargs["media_ids"] = media_ids
                if in_reply_to_tweet_id:
                    kwargs["in_reply_to_tweet_id"] = in_reply_to_tweet_id

                response = client.create_tweet(**kwargs)
                in_reply_to_tweet_id = response.data["id"]
                text_posts_count += 1

        for link in all_links:
            print("  Waiting 10 seconds before next post...")
            time.sleep(10)

            response = client.create_tweet(
                text=link, in_reply_to_tweet_id=in_reply_to_tweet_id
            )
            in_reply_to_tweet_id = response.data["id"]

        total = text_posts_count + len(all_links)
        print(f"✓ Successfully posted to X as {total} post(s) in a thread")
        if all_links:
            print(f"  ({text_posts_count} text posts + {len(all_links)} link replies)")
    except KeyError:
        print("Warning: Missing X API credentials, so not posting to X")
    except Exception as e:
        print(f"An error occurred while posting to X: {str(e)}")


def post_to_bluesky(posts: List[Post], post_dir: Optional[str] = None) -> None:
    """Post thread to Bluesky with images or link cards"""
    try:
        client = Client()
        client.login(BLUESKY_HANDLE, os.environ["BLUESKY_APP_PASSWORD"])

        if posts and search_similar_posts_bluesky(posts[0], client):
            print("Similar Bluesky post already exists. Skipping.")
            return

        if post_dir:
            os.makedirs(post_dir, exist_ok=True)

        reply_to = None
        total_posted = 0

        for post in posts:
            if total_posted > 0:
                print("  Waiting 10 seconds before next post...")
                time.sleep(10)

            tb, first_url = build_bluesky_text_with_links(post["text"])
            embed = None

            if post.get("images"):
                images_to_embed = []
                image_paths = download_images_for_post(post, post_dir)
                for i, image_path in enumerate(image_paths):
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()

                        with Image.open(io.BytesIO(image_data)) as img:
                            width, height = img.size

                        upload_response = client.upload_blob(image_data)
                        alt_text = (
                            post["images"][i].get("alt", "")
                            if i < len(post["images"])
                            else ""
                        )

                        images_to_embed.append(
                            {
                                "alt": alt_text,
                                "image": upload_response.blob,
                                "aspectRatio": {"width": width, "height": height},
                            }
                        )
                    except Exception as e:
                        print(f"Error uploading image to Bluesky: {e}")

                if images_to_embed:
                    embed = {
                        "$type": "app.bsky.embed.images",
                        "images": images_to_embed,
                    }

            elif first_url:
                embed = create_bluesky_link_card(first_url)

            kwargs = {"reply_to": reply_to} if reply_to else {}
            if embed:
                kwargs["embed"] = embed
            response = client.send_post(tb, **kwargs)

            reply_to = {
                "root": reply_to["root"]
                if reply_to
                else {"uri": response.uri, "cid": response.cid},
                "parent": {"uri": response.uri, "cid": response.cid},
            }
            total_posted += 1

        print(f"✓ Successfully posted to Bluesky as {total_posted} post(s) in a thread")
    except KeyError:
        print("Warning: Missing BLUESKY_APP_PASSWORD, so not posting to Bluesky")
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
        """,
    )

    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["blog", "mastodon", "x", "bluesky"],
        default=["blog", "mastodon", "x", "bluesky"],
        help="Platforms to post to (default: blog and all social platforms)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode - show what would be posted without actually posting",
    )

    parser.add_argument("--issue", type=int, help="Post specific GitHub issue by ID")

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reposting even if post already exists",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    issues = get_issues_from_github(issue_id=args.issue)
    print(f"Found {len(issues)} issue(s).")

    for issue in issues:
        excluded_platforms = get_excluded_platforms(issue)

        if excluded_platforms:
            print(
                f"Issue #{issue.number}: Excluding platforms based on labels: {excluded_platforms}"
            )

        active_platforms = [p for p in args.platforms if p not in excluded_platforms]

        if not active_platforms:
            print(f"Issue #{issue.number}: All platforms excluded by labels, skipping.")
            continue

        social_platforms = [p for p in active_platforms if p != "blog"]
        include_blog = "blog" in active_platforms

        if include_blog:
            blog_post = convert_issue_to_post(issue, for_social=False)
            save_post(
                blog_post,
                test_mode=args.test,
                force=args.force,
                specific_issue=args.issue is not None,
            )

        if social_platforms:
            social_posts = convert_issue_to_post(issue, for_social=True)
            post_to_social_media(
                social_posts,
                platforms=social_platforms,
                test_mode=args.test,
                force=args.force,
                specific_issue=args.issue is not None,
            )

        if not args.test:
            issue.edit(state="closed")


if __name__ == "__main__":
    main()
