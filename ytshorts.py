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
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY) # japantschmidt google account

def format_timestamp(timestamp_str):
    """Convert UTC timestamp to a more readable local time format."""
    try:
        # Try parsing with microseconds
        utc_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            # If that fails, try without microseconds
            utc_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # If both fail, return the original string
            return timestamp_str
    
    local_time = utc_time.replace(tzinfo=timezone.utc).astimezone()  # Convert to local timezone
    return local_time.strftime("%Y-%m-%d %I:%M %p %Z")

def get_video_details(video_id):
    video_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    ).execute()
   
    if not video_response['items']:
        return None
    
    video_data = video_response['items'][0]
    snippet = video_data['snippet']
    content_details = video_data['contentDetails']
    stats = video_data['statistics']
    
    duration = isodate.parse_duration(content_details['duration'])
   
    return {
        'title': snippet['title'],
        'description': snippet['description'],
        'published_at': snippet['publishedAt'],
        'category_id': snippet['categoryId'],
        'duration': duration,
        'view_count': int(stats.get('viewCount', 0)),
        'like_count': int(stats.get('likeCount', 0)),
        'comment_count': int(stats.get('commentCount', 0))
    }

def get_top_shorts(keyword, start_date, end_date):
    search_response = youtube.search().list(
        q=keyword,
        part="id",
        maxResults=10,
        type="video",
        videoDuration="short",
        order="viewCount",
        publishedAfter=start_date.isoformat(),
        publishedBefore=end_date.isoformat()
    ).execute()
   
    results = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        video_details = get_video_details(video_id)
        if video_details:
            results.append((video_id, video_details))
    return results

def main():
    keyword = input("Enter a keyword to search for: ")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=5)
   
    print(f"Searching for top shorts from {start_date.date()} to {end_date.date()}...")
   
    top_shorts = get_top_shorts(keyword, start_date, end_date)
   
    if top_shorts:
        print(f"\nTop shorts for '{keyword}':")
        for i, (video_id, details) in enumerate(top_shorts, 1):
            print(f"{i}. {details['title']}")
            print(f"   Desc: {details['description'][:100]}...")
            print(f"   Video ID: {video_id}")
            print(f"   Video Link: https://www.youtube.com/watch?v={video_id}")
            print(f"   Published UTC: {details['published_at']}")
            print(f"   Published: {format_timestamp(details['published_at'])}")
            print(f"   Duration: {details['duration']}")
            print(f"   Views: {details['view_count']}")
            print(f"   Likes: {details['like_count']}")
            print(f"   Comments: {details['comment_count']}")
            print(f"   CategoryID: {details['category_id']}")
            print()
    else:
        print("No results found.")

if __name__ == "__main__":
    main()