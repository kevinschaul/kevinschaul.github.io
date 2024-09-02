#!/usr/bin/env python3

import re
import os
import requests
from datetime import datetime, timedelta
from urllib import parse

NEWSBLUR_USER_ID = 651620
NEWSBLUR_USER_NAME = "kasnewsblur"

# https://mastodon.social/api/v1/accounts/lookup?acct=kevinschaul
MASTODON_USER_ID = "112973733509746771"

url = (
    f"https://www.newsblur.com/social/stories/{NEWSBLUR_USER_ID}/{NEWSBLUR_USER_NAME}/"
)


def slugify(name):
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


def fix_encoding(text):
    """
    Attempt to fix encoding issues by assuming the text was originally UTF-8
    but was decoded incorrectly as Windows-1252 or ISO-8859-1.
    """
    # First, encode the string back to bytes assuming it was wrongly decoded as Windows-1252
    try:
        byte_string = text.encode("windows-1252")
        # Then decode those bytes as UTF-8
        return byte_string.decode("utf-8")
    except UnicodeEncodeError:
        # If that fails, try assuming it was wrongly decoded as ISO-8859-1
        try:
            byte_string = text.encode("iso-8859-1")
            return byte_string.decode("utf-8")
        except UnicodeEncodeError:
            # If both attempts fail, return the original string
            return text


def clean_title(title):
    title = title.strip()
    # Replace problematic characters
    title = fix_encoding(title)
    return title


def save_link(story):
    permalink = story["story_permalink"]
    parsed_url = parse.urlparse(permalink)
    # Remove querystring
    url = slugify(parsed_url.netloc + parsed_url.path)
    filename = os.path.join("./content", "link", url)

    # Save the link if it does not already exist
    if not os.path.isdir(filename):
        os.mkdir(filename)
        with open(os.path.join(filename, "index.md"), "w", encoding="utf-8") as f:
            story_title = clean_title(story["story_title"])
            shared_date = story["shared_date"]
            f.write("---\n")
            f.write(f'title: "{story_title}"\n')
            f.write(f"date: {shared_date}\n")
            f.write(f'external_url: "{permalink}"\n')
            f.write(f"tags: [link]\n")
            f.write("---\n\n")

            if story["user_id"] == NEWSBLUR_USER_ID:
                f.write(story["comments"])

        post_to_mastodon(story)


def search_similar_posts(story, token):
    search_url = "https://mastodon.social/api/v2/search"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    # Search for posts in the last 7 days
    since_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    params = {
        "q": story["story_permalink"],
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
        print(f"Error searching for similar posts: {str(e)}")
        return True


def post_to_mastodon(story):
    url = "https://mastodon.social/api/v1/statuses/"

    try:
        token = os.environ["MASTODON_ACCESS_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": story["story_permalink"],
        }

        # Check for similar posts
        if search_similar_posts(story, token):
            print(
                f"Similar post already exists for {story['story_permalink']}. Skipping."
            )
            return

        status = story["story_permalink"]

        if story["user_id"] == NEWSBLUR_USER_ID and story["comments"]:
            status = story["comments"] + " --> " + status

        data = {"status": status}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            print(f"Successfully posted to Mastodon: {story['story_permalink']}")
        else:
            print(f"Failed to post to Mastodon. Status code: {response.status_code}")
    except KeyError:
        print("Warning: Missing MASTODON_ACCESS_TOKEN, so not posting to Mastodon")
    except Exception as e:
        print(f"An error occurred while posting to Mastodon: {str(e)}")


def main():
    r = requests.get(url)
    data = r.json()

    for story in data["stories"]:
        save_link(story)


if __name__ == "__main__":
    main()
