from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def generate_feed(channel_info, episodes, output_file="feed.xml", repo_url=""):
    """
    Generates an RSS feed for a podcast.

    Args:
        channel_info (dict): Metadata about the channel (title, description, etc.)
        episodes (list): List of dicts containing episode info (title, url, size, etc.)
        output_file (str): Path to save the XML file.
        repo_url (str): Base URL for the GitHub repository (to construct file links if needed,
                        though episodes should already have direct download URLs).
    """
    fg = FeedGenerator()
    fg.load_extension('podcast')

    # Set basic feed metadata
    fg.title(channel_info.get('title', 'YouTube Podcast'))
    fg.description(channel_info.get('description', 'Audio feed generated from YouTube channel'))
    fg.link(href=channel_info.get('webpage_url', repo_url), rel='alternate')
    fg.language('en') # Default to en, but could be inferred

    # Podcast specific metadata
    fg.podcast.itunes_category('Technology') # Generic category
    fg.podcast.itunes_explicit('no')

    # Add episodes
    for ep in episodes:
        fe = fg.add_entry()
        fe.id(ep['id'])
        fe.title(ep['title'])
        fe.description(ep.get('description', ''))

        # Link to the video original URL as guidance
        fe.link(href=ep.get('original_url', ''), rel='alternate')

        # The enclosure is the most important part for a podcast
        # It must point to the direct audio file
        fe.enclosure(
            url=ep['download_url'],
            length=str(ep.get('file_size', 0)),
            type='audio/mpeg'
        )

        # Date handling
        if ep.get('upload_date'):
            try:
                # upload_date is usually YYYYMMDD
                dt = datetime.strptime(ep['upload_date'], '%Y%m%d')
                dt = dt.replace(tzinfo=timezone.utc)
                fe.pubDate(dt)
            except ValueError:
                fe.pubDate(datetime.now(timezone.utc))
        else:
             fe.pubDate(datetime.now(timezone.utc))

    try:
        fg.rss_file(output_file, pretty=True)
        logger.info(f"Feed generated successfully at {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate feed: {str(e)}")
        return False
