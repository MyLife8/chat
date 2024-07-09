from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import configparser
import isodate

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# YouTube Data API setup
DEVELOPER_KEY = config.get('API_CREDENTIALS', 'yt_api_key')
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

def format_timestamp(timestamp_str):
    # ... (unchanged)

def get_recent_videos_count(channel_id, days):
    # ... (unchanged)

def get_video_stats(video_id):
    video_response = youtube.videos().list(
        part="statistics,contentDetails,snippet",
        id=video_id
    ).execute()
   
    if not video_response['items']:
        return None
    
    item = video_response['items'][0]
    content_details = item['contentDetails']
    duration = isodate.parse_duration(content_details['duration'])
   
    stats = item['statistics']
    snippet = item['snippet']
    
    channel_id = snippet['channelId']
    channel_response = youtube.channels().list(
        part="statistics,snippet",
        id=channel_id
    ).execute()
    
    if channel_response['items']:
        channel_item = channel_response['items'][0]
        channel_stats = channel_item['statistics']
        channel_snippet = channel_item['snippet']
        channel_created_date = channel_snippet['publishedAt']
        channel_video_views = channel_stats['viewCount']  # Fixed: Use channel_stats instead of channel_snippet
        custom_url = channel_snippet.get('customUrl', 'Not available')
        
        # Get recent video counts
        videos_last_7_days = get_recent_videos_count(channel_id, 7)
        videos_last_30_days = get_recent_videos_count(channel_id, 30)
    else:
        channel_stats = {}
        channel_created_date = None
        channel_video_views = 'Not available'
        custom_url = 'Not available'
        videos_last_7_days = 0
        videos_last_30_days = 0
    
    return {
        'duration': duration,
        'view_count': int(stats.get('viewCount', 0)),
        'like_count': int(stats.get('likeCount', 0)),
        'comment_count': int(stats.get('commentCount', 0)),
        'category_id': int(snippet.get('categoryId', 0)),
        'channel_title': snippet['channelTitle'],
        'channel_id': channel_id,
        'channel_custom_url': custom_url,
        'channel_subscriber_count': int(channel_stats.get('subscriberCount', 0)),
        'channel_created_date': channel_created_date,
        'channel_video_views': int(channel_stats.get('viewCount', 0)),
        'published_at': snippet['publishedAt'],
        'videos_last_7_days': videos_last_7_days,
        'videos_last_30_days': videos_last_30_days
    }

def get_top_shorts(keyword, start_date, end_date):
    # ... (unchanged)

def main():
    # ... (unchanged)

if __name__ == "__main__":
    main()