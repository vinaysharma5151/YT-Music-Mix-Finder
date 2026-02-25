let currentTracks = [];
let currentTrackIndex = -1;

async function searchSong() {
    const songName = document.getElementById('songInput').value;
    const limit = document.getElementById('limitInput').value;
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const trackList = document.getElementById('trackList');
    const header = document.getElementById('resultHeader');

    if (!songName) return;

    // UI Reset
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    trackList.innerHTML = '';

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ song_name: songName, limit: limit })
        });

        const data = await response.json();

        loading.classList.add('hidden');

        if (response.ok) {
            results.classList.remove('hidden');
            header.innerText = `Mix based on "${data.root_song.title}"`;
            currentTracks = data.tracks; // Store tracks globally
            currentTrackIndex = -1;

            data.tracks.forEach((track, index) => {
                const card = document.createElement('div');
                card.className = 'track-card';

                const img = track.thumbnail ? `<img src="${track.thumbnail}" class="track-img" alt="thumb">` : '';
                const safeTitle = track.title.replace(/'/g, "\\'");

                card.innerHTML = `
                    ${img}
                    <div class="track-info">
                        <div class="track-title">${track.title}</div>
                        <a href="${track.url}" target="_blank" style="color: #666; font-size: 0.8rem; text-decoration: none;">Watch on YouTube</a>
                    </div>
                    <div class="track-actions">
                        <button class="play-btn">Play</button>
                        <button onclick="downloadTrack('${track.url}', '${safeTitle}')">Download</button>
                    </div>
                `;

                // Update Play button to pass index
                const playBtn = card.querySelector('.play-btn');
                playBtn.onclick = () => playTrack(index);

                trackList.appendChild(card);
            });
        } else {
            showNotification(data.error || 'Something went wrong', true);
        }

    } catch (error) {
        loading.classList.add('hidden');
        showNotification('Failed to connect to server', true);
        console.error(error);
    }
}

async function downloadTrack(url, title) {
    showNotification(`Download starting for: ${title}...`);

    try {
        // Construct the stream download URL
        const safeTitleQuery = encodeURIComponent(title);
        const urlQuery = encodeURIComponent(url);

        // Trigger download by navigating to the stream URL
        // This will start the browser's download manager
        const downloadUrl = `/api/stream_download?url=${urlQuery}&title=${safeTitleQuery}`;

        const link = document.createElement('a');
        link.href = downloadUrl;

        // Use download attribute just in case, though the server sets Content-Disposition
        link.setAttribute('download', `${title}.mp3`);

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // We don't get a callback for when it finishes, but we know the request started.
        showNotification('Download started via stream!');

    } catch (error) {
        showNotification('Error triggering download', true);
        console.error(error);
    }
}

async function playTrack(index) {
    if (index < 0 || index >= currentTracks.length) return;

    currentTrackIndex = index;
    const track = currentTracks[index];
    const url = track.url;
    const title = track.title;

    const playerBar = document.getElementById('player-bar');
    const playerTitle = document.getElementById('player-title');
    const audioPlayer = document.getElementById('audio-player');

    showNotification(`your song is getting ready you to get ready to vive babes 🥳`, false, 0);

    try {
        // Construct the stream URL with mode=play for inline disposition
        const safeTitleQuery = encodeURIComponent(title);
        const urlQuery = encodeURIComponent(url);

        // This URL streams MP3 directly
        const streamUrl = `/api/stream_download?url=${urlQuery}&title=${safeTitleQuery}&mode=play`;

        // Show player if hidden
        playerBar.classList.remove('hidden');

        // Set playback details
        playerTitle.innerText = title;

        // Set the source directly to our stream
        audioPlayer.src = streamUrl;

        // Start playing
        try {
            await audioPlayer.play();
            showNotification('Playing now!');
        } catch (playError) {
            console.error("Auto-play blocked or failed:", playError);
            showNotification('Click play to start', false);
        }

    } catch (error) {
        showNotification('Error connecting to stream', true);
        console.error(error);
    }
}

function showNotification(message, isError = false, duration = 4000) {
    const note = document.getElementById('notification');
    note.innerText = message;
    note.style.borderLeft = isError ? '4px solid #ff0050' : '4px solid #00f2ea';
    note.classList.remove('hidden');

    // Clear any previous timeout to avoid hiding too early
    if (note.timeoutId) clearTimeout(note.timeoutId);

    if (duration > 0) {
        note.timeoutId = setTimeout(() => {
            note.classList.add('hidden');
        }, duration);
    }
}

// Allow Enter key
document.getElementById('songInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        searchSong();
    }
});

// Auto-play next song
document.getElementById('audio-player').addEventListener('ended', function () {
    if (currentTrackIndex < currentTracks.length - 1) {
        playTrack(currentTrackIndex + 1);
    }
});
