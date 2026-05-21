#!/usr/bin/env python3
"""
MiniMax Music 2.6 — AI Music Generator + YouTube Reference Cover
Endpoints:
  POST /api/generate   — text-to-music (music-2.6)
  POST /api/cover      — YouTube URL → audio → cover (music-cover)
  GET  /api/health
"""
import base64
import json
import os
import subprocess
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "index.html"
AUDIO_DIR = ROOT / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("MUSIC_HOST", "127.0.0.1")
PORT = int(os.getenv("MUSIC_PORT", "8779"))
MINIMAX_MUSIC_URL = "https://api.minimax.io/v1/music_generation"
MINIMAX_PUBLIC_BASE = os.getenv("MUSIC_PUBLIC_BASE", "https://on9claw.com/music")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")

YTDLP_BIN = "/usr/bin/yt-dlp"
FFMPEG_BIN = "/usr/bin/ffmpeg"


def json_response(handler, payload, status=200):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(data)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8")) if raw else {}


def _decode_audio_hex(raw: dict) -> dict:
    """Parse MiniMax music generation response, decode hex audio, save to disk."""
    base_resp = raw.get("base_resp") or {}
    if base_resp.get("status_code") not in (0, None):
        raise RuntimeError(f"MiniMax Music failed: {base_resp.get('status_msg', 'unknown error')}")

    data = raw.get("data") or {}
    audio = data.get("audio", "").strip()
    if not audio:
        raise RuntimeError("MiniMax Music returned no audio data.")

    try:
        audio_bytes = bytes.fromhex(audio)
    except Exception:
        raise RuntimeError("MiniMax Music returned invalid audio encoding.")

    job_id = str(uuid.uuid4())[:12]
    filename = f"{job_id}.mp3"
    filepath = AUDIO_DIR / filename
    filepath.write_bytes(audio_bytes)

    extra = raw.get("extra_info") or {}
    return {
        "job_id": job_id,
        "filename": filename,
        "duration_ms": extra.get("music_duration", 0),
        "sample_rate": extra.get("music_sample_rate", 44100),
        "bitrate": extra.get("bitrate", 256000),
        "channels": extra.get("music_channel", 2),
        "size_bytes": extra.get("music_size", len(audio_bytes)),
        "mime_type": "audio/mpeg",
        "audio_base64": base64.b64encode(audio_bytes).decode("ascii"),
    }


def call_minimax_api(payload: dict, timeout: int = 180) -> dict:
    """Send a request to MiniMax and return the parsed JSON response."""
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        MINIMAX_MUSIC_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:4000]
        raise RuntimeError(f"MiniMax API error {e.code}: {detail}")
    except Exception as e:
        raise RuntimeError(f"MiniMax request failed: {e}")
    return json.loads(raw)


# ═══════════════════════════════════════════════
#  Text-to-Music  (music-2.6 / music-2.6-free)
# ═══════════════════════════════════════════════
def generate_music(prompt: str, lyrics: str = "", is_instrumental: bool = False,
                   lyrics_optimizer: bool = False, model: str = "music-2.6-free",
                   sample_rate: int = 44100, bitrate: int = 256000,
                   audio_format: str = "mp3") -> dict:
    if not MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is missing.")

    payload: dict = {
        "model": model,
        "is_instrumental": is_instrumental,
        "lyrics_optimizer": lyrics_optimizer,
        "stream": False,
        "audio_setting": {
            "sample_rate": sample_rate,
            "bitrate": bitrate,
            "format": audio_format,
        },
    }
    if prompt:
        payload["prompt"] = prompt[:2000]
    if not is_instrumental:
        if lyrics:
            payload["lyrics"] = lyrics[:3500]
        elif not lyrics_optimizer:
            payload["lyrics_optimizer"] = True

    raw = call_minimax_api(payload, timeout=120)
    result = _decode_audio_hex(raw)
    result["model"] = model
    return result


