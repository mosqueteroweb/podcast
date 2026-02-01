import os
import logging
from src.audio_processor import get_channel_info, download_audio
from src.feed_generator import generate_feed
from src.github_client import GitHubClient
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CHANNELS_FILE = "channels.txt"
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
YOUTUBE_COOKIES = os.getenv("YOUTUBE_COOKIES")
MAX_EPISODES = 5
COOKIE_FILE = "cookies.txt"

def main():
    if not GITHUB_REPO or not GITHUB_TOKEN:
        logger.error("GITHUB_REPOSITORY and GITHUB_TOKEN environment variables must be set.")
        return

    logger.info(f"Starting podcast feed update for repo: {GITHUB_REPO}")

    # Write cookies to file if secret is present
    if YOUTUBE_COOKIES:
        with open(COOKIE_FILE, "w") as f:
            f.write(YOUTUBE_COOKIES)
        logger.info("Cookies loaded from secret.")
    else:
        logger.warning("YOUTUBE_COOKIES secret not found. YouTube might block requests.")

    # Initialize GitHub Client
    gh_client = GitHubClient(GITHUB_TOKEN, GITHUB_REPO)
    release = gh_client.get_or_create_release(tag_name="downloads")

    if not release:
        logger.error("Failed to get or create release. Exiting.")
        return

    # Read channels
    if not os.path.exists(CHANNELS_FILE):
        logger.error(f"{CHANNELS_FILE} not found.")
        return

    with open(CHANNELS_FILE, 'r') as f:
        channels = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    for channel_url in channels:
        try:
            process_channel(channel_url, gh_client, release)
        except Exception as e:
            logger.error(f"Critical error processing channel {channel_url}: {e}")

    # Cleanup cookies
    if os.path.exists(COOKIE_FILE):
        os.remove(COOKIE_FILE)

def process_channel(channel_url, gh_client, release):
    logger.info(f"Processing channel: {channel_url}")

    # 1. Get Channel Info and latest videos
    cookie_path = COOKIE_FILE if os.path.exists(COOKIE_FILE) else None
    channel_info = get_channel_info(channel_url, limit=MAX_EPISODES, cookiefile=cookie_path)
    if not channel_info:
        logger.warning(f"Skipping channel {channel_url} due to error (could not fetch info).")
        return

    if not channel_info.get('entries'):
        logger.warning(f"Channel {channel_url} found but has no videos/entries.")
        return

    # Prepare episode list for the feed
    # Ideally, we should persist this state. For now, we regenerate based on what's available
    # or what we just downloaded.
    # To keep it stateless but functional:
    # We will try to download the latest X videos.
    # If they already exist in the Release, we get their URL.
    # If not, we download and upload them.

    episodes_for_feed = []

    # Helper to clean channel name for file naming (simple version)
    # Using Channel ID to avoid collisions if two channels have the same name
    channel_name_slug = channel_info['id']

    # Identify current assets in release to avoid re-uploading if not needed
    existing_assets = gh_client.list_assets(release)

    for video in channel_info['entries']:
        video_id = video['id']
        video_url = video['url']

        if not video_id or not video_url:
            logger.warning(f"Skipping video with missing ID or URL: {video}")
            continue

        # Unique filename: CHANNEL_SLUG_VIDEOID.mp3
        filename = f"{channel_name_slug}_{video_id}.mp3"

        # Check if asset exists in release
        if filename in existing_assets:
            logger.info(f"File {filename} already exists in Release.")
            asset = existing_assets[filename]
            download_url = asset.browser_download_url
            file_size = asset.size

        else:
            # Download and Upload
            logger.info(f"Downloading new episode: {video['title']}")
            cookie_path = COOKIE_FILE if os.path.exists(COOKIE_FILE) else None
            result = download_audio(video_url, cookiefile=cookie_path)

            if result:
                # Rename file to our unique format
                original_path = result['filepath']
                new_path = os.path.join(os.path.dirname(original_path), filename)
                os.rename(original_path, new_path)

                # Upload
                download_url = gh_client.upload_asset(release, new_path)

                if download_url:
                    file_size = os.path.getsize(new_path)

                    # Cleanup local file
                    os.remove(new_path)
                else:
                    logger.error(f"Failed to upload {filename}")
                    continue
            else:
                logger.error(f"Failed to download {video['url']}")
                continue

        # Add to feed list
        episodes_for_feed.append({
            'id': video_id,
            'title': video['title'],
            'description': video['description'],
            'original_url': video['url'],
            'download_url': download_url,
            'file_size': file_size,
            'upload_date': video['upload_date']
        })

    # Generate Feed XML
    # Feed filename: CHANNEL_SLUG.xml
    feed_filename = f"{channel_name_slug}.xml"
    generate_feed(channel_info, episodes_for_feed, feed_filename, repo_url=f"https://github.com/{GITHUB_REPO}")

    # We leave the XML files in the root (or specific folder) so the git commit step picks them up.

    # Cleanup Old Episodes (Logic: Logic is per-channel, but Release is global)
    # This is tricky because "latest 5" is per channel.
    # To do this safely:
    # 1. We know the filenames of the "active" episodes we just processed: [e['id'] for e in episodes_for_feed]
    # 2. We can list all assets starting with `channel_name_slug_`
    # 3. Delete those that are NOT in the active list.

    active_filenames = [f"{channel_name_slug}_{ep['id']}.mp3" for ep in episodes_for_feed]

    for asset_name in existing_assets:
        if asset_name.startswith(f"{channel_name_slug}_") and asset_name.endswith(".mp3"):
            if asset_name not in active_filenames:
                logger.info(f"Cleaning up old episode: {asset_name}")
                gh_client.delete_asset(release, asset_name)

if __name__ == "__main__":
    main()
