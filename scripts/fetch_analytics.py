#!/usr/bin/env python3
"""
Fetch Bluesky analytics into a CSV report.
"""

import argparse
import csv
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from atproto import Client
from dotenv import load_dotenv

load_dotenv()

# Constants
BLUESKY_HANDLE = "kevinschaul.bsky.social"


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fetch Bluesky analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch last 30 days of analytics (default)
  python scripts/fetch_analytics.py

  # Fetch last 180 days (6 months)
  python scripts/fetch_analytics.py --days 180

  # Specify custom output directory
  python scripts/fetch_analytics.py --output ./data/analytics

  # Dry run to test API connection
  python scripts/fetch_analytics.py --dry-run
        """,
    )

    parser.add_argument(
        "--days", type=int, default=30, help="Number of days to fetch (default: 30)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./analytics",
        help="Output directory for CSV file (default: ./analytics)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test API connection without saving data",
    )

    return parser.parse_args()


def fetch_bluesky_analytics(days: int = 30) -> List[Dict]:
    """
    Fetch Bluesky post analytics for the last N days

    Returns:
        List of dicts with keys: date, platform, post_text, post_link,
        likes, reposts, replies, quotes, has_media, is_reply
    """
    client = Client()
    client.login(BLUESKY_HANDLE, os.environ["BLUESKY_APP_PASSWORD"])

    # Calculate date threshold
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Fetch author feed with pagination
    posts = []
    cursor = None

    while True:
        params = {"actor": BLUESKY_HANDLE, "limit": 100}
        if cursor:
            params["cursor"] = cursor
        response = client.app.bsky.feed.get_author_feed(params)

        for feed_item in response.feed:
            # Skip reposts - only include original posts
            if feed_item.reason:
                continue

            post = feed_item.post
            post_date = datetime.fromisoformat(
                post.record.created_at.replace("Z", "+00:00")
            )

            # Stop if we've gone past our date threshold
            if post_date < cutoff_date:
                return posts

            # Extract the post ID from the URI (last segment)
            post_id = post.uri.split("/")[-1]

            # Check for media attachments
            has_media = False
            if hasattr(post, "embed") and post.embed:
                # Check for images, videos, or other media
                embed_type = post.embed.py_type if hasattr(post.embed, "py_type") else ""
                has_media = "images" in embed_type or "video" in embed_type or "media" in embed_type

            # Check if this is a reply to another post
            is_reply = hasattr(post.record, "reply") and post.record.reply is not None

            # Extract engagement metrics
            posts.append(
                {
                    "date": post_date.date().isoformat(),
                    "platform": "bluesky",
                    "post_text": post.record.text[:100] if post.record.text else "",
                    "post_link": f"https://bsky.app/profile/{BLUESKY_HANDLE}/post/{post_id}",
                    "likes": post.like_count or 0,
                    "reposts": post.repost_count or 0,
                    "replies": post.reply_count or 0,
                    "quotes": post.quote_count or 0,
                    "has_media": has_media,
                    "is_reply": is_reply,
                }
            )

        # Check if there are more results
        if not response.cursor:
            break
        cursor = response.cursor

    return posts


def export_to_csv(
    data: List[Dict], start_date, end_date, output_dir: str = "./analytics"
) -> str:
    """Export analytics to CSV"""
    os.makedirs(output_dir, exist_ok=True)

    filename = f"analytics_{start_date}_to_{end_date}.csv"
    filepath = os.path.join(output_dir, filename)

    fieldnames = [
        "date",
        "platform",
        "post_text",
        "post_link",
        "likes",
        "reposts",
        "replies",
        "quotes",
        "has_media",
        "is_reply",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return filepath


def main():
    args = parse_args()

    # Calculate date range
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=args.days)

    print(f"Fetching Bluesky analytics from {start_date} to {end_date}\n")

    # Fetch data
    try:
        print("Fetching Bluesky analytics...")
        posts = fetch_bluesky_analytics(args.days)
        print(f"  Found {len(posts)} Bluesky posts\n")
    except KeyError as e:
        print(f"Error: Missing credentials: {e}")
        print("Please ensure BLUESKY_APP_PASSWORD is set in your .env file")
        return
    except Exception as e:
        print(f"Error fetching Bluesky analytics: {e}")
        return

    # Sort by date descending
    posts.sort(key=lambda x: x["date"], reverse=True)

    if args.dry_run:
        print("DRY RUN - Not saving to file")
        print(f"Would save {len(posts)} records")
        if posts:
            print("\nSample record:")
            print(json.dumps(posts[0], indent=2))
    else:
        # Export to CSV
        filepath = export_to_csv(posts, start_date, end_date, args.output)
        print(f"✓ Exported to {filepath}")


if __name__ == "__main__":
    main()
