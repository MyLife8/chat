from googleapiclient.discovery import build
import configparser

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

DEVELOPER_KEY = config.get('API_CREDENTIALS', 'yt_api_key')

# Build the YouTube Data API v3 service
youtube = build('youtube', 'v3', developerKey=DEVELOPER_KEY)

# Make the API request
request = youtube.videoCategories().list(
    part='snippet',
    regionCode='US'  # You can change this to your desired region
)
response = request.execute()

# Print the category titles
print("ID - Category")
for item in response['items']:
    print(f"{item['id']} - {item['snippet']['title']}")
