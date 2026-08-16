import os
import sys
import pickle
import argparse
from datetime import datetime, date
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Default start date for Day 0 counter (2026-08-16)
START_DATE = date(2026, 8, 16)

VIDEO_FILENAME = "vidssave.com Ravi kishan singing song new meme template __ ravi kishan singing in white outfit new trending meme 720P.mp4"

def get_day_counter(counter_file="day_counter.txt"):
    """Calculates day count starting from START_DATE (Day 0). Also checks counter_file if overridden."""
    today = datetime.now().date()
    days_elapsed = max(0, (today - START_DATE).days)
    
    if os.path.exists(counter_file):
        try:
            with open(counter_file, "r") as f:
                file_val = int(f.read().strip())
                return max(file_val, days_elapsed)
        except Exception:
            pass
            
    return days_elapsed

def get_authenticated_service(token_path="token_ravi_kishan.pickle"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    creds = None
    
    candidate_paths = [
        token_path,
        "token_ravi_kishan.pickle",
        "token.pickle",
        "token.json",
        os.path.join("agentforchatvid", "token.json")
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
            raise Exception("No valid YouTube credentials token found! Please run generate_new_token.py first.")
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_short(video_path, day_num, upload=False):
    title = f"Ravi Kishan singing song day {day_num} #shorts #ravikishan #meme"
    description = (
        f"Day {day_num} of posting Ravi Kishan singing in white outfit meme template.\n\n"
        f"#shorts #ravikishan #memes #trending #ravikishansinging"
    )
    
    print("=======================================================")
    print(f" PIPELINE: Ravi Kishan Singing Short - Day {day_num}")
    print("=======================================================")
    print(f"Video File: {video_path}")
    print(f"Title: {title}")
    print(f"Description:\n{description}")
    print("=======================================================\n")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not upload:
        print("[DRY-RUN MODE] --upload flag not passed. Skipping actual YouTube upload.")
        return None

    youtube = get_authenticated_service()
    
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "23", # 23 = Comedy, 10 = Music
                "description": description,
                "title": title
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    
    print("Uploading video to YouTube Shorts...")
    response = request.execute()
    video_id = response.get("id")
    print(f"Upload Successful! YouTube Video ID: {video_id}")
    print(f"Watch URL: https://youtube.com/shorts/{video_id}")
    
    # Save/update local counter file
    with open("day_counter.txt", "w") as f:
        f.write(str(day_num + 1))
        
    return video_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Daily Ravi Kishan Meme Short")
    parser.add_argument("--upload", action="store_true", help="Perform actual YouTube upload")
    parser.add_argument("--video", type=str, default=VIDEO_FILENAME, help="Path to video file")
    parser.add_argument("--day", type=int, default=None, help="Override day counter")
    
    args = parser.parse_args()
    
    day_num = args.day if args.day is not None else get_day_counter()
    video_path = args.video if os.path.exists(args.video) else os.path.join(os.path.dirname(__file__), args.video)
    
    upload_short(video_path, day_num, upload=args.upload)
