import os
import re
import requests
import urllib.parse
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv() # Load from current directory

app = Flask(__name__)

def get_youtube_service():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return None
    return build('youtube', 'v3', developerKey=api_key, cache_discovery=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    song_name = data.get('song_name')
    limit = int(data.get('limit', 50))

    if not song_name:
        return jsonify({"error": "No song name provided"}), 400

    youtube = get_youtube_service()
    if not youtube:
        return jsonify({"error": "YouTube API Key missing"}), 500

    try:
        # 1. Search for the video
        search_request = youtube.search().list(
            part="snippet",
            maxResults=1,
            q=song_name,
            type="video",
            videoCategoryId="10"
        )
        search_response = search_request.execute()

        if not search_response['items']:
            return jsonify({"error": "Song not found"}), 404

        video_id = search_response['items'][0]['id']['videoId']
        video_title = search_response['items'][0]['snippet']['title']
        playlist_id = f"RD{video_id}"

        # 2. Fetch the Mix
        mix_tracks = []
        next_page_token = None

        while len(mix_tracks) < limit:
            remaining = limit - len(mix_tracks)
            batch_size = min(remaining, 50)
            
            pl_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=batch_size,
                pageToken=next_page_token
            )
            pl_response = pl_request.execute()

            for item in pl_response['items']:
                title = item['snippet']['title']
                vid_id = item['snippet']['resourceId']['videoId']
                url = f"https://www.youtube.com/watch?v={vid_id}"
                
                # Check for thumbnails if available
                thumb = item['snippet']['thumbnails'].get('medium', {}).get('url', '')
                
                mix_tracks.append({
                    'title': title,
                    'url': url,
                    'thumbnail': thumb
                })
                
                if len(mix_tracks) >= limit:
                    break
            
            next_page_token = pl_response.get('nextPageToken')
            if not next_page_token or len(mix_tracks) >= limit:
                break
        
        return jsonify({
            "root_song": {"title": video_title, "id": video_id},
            "tracks": mix_tracks
        })

    except HttpError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stream_download', methods=['GET'])
def stream_download():
    """
    Streams the audio directly to the client using yt-dlp piped to ffmpeg.
    Query Params:
      url: The YouTube URL.
      title: The desired filename (optional).
      mode: 'download' (default) or 'play'.
    """
    song_url = request.args.get('url')
    title = request.args.get('title')
    mode = request.args.get('mode', 'download')

    if not song_url:
        return jsonify({"error": "No URL provided"}), 400

    # Extract Video ID
    video_id = None
    try:
        # Simple extraction for standard YouTube URLs
        parsed = urllib.parse.urlparse(song_url)
        if parsed.hostname == 'youtu.be':
            video_id = parsed.path[1:]
        elif parsed.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed.path == '/watch':
                p = urllib.parse.parse_qs(parsed.query)
                video_id = p['v'][0]
            elif parsed.path[:7] == '/embed/':
                video_id = parsed.path.split('/')[2]
            elif parsed.path[:3] == '/v/':
                video_id = parsed.path.split('/')[2]
    except Exception as e:
        print(f"Error extracting ID: {e}")

    if not video_id:
         # Fallback: try to regex it or fail
        #  If the user provides just the ID, we might handle that too, but let's assume full URL
        # For now, if extraction fails, we can't proceed with this API
        return jsonify({"error": "Could not extract Video ID"}), 400


    # RapidAPI Setup
    api_url = "https://youtube-mp36.p.rapidapi.com/dl"
    querystring = {"id": video_id}
    headers = {
        "x-rapidapi-host": "youtube-mp36.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY")
    }

    # Sanitize title
    safe_title = "audio.mp3"
    if title:
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
        safe_title = f"{clean_title}.mp3"
    
    try:
        encoded_filename = urllib.parse.quote(safe_title)
    except:
        encoded_filename = "download.mp3"


    def generate_audio():
        try:
            # 1. Fetch the JSON from RapidAPI
            resp = requests.get(api_url, headers=headers, params=querystring)
            resp.raise_for_status()
            
            data = resp.json()
            download_link = data.get('link')
            
            if not download_link:
                print(f"No link in response: {data}")
                return

            # 2. Stream the actual file from the link
            with requests.get(download_link, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk
        except Exception as e:
            print(f"RapidAPI Streaming error: {e}")
            return

    # Determine disposition
    disposition = "attachment" if mode == 'download' else "inline"
    
    return Response(
        stream_with_context(generate_audio()),
        mimetype="audio/mpeg",
        headers={
            "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_filename}; filename=\"{safe_title}\""
        }
    )

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
