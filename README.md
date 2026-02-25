# VibeFlow

A sleek web application to generate a continuous music mix based on any YouTube song name. Seamlessly search for tracks and stream/download them directly.

## Features
- **Smart Mix Generation**: Enter one song, and get a curated mix using YouTube's recommendation engine.
- **Direct Streaming**: Listen to tracks directly in the browser.
- **Instant Downloads**: Save tracks as MP3 files for offline listening.
- **Modern UI**: Clean, responsive design with smooth animations.

## Tech Stack
- **Backend**: Python (Flask)
- **Frontend**: HTML5, CSS3, JavaScript
- **APIs**: YouTube Data API v3, RapidAPI (YouTube to MP3)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd web_app
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create a `.env` file in the root directory (use `.env.example` as a template):
   ```env
   RAPIDAPI_KEY=your_rapidapi_key_here
   YOUTUBE_API_KEY=your_youtube_api_key_here
   ```

4. **Run the app**:
   ```bash
   python3 app.py
   ```
   The app will be available at `http://localhost:5001`.

## Development
This app uses `ngrok` for tunneling if needed, which can be configured via environment or local logs.
