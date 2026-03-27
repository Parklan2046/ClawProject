#!/usr/bin/env python3
import base64
import html
import json
import os
import re
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib import request, error

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "index.html"
HOST = os.getenv("EBOOK_POC_HOST", "127.0.0.1")
PORT = int(os.getenv("EBOOK_POC_PORT", "8765"))
MINIMAX_URL = "https://api.minimax.io/anthropic/v1/messages"
MINIMAX_MODEL = os.getenv("EBOOK_POC_MODEL", "MiniMax-M2.5")
MINIMAX_TTS_URL = "https://api.minimax.io/v1/t2a_v2"
MINIMAX_TTS_MODEL = os.getenv("EBOOK_POC_TTS_MODEL", "speech-02-hd")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MAX_SOURCE_CHARS = 6000
MAX_TTS_CHARS = 2500


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


def strip_tags(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_epub_text(file_bytes: bytes) -> str:
    chunks = []
    with zipfile.ZipFile(io_from_bytes(file_bytes)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
        for name in sorted(names):
            try:
                raw = zf.read(name).decode("utf-8", "ignore")
            except Exception:
                continue
            text = normalize_whitespace(strip_tags(raw))
            if len(text) > 80:
                chunks.append(text)
    return "\n\n".join(chunks)


def io_from_bytes(b: bytes):
    import io
    return io.BytesIO(b)


def extract_text_from_upload(filename: str, file_b64: str) -> str:
    data = base64.b64decode(file_b64)
    lower = filename.lower()
    if lower.endswith(".txt") or lower.endswith(".md"):
        return normalize_whitespace(data.decode("utf-8", "ignore"))
    if lower.endswith(".epub"):
        return extract_epub_text(data)
    raise ValueError("Only .txt, .md, and .epub are supported in this prototype.")


def chunk_source_text(text: str, limit: int = MAX_SOURCE_CHARS) -> str:
    text = normalize_whitespace(text)
    return text[:limit].strip()


def extract_text_blocks(content):
    parts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
    return "\n".join(parts).strip()


def minimax_rewrite_to_cantonese(text: str, style: str = "story"):
    if not MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is missing on this machine.")

    prompt = f"""
You are helping build a proof-of-concept Cantonese story-reading app.

Task:
Transform the input passage into natural SPOKEN Cantonese narration suitable for listening.
Do not summarize away important plot details, but you may lightly rewrite for listening flow.
Keep names and story meaning intact.
Use Traditional Chinese characters.

Return STRICT JSON only in this shape:
{{
  "title": "short title",
  "summary": "one sentence in Cantonese",
  "segments": [
    {{"emotion": "calm", "text": "..."}},
    {{"emotion": "mysterious", "text": "..."}}
  ]
}}

Rules:
- emotions allowed: calm, warm, mysterious, excited, sad, tense, dialogue
- each segment should be short enough for TTS, around 1-3 sentences
- write natural Hong Kong style spoken Cantonese
- avoid markdown
- no explanation outside JSON
- if there is dialogue, make it sound natural in spoken Cantonese

Style preference: {style}

Source passage:
{text}
""".strip()

    payload = {
        "model": MINIMAX_MODEL,
        "max_tokens": 1800,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        MINIMAX_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": MINIMAX_API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:4000]
        raise RuntimeError(f"MiniMax API error {e.code}: {detail}")
    except Exception as e:
        raise RuntimeError(f"MiniMax request failed: {e}")

    parsed = json.loads(raw)
    text_out = extract_text_blocks(parsed.get("content", []))
    if not text_out:
        raise RuntimeError("MiniMax returned no text blocks.")

    cleaned = text_out.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        result = json.loads(cleaned)
    except Exception:
        # fallback if model didn't obey JSON perfectly
        result = {
            "title": "Prototype narration",
            "summary": "已轉成廣東話旁白。",
            "segments": [{"emotion": "calm", "text": cleaned}],
        }

    segments = result.get("segments") or []
    safe_segments = []
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        emotion = str(seg.get("emotion", "calm")).strip().lower() or "calm"
        text_val = str(seg.get("text", "")).strip()
        if text_val:
            safe_segments.append({"emotion": emotion, "text": text_val})

    if not safe_segments:
        raise RuntimeError("No usable narration segments were returned.")

    return {
        "title": str(result.get("title", "Prototype narration")).strip() or "Prototype narration",
        "summary": str(result.get("summary", "已轉成廣東話旁白。 ")).strip() or "已轉成廣東話旁白。",
        "segments": safe_segments,
        "model": MINIMAX_MODEL,
    }


def minimax_tts(text: str, voice_id: str = "cantonese_female", emotion: str = "calm"):
    if not MINIMAX_API_KEY:
        raise RuntimeError("MINIMAX_API_KEY is missing on this machine.")
    text = chunk_source_text(text, MAX_TTS_CHARS)
    if not text:
        raise RuntimeError("No text provided for speech synthesis.")

    speed = 0.96
    pitch = 0
    volume = 1.0
    if emotion == "excited":
        speed = 1.06
        pitch = 1
        volume = 1.05
    elif emotion == "dialogue":
        speed = 1.02
        pitch = 1
    elif emotion == "mysterious":
        speed = 0.88
        pitch = -1
    elif emotion == "sad":
        speed = 0.87
        pitch = -1
        volume = 0.96
    elif emotion == "tense":
        speed = 1.0
        pitch = -1
    elif emotion == "warm":
        speed = 0.93
        pitch = 1

    payload = {
        "model": MINIMAX_TTS_MODEL,
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": volume,
            "pitch": pitch,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        MINIMAX_TTS_URL,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
        },
    )
    try:
        with request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8", "ignore")
    except error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:4000]
        raise RuntimeError(f"MiniMax TTS API error {e.code}: {detail}")
    except Exception as e:
        raise RuntimeError(f"MiniMax TTS request failed: {e}")

    parsed = json.loads(raw)
    base_resp = parsed.get("base_resp") or {}
    if base_resp.get("status_code") not in (0, None):
        raise RuntimeError(f"MiniMax TTS failed: {base_resp.get('status_msg', 'unknown error')}")
    audio_hex = ((parsed.get("data") or {}).get("audio") or "").strip()
    if not audio_hex:
        raise RuntimeError("MiniMax TTS returned no audio data.")
    try:
        audio_bytes = bytes.fromhex(audio_hex)
    except Exception:
        raise RuntimeError("MiniMax TTS returned invalid audio encoding.")
    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    return {
        "mime_type": "audio/mpeg",
        "audio_base64": audio_b64,
        "voice_id": voice_id,
        "emotion": emotion,
        "model": MINIMAX_TTS_MODEL,
    }


def minimax_tts_segments(segments, voice_id: str = "cantonese_female"):
    out = []
    for idx, seg in enumerate(segments, 1):
        if not isinstance(seg, dict):
            continue
        text = str(seg.get("text", "")).strip()
        emotion = str(seg.get("emotion", "calm")).strip().lower() or "calm"
        if not text:
            continue
        audio = minimax_tts(text, voice_id=voice_id, emotion=emotion)
        out.append({
            "index": idx,
            "text": text,
            "emotion": emotion,
            **audio,
        })
    if not out:
        raise RuntimeError("No usable segments provided for speech synthesis.")
    return out


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
        if self.path in ("/", "/index.html"):
            return self._send_index()
        if self.path == "/api/health":
            return json_response(self, {
                "ok": True,
                "minimax_configured": bool(MINIMAX_API_KEY),
                "model": MINIMAX_MODEL,
                "tts_model": MINIMAX_TTS_MODEL,
                "max_source_chars": MAX_SOURCE_CHARS,
            })
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/extract":
            try:
                payload = read_json(self)
                filename = str(payload.get("filename", "upload.txt"))
                file_b64 = str(payload.get("file_base64", ""))
                text = extract_text_from_upload(filename, file_b64)
                text = chunk_source_text(text)
                if not text:
                    raise ValueError("No readable text found in the file.")
                return json_response(self, {"ok": True, "text": text})
            except Exception as e:
                return json_response(self, {"ok": False, "error": str(e)}, 400)

        if self.path == "/api/rewrite":
            try:
                payload = read_json(self)
                source_text = chunk_source_text(str(payload.get("text", "")))
                style = str(payload.get("style", "story"))
                if not source_text:
                    raise ValueError("Please provide some source text first.")
                result = minimax_rewrite_to_cantonese(source_text, style=style)
                return json_response(self, {"ok": True, **result})
            except Exception as e:
                return json_response(self, {"ok": False, "error": str(e)}, 400)

        if self.path == "/api/tts":
            try:
                payload = read_json(self)
                text = str(payload.get("text", "")).strip()
                voice_id = str(payload.get("voice_id", "cantonese_female")).strip() or "cantonese_female"
                emotion = str(payload.get("emotion", "calm")).strip().lower() or "calm"
                result = minimax_tts(text, voice_id=voice_id, emotion=emotion)
                return json_response(self, {"ok": True, **result})
            except Exception as e:
                return json_response(self, {"ok": False, "error": str(e)}, 400)

        if self.path == "/api/tts_segments":
            try:
                payload = read_json(self)
                voice_id = str(payload.get("voice_id", "cantonese_female")).strip() or "cantonese_female"
                segments = payload.get("segments") or []
                result = minimax_tts_segments(segments, voice_id=voice_id)
                return json_response(self, {"ok": True, "segments": result, "voice_id": voice_id, "model": MINIMAX_TTS_MODEL})
            except Exception as e:
                return json_response(self, {"ok": False, "error": str(e)}, 400)

        return json_response(self, {"ok": False, "error": "Unknown endpoint"}, 404)


if __name__ == "__main__":
    print(f"ebook-canto-poc running on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
