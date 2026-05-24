import asyncio
import json
import logging
import os
import sys
import uuid
import requests
from tqdm import tqdm

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.contrib.media import MediaPlayer

# Configure logging
logging.basicConfig(level=logging.INFO)
ROOT = os.path.dirname(__file__)

# Global variables
pcs = set()
# Use a new, reliable URL for a shorter sample video
VIDEO_URL = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/Big_Buck_Bunny_1080_10s_1MB.mp4"
VIDEO_PATH = os.path.join(ROOT, "sample_video.mp4")

# Configure STUN and TURN servers
# Using the OpenRelay public servers.
ICE_SERVERS = [
    RTCIceServer("stun:stun.l.google.com:19302"),
    RTCIceServer("stun:stun1.l.google.com:19302"),
    RTCIceServer(
        "turn:openrelay.metered.ca:80",
        username="openrelayproject",
        credential="openrelayproject"
    ),
    RTCIceServer(
        "turn:openrelay.metered.ca:443",
        username="openrelayproject",
        credential="openrelayproject"
    )
]


def download_file(url, filename):
    """Downloads a file from a URL to a local path, showing a progress bar."""
    if os.path.exists(filename):
        # Check if the file is valid by checking its size.
        if os.path.getsize(filename) > 1000:
            logging.info(f"File {filename} already exists. Skipping download.")
            return True
        else:
            logging.warning(f"File {filename} is very small, likely a failed download. Re-downloading.")
            os.remove(filename)

    logging.info(f"Downloading {filename} from {url}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(filename, 'wb') as f, tqdm(
                total=total_size, unit='iB', unit_scale=True, desc=os.path.basename(filename)
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        logging.info(f"Successfully downloaded {filename}.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download video: {e}")
        # If the file was partially created, remove it.
        if os.path.exists(filename):
            os.remove(filename)
        return False


async def index(request):
    """Serve the main HTML page."""
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    """Serve the main JavaScript file."""
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    """Handle the WebRTC offer from the client."""
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    # Create RTCPeerConnection with STUN and TURN server configuration
    config = RTCConfiguration(iceServers=ICE_SERVERS)
    pc = RTCPeerConnection(configuration=config)
    pc_id = f"PeerConnection({uuid.uuid4()})"
    pcs.add(pc)

    def log_info(msg, *args):
        logging.info(f"{pc_id} {msg}", *args)

    log_info("Created for %s", request.remote)

    # Create a media player to stream the downloaded video file
    try:
        player = MediaPlayer(VIDEO_PATH, loop=True)
    except Exception as e:
        log_info(f"Failed to open media player for {VIDEO_PATH}: {e}")
        # Return a JSON error response if the media player fails
        return web.Response(
            content_type="application/json",
            status=500,
            text=json.dumps({"error": f"Failed to open video file on server. Check logs for details. Error: {e}"}),
        )

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            await pc.close()
            pcs.discard(pc)

    # Handle offer
    await pc.setRemoteDescription(offer)

    # Add the server-side video track to the connection
    if player and player.video:
        pc.addTrack(player.video)
    if player and player.audio:
        pc.addTrack(player.audio)

    # Send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    """Close all peer connections on shutdown."""
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    # Download the sample video file
    if not download_file(VIDEO_URL, VIDEO_PATH):
        logging.error("Could not download the required video file. Exiting.")
        sys.exit(1)

    # Create the necessary HTML, JS, and requirements files if they don't exist
    if not os.path.exists("index.html"):
        with open("index.html", "w") as f:
            f.write("""
<!DOCTYPE html>
<html>
    <head>
        <title>AI Avatar</title>
        <style>
            body { font-family: sans-serif; background-color: #f0f2f5; color: #333; }
            video { width: 100%; max-width: 640px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); background-color: #000;}
            .container { max-width: 800px; margin: 2rem auto; text-align: center; background: #fff; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
            h1 { color: #1a1a1a; }
            p { color: #666; margin-bottom: 1.5rem; }
            button {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            button:hover { background-color: #0056b3; }
            #stop { background-color: #dc3545; }
            #stop:hover { background-color: #c82333; }
            #status-box, #error-box { padding: .75rem 1.25rem; margin-top: 1rem; border: 1px solid transparent; border-radius: .25rem; display: none; }
            #status-box { color: #0c5460; background-color: #d1ecf1; border-color: #bee5eb; }
            #error-box { color: #721c24; background-color: #f8d7da; border-color: #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI Avatar</h1>
            <p>A video file is being streamed from the server to this page in real-time.</p>
            <video id="video" autoplay="true" playsinline="true" muted></video>
            <div id="controls">
                <!-- Buttons will be added here by JavaScript -->
            </div>
            <div id="status-box"></div>
            <div id="error-box"></div>
        </div>
        <script src="client.js"></script>
    </body>
</html>
            """)

    if not os.path.exists("client.js"):
        with open("client.js", "w") as f:
            f.write("""
var pc = null;
var videoElement = document.getElementById('video');
var statusBox = document.getElementById('status-box');
var errorBox = document.getElementById('error-box');

// Define STUN and TURN server configuration
var iceConfig = {
    'iceServers': [
        { 'urls': 'stun:stun.l.google.com:19302' },
        { 'urls': 'stun:stun1.l.google.com:19302' },
        {
            'urls': 'turn:openrelay.metered.ca:80',
            'username': 'openrelayproject',
            'credential': 'openrelayproject'
        },
        {
            'urls': 'turn:openrelay.metered.ca:443',
            'username': 'openrelayproject',
            'credential': 'openrelayproject'
        }
    ]
};

function setStatus(message) {
    statusBox.style.display = 'block';
    statusBox.textContent = message;
}

function displayError(message) {
    errorBox.style.display = 'block';
    errorBox.textContent = message;
    setStatus(''); // Clear status on error
}

function negotiate() {
    setStatus('Negotiating connection...');
    pc.addTransceiver('video', {direction: 'recvonly'});
    pc.addTransceiver('audio', {direction: 'recvonly'});
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                pc.addEventListener('icegatheringstatechange', function() {
                    if (pc.iceGatheringState === 'complete') {
                        resolve();
                    }
                });
            }
        });
    }).then(function() {
        var offer = pc.localDescription;
        setStatus('Sending offer to server...');
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: { 'Content-Type': 'application/json' },
            method: 'POST'
        });
    }).then(function(response) {
        if (!response.ok) {
            return response.json().then(function(err) { throw new Error(err.error); });
        }
        return response.json();
    }).then(function(answer) {
        setStatus('Received answer, setting remote description.');
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        displayError('Connection failed: ' + e.message);
        stop();
    });
}

function start() {
    errorBox.style.display = 'none';
    setStatus('Starting...');
    // Create RTCPeerConnection with STUN and TURN server configuration
    pc = new RTCPeerConnection(iceConfig);

    pc.addEventListener('track', function(evt) {
        setStatus('Track received, attempting to play...');
        if (videoElement.srcObject !== evt.streams[0]) {
            videoElement.srcObject = evt.streams[0];
        }
        // Attempt to play the video element, as autoplay might be blocked.
        videoElement.play().catch(function(error) {
            displayError('Video playback failed. Please click the video to play. Error: ' + error.message);
            // Add a click listener to the video to try playing again on user interaction
            videoElement.addEventListener('click', function() {
                videoElement.play();
            }, { once: true });
        });
    });
    
    pc.addEventListener('connectionstatechange', function() {
        setStatus('Connection state: ' + pc.connectionState);
        if (pc.connectionState === 'connected') {
            statusBox.style.display = 'none'; // Hide status when connected
        }
    });

    document.getElementById('start').style.display = 'none';
    negotiate();
    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    setStatus('Stopping connection...');
    document.getElementById('stop').style.display = 'none';
    document.getElementById('start').style.display = 'inline-block';
    if (pc) {
        pc.close();
        pc = null;
    }
    videoElement.srcObject = null;
    setTimeout(function() {
        statusBox.style.display = 'none';
    }, 2000);
}

// --- Initialize UI ---
var controlsContainer = document.getElementById('controls');

var startButton = document.createElement('button');
startButton.id = 'start';
startButton.innerHTML = 'Start';
startButton.onclick = start;
controlsContainer.appendChild(startButton);

var stopButton = document.createElement('button');
stopButton.id = 'stop';
stopButton.style.display = 'none';
stopButton.innerHTML = 'Stop';
stopButton.onclick = stop;
controlsContainer.appendChild(stopButton);
            """)

    # Update requirements.txt
    if not os.path.exists("requirements.txt"):
        with open("requirements.txt", "w") as f:
            f.write("""aiohttp
aiortc
av
requests
tqdm
""")
    else:
        # Ensure requests and tqdm are in the requirements
        with open("requirements.txt", "r+") as f:
            content = f.read()
            if "requests" not in content:
                f.write("\nrequests")
            if "tqdm" not in content:
                f.write("\ntqdm")


    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, access_log=None, host="0.0.0.0", port=8080)