# ═══════════════════════════════════════════════
#  YouTube → Audio download
# ═══════════════════════════════════════════════
def download_youtube_audio(yt_url: str) -> dict:
    """Download audio from YouTube, trim to max 6 min, return metadata."""
    job_id = str(uuid.uuid4())[:12]
    out_template = str(AUDIO_DIR / f"yt-{job_id}.%(ext)s")
    final_path = AUDIO_DIR / f"yt-{job_id}.mp3"

    # Step 1: download best audio + convert to mp3
    cmd = [
        YTDLP_BIN,
        "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "--extract-audio", "--audio-format", "mp3",
        "--audio-quality", "192K",
        "--max-filesize", "50M",
        "--user-agent", "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
        "--force-ipv4",
        "--extractor-args", "youtube:player_client=android,ios",
        "--postprocessor-args", f"{FFMPEG_BIN}:-t 360",  # max 6 min
        "-o", out_template,
        "--no-playlist",
        "--no-warnings",
        "--no-check-certificates",
        yt_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise RuntimeError("YouTube download timed out (120s).")

    if result.returncode != 0:
        err = result.stderr[-500:] or result.stdout[-500:] or "Unknown yt-dlp error"
        raise RuntimeError(f"yt-dlp failed: {err}")

    # Find the output file
    actual_files = sorted(AUDIO_DIR.glob(f"yt-{job_id}.*"), key=lambda p: p.stat().st_size, reverse=True)
    if not actual_files:
        raise RuntimeError("yt-dlp completed but no audio file found.")

    audio_path = actual_files[0]
    file_size = audio_path.stat().st_size

    # Get duration with ffprobe
    duration_s = 0
    try:
        probe = subprocess.run(
            [FFMPEG_BIN, "-i", str(audio_path), "-f", "null", "-"],
            capture_output=True, text=True, timeout=30,
        )
        for line in (probe.stderr or "").split("\n"):
            if "Duration" in line:
                # Duration: 00:03:45.12
                parts = line.split("Duration:")[1].strip().split(".")[0].split(":")
                duration_s = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                break
    except Exception:
        pass

    return {
        "job_id": job_id,
        "filename": audio_path.name,
        "size_bytes": file_size,
        "duration_s": duration_s,
        "public_url": f"{MINIMAX_PUBLIC_BASE}/audio/{audio_path.name}",
    }


# ═══════════════════════════════════════════════
#  Cover generation  (music-cover / music-cover-free)
# ═══════════════════════════════════════════════
def generate_cover(audio_url: str, prompt: str = "", lyrics: str = "",
                   model: str = "music-cover-free") -> dict:
    """Call MiniMax music-cover API with a reference audio URL."""
    if not MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is missing.")

    payload: dict = {
        "model": model,
        "audio_url": audio_url,
    }
    if prompt:
        payload["prompt"] = prompt[:300]
    if lyrics:
        payload["lyrics"] = lyrics[:1000]

    raw = call_minimax_api(payload, timeout=300)
    result = _decode_audio_hex(raw)
    result["model"] = model
    return result


# ═══════════════════════════════════════════════
#  HTTP Handler
# ═══════════════════════════════════════════════
class Handler(BaseHTTPRequestHandler):
    def _send_index(self):
        content = INDEX_HTML.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html", ""):
            return self._send_index()
        if self.path.startswith("/audio/"):
            filename = self.path.split("/")[-1]
            filepath = AUDIO_DIR / filename
            if filepath.exists():
                content = filepath.read_bytes()
                ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp3"
                mime = "audio/mpeg" if ext == "mp3" else "audio/wav"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(content)
                return
        if self.path == "/api/health":
            return json_response(self, {
                "ok": True,
                "minimax_configured": bool(MINIMAX_API_KEY),
                "model": "music-2.6-free",
                "cover_model": "music-cover-free",
                "ytdlp_available": os.path.exists(YTDLP_BIN),
            })
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/generate":
            try:
                p = read_json(self)
                prompt = str(p.get("prompt", "")).strip()
                lyrics = str(p.get("lyrics", "")).strip()
                is_instrumental = bool(p.get("is_instrumental", False))
                lyrics_optimizer = bool(p.get("lyrics_optimizer", False))
                model = str(p.get("model", "music-2.6-free")).strip() or "music-2.6-free"
                sample_rate = int(p.get("sample_rate", 44100))
                bitrate = int(p.get("bitrate", 256000))
                audio_format = str(p.get("audio_format", "mp3")).strip() or "mp3"

                if not prompt and not lyrics:
                    raise ValueError("Please provide a prompt or lyrics.")

                result = generate_music(
                    prompt=prompt, lyrics=lyrics,
                    is_instrumental=is_instrumental,
                    lyrics_optimizer=lyrics_optimizer,
                    model=model, sample_rate=sample_rate,
                    bitrate=bitrate, audio_format=audio_format,
                )
                return json_response(self, {"ok": True, **result})
            except Exception as e:
                return json_response(self, {"ok": False, "error": str(e)}, 400)

        if self.path == "/api/cover":
            try:
                p = read_json(self)
                yt_url = str(p.get("youtube_url", "")).strip()
                audio_url_direct = str(p.get("audio_url", "")).strip()
                prompt = str(p.get("prompt", "")).strip()
                lyrics = str(p.get("lyrics", "")).strip()
                model = str(p.get("model", "music-cover-free")).strip() or "music-cover-free"

                if audio_url_direct:
                    # Direct audio URL — skip yt-dlp
                    source_info = {"audio_url": audio_url_direct}
                    cover_audio_url = audio_url_direct
                elif yt_url:
                    # YouTube URL — download first
                    yt_info = download_youtube_audio(yt_url)
                    source_info = {
                        "youtube_url": yt_url,
                        "filename": yt_info["filename"],
                        "duration_s": yt_info["duration_s"],
                        "size_bytes": yt_info["size_bytes"],
                    }
                    cover_audio_url = yt_info["public_url"]
                else:
                    raise ValueError("Please provide a YouTube URL or direct audio URL.")

                # Generate cover
                cover = generate_cover(
                    audio_url=cover_audio_url,
                    prompt=prompt,
                    lyrics=lyrics,
                    model=model,
                )

                return json_response(self, {
                    "ok": True,
                    "source": source_info,
                    **cover,
                })
            except Exception as e:
                return json_response(self, {"ok": False, "error": str(e)}, 400)

        return json_response(self, {"ok": False, "error": "Unknown endpoint"}, 404)


if __name__ == "__main__":
    print(f"🎵 MiniMax Music 2.6 + Cover")
    print(f"🎬 YouTube → Cover available")
    print(f"🚀 http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
