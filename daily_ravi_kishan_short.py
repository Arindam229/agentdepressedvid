import os
import sys
import json
import pickle
import argparse
import subprocess
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

def prepare_short_video(input_path, output_path="ravi_kishan_short_vertical.mp4"):
    """Converts 16:9 landscape video into 9:16 vertical 1080x1920 video for YouTube Shorts."""
    print("=======================================================")
    print(" [1/3] Converting landscape video into 9:16 Vertical Short format...")
    print("=======================================================")
    
    filter_graph = (
        "split[a][b];"
        "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15:3[bg];"
        "[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", filter_graph,
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Vertical Short video generated: {output_path}\n")
    return output_path

def get_authenticated_service(token_path="token_ravi_kishan.pickle"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    creds = None
    
    candidate_paths = [
        "token_ravi_kishan.json",
        token_path,
        "token_ravi_kishan.pickle",
        "token.json",
        "token.pickle",
        os.path.join("agentforchatvid", "token.json")
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
            raise Exception(
                "No valid YouTube credentials token found!\n"
                "Please update RAVI_KISHAN_TOKEN_BASE64 secret in GitHub Repository Settings."
            )
            
    return googleapiclient.discovery.build("youtube", "v3", credentials=creds)

def upload_short_and_video(video_path, day_num, upload=False):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Prepare vertical 9:16 short video file
    vertical_short_path = "ravi_kishan_short_vertical.mp4"
    prepare_short_video(video_path, vertical_short_path)

    # 1. YouTube Short Details (9:16 Vertical Video)
    short_title = f"Ravi Kishan singing song day {day_num} #shorts #ravikishan #meme"
    short_description = (
        f"Day {day_num} of posting Ravi Kishan singing in white outfit meme template.\n\n"
        f"#shorts #ravikishan #memes #trending #ravikishansinging"
    )

    # 2. Regular YouTube Video Details (Original Landscape Video)
    video_title = f"Ravi Kishan singing song day {day_num}"
    video_description = (
        f"Day {day_num} of posting Ravi Kishan singing in white outfit meme template.\n\n"
        f"#ravikishan #memes #trending #ravikishansinging"
    )

    print("=======================================================")
    print(f" PIPELINE SUMMARY: Day {day_num}")
    print("=======================================================")
    print(f"[1] SHORT TITLE: {short_title}")
    print(f"[1] SHORT FILE: {vertical_short_path} (1080x1920 9:16 Vertical)")
    print("-------------------------------------------------------")
    print(f"[2] REGULAR TITLE: {video_title}")
    print(f"[2] REGULAR FILE: {video_path} (1280x720 16:9 Landscape)")
    print("=======================================================\n")

    if not upload:
        print("[DRY-RUN MODE] --upload flag not passed. Skipping actual YouTube upload.")
        return None

    youtube = get_authenticated_service()

    # Upload 1: YouTube Short
    print("=======================================================")
    print(" [2/3] Uploading YouTube Short (9:16 Vertical)...")
    print("=======================================================")
    short_request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "23", # 23 = Comedy
                "description": short_description,
                "title": short_title
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(vertical_short_path, chunksize=-1, resumable=True)
    )
    short_response = short_request.execute()
    short_id = short_response.get("id")
    print(f"[+] Short Upload Successful! ID: {short_id}")
    print(f"    Short URL: https://youtube.com/shorts/{short_id}\n")

    # Upload 2: Regular Video
    print("=======================================================")
    print(" [3/3] Uploading Regular YouTube Video (16:9 Landscape)...")
    print("=======================================================")
    video_request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "23", # 23 = Comedy
                "description": video_description,
                "title": video_title
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    video_response = video_request.execute()
    video_id = video_response.get("id")
    print(f"[+] Regular Video Upload Successful! ID: {video_id}")
    print(f"    Video URL: https://youtube.com/watch?v={video_id}\n")

    # Save/update local counter file
    with open("day_counter.txt", "w") as f:
        f.write(str(day_num + 1))

    # Clean up generated vertical short video file
    if os.path.exists(vertical_short_path):
        try:
            os.remove(vertical_short_path)
        except Exception:
            pass

    return short_id, video_id

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload Daily Ravi Kishan Meme Short & Video")
    parser.add_argument("--upload", action="store_true", help="Perform actual YouTube upload")
    parser.add_argument("--video", type=str, default=VIDEO_FILENAME, help="Path to video file")
    parser.add_argument("--day", type=int, default=None, help="Override day counter")
    
    args = parser.parse_args()
    
    day_num = args.day if args.day is not None else get_day_counter()
    video_path = args.video if os.path.exists(args.video) else os.path.join(os.path.dirname(__file__), args.video)
    
    upload_short_and_video(video_path, day_num, upload=args.upload)
