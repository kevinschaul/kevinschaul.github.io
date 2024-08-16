#!/usr/bin/env python3

import re
import os
import requests
from urllib import parse

USER_ID = 651620
USER_NAME = "kasnewsblur"

url = f"https://www.newsblur.com/social/stories/{USER_ID}/{USER_NAME}/"


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


def save_link(story):
    permalink = story["story_permalink"]
    parsed_url = parse.urlparse(permalink)
    # Remove querystring
    url = slugify(parsed_url.netloc + parsed_url.path)
    filename = os.path.join("./content", "link", url)

    # Save the link if it does not already exist
    if not os.path.isdir(filename):
        os.mkdir(filename)
        with open(os.path.join(filename, "index.md"), "w") as f:
            story_title = story["story_title"].strip().replace('"', "")
            shared_date = story["shared_date"]
            f.write("---\n")
            f.write(f'title: "{story_title}"\n')
            f.write(f"date: {shared_date}\n")
            f.write(f'external_url: "{permalink}"\n')
            f.write(f'tags: [link]\n')
            f.write("---\n\n")

            if story["user_id"] == USER_ID:
                f.write(story["comments"])

        post_to_mastodon(story)


def post_to_mastodon(story):
    url = "https://mastodon.social/api/v1/statuses/"

    try:
        token = os.environ["MASTODON_ACCESS_TOKEN"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": story["story_permalink"],
        }

        status = story['story_permalink']

        if story["user_id"] == USER_ID and story["comments"]:
            status = story["comments"] + ' --> ' + status

        data = {
            'status': status
        }
        requests.post(url, headers=headers, data=data)
    except KeyError:
        print('Warning: Missing MASTODON_ACCESS_TOKEN, so not posting to mastodon')


def main():
    r = requests.get(url)
    data = r.json()

    for story in data["stories"]:
        save_link(story)


if __name__ == "__main__":
    main()
