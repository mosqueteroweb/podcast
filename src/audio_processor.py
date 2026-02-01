import yt_dlp
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_channel_info(channel_url, limit=5):
    """
    Fetches channel metadata and the latest videos.
    """
    ydl_opts = {
        'extract_flat': True,
        'playlistend': limit,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)

            # Basic validation
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

            if 'entries' in info:
                for entry in info['entries']:
                    video_data = {
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': entry.get('url'),
                        'duration': entry.get('duration'),
                        'upload_date': entry.get('upload_date'),
                        'description': entry.get('description', ''), # Might be empty in flat extraction
                    }
                    channel_data['entries'].append(video_data)

            return channel_data

    except Exception as e:
        logger.error(f"Error processing channel {channel_url}: {str(e)}")
        return None

def download_audio(video_url, output_dir="downloads"):
    """
    Downloads audio from a video URL and converts it to MP3.
    Returns the path to the downloaded file and metadata.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Output template: downloads/VIDEO_ID.mp3
    out_tmpl = os.path.join(output_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
             'key': 'FFmpegMetadata',
        }],
        'outtmpl': out_tmpl,
        'quiet': True,
        # Anti-bot options
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading {video_url}...")
            info = ydl.extract_info(video_url, download=True)

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
                logger.error(f"File not found after download: {filepath}")
                return None

    except Exception as e:
        logger.error(f"Error downloading {video_url}: {str(e)}")
        return None
