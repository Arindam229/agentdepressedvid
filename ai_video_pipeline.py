import os
import sys
import json
import random
import urllib.request
import re
import subprocess
from datetime import timedelta

# Dependencies required: yt-dlp, ffmpeg (in system PATH)

TARGET_DURATION_SECONDS = 3 * 60 * 60  # 3 hours target duration (10800 seconds)

DEFAULT_TITLES = [
    "you have to sleep...",
    "songs that hit different at 3 am",
    "staring at the ceiling again",
    "late night overthinking playlist",
    "lonely nights in a quiet room",
    "for when you can't fall asleep",
    "nostalgic songs for late night drives",
    "crying in your room at 2am",
    "songs for when everything feels quiet",
    "a playlist for quiet midnight thoughts"
]


DEFAULT_PROMPT = (
    "A blurry, candid lo-fi frame of a depressed somber young girl looking out a window at twilight, "
    "dark deep blue lighting, ambient city night lights outside, melancholic sad mood, camera grain, "
    "subtle VHS scanlines, realistic raw aesthetic, 90s aesthetic"
)

def fetch_spotify_tracks(playlist_url):
    """Scrapes track links/titles from a public Spotify playlist URL."""
    print(f"[1/5] Fetching Spotify playlist: {playlist_url}")
    req = urllib.request.Request(playlist_url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    
    track_ids = re.findall(r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)', html)
    tracks = []
    seen = set()
    
    for track_id in track_ids:
        if track_id in seen:
            continue
        seen.add(track_id)
        try:
            embed_url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/track/{track_id}"
            resp = urllib.request.urlopen(embed_url)
            data = json.loads(resp.read().decode('utf-8'))
            title = data.get('title')
            if title:
                tracks.append(title)
        except Exception:
            pass

    print(f"Total unique tracks scraped: {len(tracks)}")
    return tracks

def download_and_select_audio(tracks, temp_dir="temp_audio"):
    """Randomly selects tracks and downloads audio until total ~3 hours is reached."""
    os.makedirs(temp_dir, exist_ok=True)
    random.shuffle(tracks)
    
    downloaded_files = []
    timestamps = []
    current_time = 0
    
    print("[2/5] Downloading random tracks with yt-dlp...")
    
    for idx, track in enumerate(tracks, 1):
        if current_time >= TARGET_DURATION_SECONDS:
            break
            
        print(f"Processing ({idx}/{len(tracks)}): {track}")
        output_template = os.path.join(temp_dir, f"track_{idx}.%(ext)s")
        
        # Download audio via yt-dlp
        cmd = [
            "yt-dlp",
            "--default-search", "ytsearch1:",
            "-x", "--audio-format", "mp3",
            "-o", output_template,
            f"{track} audio"
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Failed to download: {track}")
            continue
            
        file_path = os.path.join(temp_dir, f"track_{idx}.mp3")
        if not os.path.exists(file_path):
            continue
            
        # Get duration using ffprobe
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
        try:
            duration = float(probe_res.stdout.strip())
        except ValueError:
            duration = 180.0  # fallback duration assumption
            
        timestamp_str = str(timedelta(seconds=int(current_time)))
        if len(timestamp_str) == 7:
            timestamp_str = "0" + timestamp_str
            
        timestamps.append(f"{timestamp_str} - {track}")
        downloaded_files.append(file_path)
        current_time += duration
        print(f"Added! Current total duration: {str(timedelta(seconds=int(current_time)))}")

    return downloaded_files, timestamps

def create_concat_audio(audio_files, output_file="final_audio.mp3"):
    """Merges all downloaded tracks into a single concatenated audio file using FFmpeg."""
    print("[3/5] Merging audio files into master track...")
    list_file = "file_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for filepath in audio_files:
            clean_path = filepath.replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_file
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(list_file):
        os.remove(list_file)
    return output_file

def generate_video(image_path, audio_path, output_video="output_final.mp4", video_title=None):
    """Assembles final video with image, audio, VHS overlays, and title text."""
    if not video_title:
        video_title = random.choice(DEFAULT_TITLES)
        
    print(f"[4/5] Rendering video with title '{video_title}' & VHS overlay effects...")
    
    # FFmpeg complex filter adding scanlines, PLAY overlay, timestamp & title text
    vf_filter = (
        f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
        f"drawtext=text='PLAY ▶':x=80:y=60:fontsize=42:fontcolor=white@0.8:fontfile=C\\\\:/Windows/Fonts/arial.ttf,"
        f"drawtext=text='00\\:00\\:08':x=1600:y=1000:fontsize=36:fontcolor=white@0.7:fontfile=C\\\\:/Windows/Fonts/arial.ttf,"
        f"drawtext=text='{video_title}':x=(w-text_w)/2:y=h-120:fontsize=50:fontcolor=white@0.9:fontfile=C\\\\:/Windows/Fonts/arialbd.ttf"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", vf_filter,
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-pix_fmt", "yuv420p",
        output_video
    ]
    subprocess.run(cmd, check=True)
    print(f"Video saved successfully: {output_video}")

def export_metadata(timestamps, video_title, playlist_url, output_file="YOUTUBE_DESCRIPTION.txt"):
    """Writes YouTube description file with title, Spotify playlist link, and track timestamps."""
    print("[5/5] Generating metadata & description file...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {video_title}\n\n")
        f.write(f"🎧 Original Spotify Playlist:\n{playlist_url}\n\n")
        f.write("📜 Tracklist & Timestamps:\n")
        for line in timestamps:
            f.write(f"{line}\n")
        f.write("\n---\nCreated with AI Video Pipeline")
    print(f"Metadata exported to {output_file}")

def run_pipeline(playlist_url, image_path, video_title=None, upload=False):
    if not video_title:
        video_title = random.choice(DEFAULT_TITLES)
        
    tracks = fetch_spotify_tracks(playlist_url)
    audio_files, timestamps = download_and_select_audio(tracks)
    master_audio = create_concat_audio(audio_files)
    output_video = "output_final.mp4"
    generate_video(image_path, master_audio, output_video=output_video, video_title=video_title)
    
    desc_file = "YOUTUBE_DESCRIPTION.txt"
    export_metadata(timestamps, video_title, playlist_url, output_file=desc_file)
    
    if upload:
        try:
            from youtube_uploader import upload_video_to_youtube
            with open(desc_file, "r", encoding="utf-8") as f:
                desc = f.read()
            upload_video_to_youtube(output_video, video_title, desc)
        except Exception as e:
            print(f"Error during YouTube upload: {e}")

DEFAULT_PLAYLIST_URL = "https://open.spotify.com/playlist/3WYcoszlfcLRB3lbHEhN5i"

if __name__ == "__main__":
    playlist_url = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else DEFAULT_PLAYLIST_URL
    image_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "agentforchatvid/Gemini_Generated_Image_azeja3azeja3azej.png"
    title = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else None
    upload = "--upload" in sys.argv
    
    run_pipeline(playlist_url, image_path, title, upload=upload)



