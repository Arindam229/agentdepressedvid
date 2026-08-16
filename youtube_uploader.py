import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

def get_authenticated_service(token_path="token.pickle"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    creds = None
    
    # Try pickle first, then json token
    if os.path.exists(token_path):
        try:
            with open(token_path, "rb") as token:
                creds = pickle.load(token)
        except Exception:
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"Failed to load credentials from {token_path}: {e}")
                
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing YouTube OAuth access token...")
            creds.refresh(Request())
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)
        else:
            raise Exception("No valid YouTube credentials token found!")
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_video_to_youtube(video_path, title, description, category_id="10"):
    """Uploads video to YouTube channel (Category 10 = Music)."""
    print(f"Starting upload to YouTube: {title}")
    youtube = get_authenticated_service()
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": category_id, # 10 = Music
                "description": description,
                "title": title
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    response = request.execute()
    video_id = response.get("id")
    print(f"Upload Successful! YouTube Video ID: {video_id}")
    return video_id
