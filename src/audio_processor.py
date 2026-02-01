import yt_dlp
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_channel_info(channel_url, limit=5, cookiefile=None):
    """
    Fetches channel metadata and the latest videos.
    """
    ydl_opts = {
        'extract_flat': True,
        'playlistend': limit,
        'quiet': False,
        'ignoreerrors': True,
    }

    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Flatten playlists (handle tabs like Videos, Shorts)
            info = ydl.extract_info(channel_url, download=False)

            if not info:
                logger.error(f"Could not fetch info for {channel_url}")
                return None

            channel_data = {
                'id': info.get('id'),
                'title': info.get('title'),
                'uploader': info.get('uploader'),
                'description': info.get('description', ''),
                'webpage_url': info.get('webpage_url'),
                'entries': []
            }

            # Helper to flatten entries
            raw_entries = info.get('entries', [])
            flat_entries = []

            for entry in raw_entries:
                # If it's a playlist (like a tab), we might need to dig deeper
                # But typically extract_flat with a channel URL returns a mix or a playlist of playlists.
                # yt-dlp 2023+ handles /videos tab automatically if we just ask for the channel?
                # Actually, standard channel URL returns tabs.

                # Check if it is a video
                if entry.get('_type') == 'url' or entry.get('ie_key') == 'Youtube':
                    flat_entries.append(entry)
                elif entry.get('_type') == 'playlist':
                    # It's a nested playlist (like 'Videos' tab)
                    if 'entries' in entry:
                        flat_entries.extend(entry['entries'])

            # If flat_entries is still empty, maybe the raw_entries ARE the videos (older behavior)
            if not flat_entries and raw_entries:
                 # Check if the first item looks like a video
                 if raw_entries[0].get('id') and raw_entries[0].get('url'):
                     flat_entries = raw_entries

            # Limit and format
            for entry in flat_entries[:limit]:
                # Ensure we have a URL. In flat extraction, 'url' might be present,
                # or we construct it from 'id'.
                video_url = entry.get('url')
                if not video_url and entry.get('id'):
                    video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"

                if not video_url:
                    continue

                video_data = {
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'url': video_url,
                    'duration': entry.get('duration'),
                    'upload_date': entry.get('upload_date'),
                    'description': entry.get('description', ''),
                }
                channel_data['entries'].append(video_data)

            return channel_data

    except Exception as e:
        logger.error(f"Error processing channel {channel_url}: {str(e)}")
        return None

def download_audio(video_url, output_dir="downloads", cookiefile=None):
    """
    Downloads audio from a video URL and converts it to MP3.
    Returns the path to the downloaded file and metadata.
    """
    if not video_url:
        logger.error("download_audio called with None video_url")
        return None

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Output template: downloads/VIDEO_ID.mp3
    out_tmpl = os.path.join(output_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        # Fallback to download best available stream (video+audio) if bestaudio fails
        'format': 'best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
             'key': 'FFmpegMetadata',
        }],
        'outtmpl': out_tmpl,
        # Anti-bot options
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'quiet': False,
        'no_warnings': False,
        'default_search': 'auto',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile

    try:
        logger.info(f"Attempting to download: {video_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)

            if info:
                # Success!
                # The file extension might change after post-processing
                video_id = info['id']
                filename = f"{video_id}.mp3"
                filepath = os.path.join(output_dir, filename)

                # Verify file exists
                if os.path.exists(filepath):
                    return {
                        'filepath': filepath,
                        'filename': filename,
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'description': info.get('description'),
                        'upload_date': info.get('upload_date'),
                        'id': video_id
                    }
                else:
                    logger.error(f"Download reported success but file not found: {filepath}")
                    return None
            else:
                logger.error(f"No info returned for {video_url}")
                return None

    except Exception as e:
        logger.error(f"Failed to download from {video_url}: {str(e)}")
        return None
