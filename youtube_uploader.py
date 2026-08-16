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
    
    candidate_paths = [
        "token.json",
        token_path,
        "token.pickle",
        os.path.join("agentforchatvid", "token.json"),
        os.path.join("agentforchatvid", "token.pickle")
    ]
    
    found_path = None
    for path in candidate_paths:
        if not os.path.exists(path):
            continue
            
        # 1. Try loading as JSON (from_authorized_user_file)
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_file(path, SCOPES)
            if creds and (creds.valid or creds.refresh_token):
                found_path = path
                print(f"Loaded credentials from JSON file: {path}")
                break
        except Exception:
            pass

        # 2. Try loading as JSON dict (from_authorized_user_info)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_info(data, SCOPES)
            if creds and (creds.valid or creds.refresh_token):
                found_path = path
                print(f"Loaded credentials from JSON dict: {path}")
                break
        except Exception:
            pass

        # 3. Try loading as Pickle
        try:
            with open(path, "rb") as f:
                creds = pickle.load(f)
            if creds and (creds.valid or creds.refresh_token):
                found_path = path
                print(f"Loaded credentials from Pickle file: {path}")
                break
        except Exception as e:
            print(f"Note: Could not load pickle credentials from {path}: {e}")
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing YouTube OAuth access token...")
            creds.refresh(Request())
            target_save = found_path or token_path
            try:
                if target_save.endswith(".json"):
                    with open(target_save, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())
                else:
                    with open(target_save, "wb") as f:
                        pickle.dump(creds, f)
            except Exception:
                pass
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

