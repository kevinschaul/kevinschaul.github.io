#!/usr/bin/env python3

import re
import os
import requests
from datetime import datetime, timedelta
from urllib import parse
from typing import Dict, List, Optional, TypedDict
from bs4 import BeautifulSoup
from github import Github
from atproto import Client


class Story(TypedDict):
    """Represents a link story with metadata"""

    title: str
    date: str  # ISO format date string
    url: str
    description: str
    hash: str  # Format: github-issue-{number}


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


def get_links_from_github() -> List[Story]:
    """Fetch links from GitHub issues"""
    links = []

    # Initialize GitHub client
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

    # Get repository owner (your GitHub username)
    repo_owner = repo.owner.login

    # Get all open issues with 'link' label, filtered by author
    issues = repo.get_issues(state="open", labels=["link"], creator=repo_owner)

    for issue in issues:
        # Extract the first URL from the issue body
        url = None
        for line in issue.body.split("\n"):
            if line.startswith("http://") or line.startswith("https://"):
                url = line.strip()
                break

        if not url:
            continue

        link = {
            "title": issue.title,
            "date": issue.created_at.isoformat(),
            "url": url,
            "description": issue.body.replace(url, "").strip(),
            "hash": f"github-issue-{issue.number}",
        }
        links.append(link)

        # Close the issue since it's been processed
        issue.edit(state="closed")

    return links


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


def save_link(story: Story) -> None:
    url = story["url"]
    parsed_url = parse.urlparse(url)
    # Remove querystring
    slugged_url = slugify(parsed_url.netloc + parsed_url.path)
    filename = os.path.join("./content", "link", slugged_url)

    metadata = get_url_metadata(url)

    # Save the link if it does not already exist
    if not os.path.isdir(filename):
        os.mkdir(filename)
        with open(os.path.join(filename, "index.md"), "w", encoding="utf-8") as f:
            title = metadata.get("title", story["title"])
            title = title.strip().replace('"', "")
            shared_date = story["date"]
            f.write("---\n")
            f.write(f'title: "{title}"\n')
            f.write(f"date: {shared_date}\n")
            f.write(f'external_url: "{url}"\n')
            f.write(f"tags: [link]\n")
            f.write("---\n\n")

            if story["description"]:
                f.write(story["description"])

        post_to_mastodon(story)
        post_to_bluesky(story)


def search_similar_posts_mastodon(story: Story, token: str) -> bool:
    search_url = "https://mastodon.social/api/v2/search"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    # Search for posts in the last 7 days
    since_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    params = {
        "q": story["url"],
        "type": "statuses",
        "account_id": MASTODON_USER_ID,
        "since_id": since_date,
    }
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        results = response.json()
        return len(results.get("statuses", [])) > 0
    except requests.exceptions.RequestException as e:
        print(f"Error searching Mastodon for similar posts: {str(e)}")
        return True


def search_similar_posts_bluesky(story: Story, client: Client) -> bool:
    # Search for posts in the last 7 days
    since_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    params = {
        "q": story["url"],
        "author": BLUESKY_HANDLE,
        "type": "statuses",
        "since": since_date,
    }
    try:
        results = client.app.bsky.feed.search_posts(params=params)
        return len(results.get("posts", [])) > 0
    except requests.exceptions.RequestException as e:
        print(f"Error searching Bluesky for similar posts: {str(e)}")
        return True


def post_to_mastodon(story: Story) -> None:
    url = "https://mastodon.social/api/v1/statuses/"

    try:
        token = os.environ["MASTODON_ACCESS_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": story["url"],
        }

        # Check for similar posts
        if search_similar_posts_mastodon(story, token):
            print(f"Similar Mastodon post already exists for {story['url']}. Skipping.")
            return

        status = story["url"]

        if story["description"]:
            status = story["description"] + " --> " + status

        data = {"status": status}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            print(f"Successfully posted to Mastodon: {story['url']}")
        else:
            print(f"Failed to post to Mastodon. Status code: {response.status_code}")
    except KeyError as e:
        print("Warning: Missing MASTODON_ACCESS_TOKEN, so not posting to Mastodon")
        print(e)
    except Exception as e:
        print(f"An error occurred while posting to Mastodon: {str(e)}")


def post_to_bluesky(story: Story) -> None:
    try:
        client = Client()
        client.login(BLUESKY_HANDLE, os.environ["BLUESKY_APP_PASSWORD"])

        # Check for similar posts
        if search_similar_posts_bluesky(story, client):
            print(f"Similar Bluesky post already exists for {story['url']}. Skipping.")
            return

        status = story["url"]

        if story["description"]:
            status = story["description"] + " --> " + status

        client.send_post(status)
        print(f"Successfully posted to Bluesky: {story['url']}")
    except KeyError as e:
        print("Warning: Missing BLUESKY_APP_PASSWORD, so not posting to Bluesky")
        print(e)
    except Exception as e:
        print(f"An error occurred while posting to Bluesky: {str(e)}")


def main() -> None:
    links = get_links_from_github()
    for link in links:
        save_link(link)


if __name__ == "__main__":
    main()
