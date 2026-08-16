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
    
    # Search candidates for YouTube token
    candidate_paths = [
        token_path,
        "token.json",
        os.path.join("agentforchatvid", "token.json"),
        os.path.join("agentforchatvid", "token.pickle")
    ]
    
    found_path = None
    for path in candidate_paths:
        if os.path.exists(path):
            found_path = path
            break
            
    if found_path:
        try:
            with open(found_path, "rb") as f:
                creds = pickle.load(f)
        except Exception:
            try:
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_file(found_path, SCOPES)
            except Exception as e:
                print(f"Failed to load credentials from {found_path}: {e}")
                
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing YouTube OAuth access token...")
            creds.refresh(Request())
            target_save = found_path or token_path
            with open(target_save, "wb") as f:
                pickle.dump(creds, f)
        else:
            raise Exception("No valid YouTube credentials token found!")
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)


def upload_video_to_youtube(video_path, title, description, category_id="10", thumbnail_path=None):
    """Uploads video and custom thumbnail to YouTube channel (Category 10 = Music)."""
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
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            print(f"Uploading thumbnail: {thumbnail_path}")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("Thumbnail uploaded successfully!")
        except Exception as e:
            print(f"Failed to set thumbnail: {e}")
            
    return video_id

