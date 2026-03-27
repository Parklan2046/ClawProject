#!/usr/bin/env python3
import base64
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HOST = os.getenv('SPOTIFY_DASH_HOST', '127.0.0.1')
PORT = int(os.getenv('SPOTIFY_DASH_PORT', '8767'))
BASE = Path(os.getenv('SPOTIFY_DASH_BASE', '/opt/spotify-dashboard/credentials/spotify'))
ACCOUNT = os.getenv('SPOTIFY_DASH_ACCOUNT', 'main')
PASSWORD_SHA256 = os.getenv('SPOTIFY_DASH_PASSWORD_SHA256', '')
SESSION_SECRET = os.getenv('SPOTIFY_DASH_SESSION_SECRET', 'change-me')
COOKIE_NAME = 'spotify_dash_session'


def resolve_paths(account='main'):
    app = BASE / account / 'app.json'
    oauth = BASE / account / 'oauth.json'
    return app, oauth


def load_json(path):
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))


def refresh_access_token(account='main'):
    app_path, oauth_path = resolve_paths(account)
    app = load_json(app_path)
    oauth = load_json(oauth_path)
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': oauth['refresh_token'],
    }).encode()
    req = urllib.request.Request('https://accounts.spotify.com/api/token', data=data, method='POST')
    auth = base64.b64encode(f"{app['clientId']}:{app['clientSecret']}".encode()).decode()
    req.add_header('Authorization', f'Basic {auth}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    oauth['access_token'] = payload['access_token']
    oauth['expires_in'] = payload.get('expires_in', 3600)
    oauth['refreshed_at'] = int(time.time())
    save_json(oauth_path, oauth)
    return oauth['access_token']


def api_request(method, url, token, payload=None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    if payload is not None:
        req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode() or '{}'
        if body:
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {'raw': body}
        return {}


def compact_track(item):
    album = item.get('album', {}) or {}
    images = album.get('images') or []
    return {
        'name': item.get('name'),
        'artists': ', '.join(a.get('name', '') for a in item.get('artists', [])),
        'uri': item.get('uri'),
        'album': album.get('name'),
        'image': images[0]['url'] if images else None,
    }


def get_devices(token):
    return api_request('GET', 'https://api.spotify.com/v1/me/player/devices', token)


def get_active_device_id(token):
    devices = get_devices(token).get('devices', [])
    active = next((d for d in devices if d.get('is_active')), None)
    if active:
        return active.get('id'), devices
    if devices:
        return devices[0].get('id'), devices
    return None, devices


def queue_state(token):
    return api_request('GET', 'https://api.spotify.com/v1/me/player/queue', token)


def search_track(token, query):
    q = urllib.parse.quote(query)
    return api_request('GET', f'https://api.spotify.com/v1/search?q={q}&type=track&limit=5', token)


def play_uri(token, uri):
    device_id, devices = get_active_device_id(token)
    if not device_id:
        raise RuntimeError('No Spotify device found. Open Spotify on your phone first.')
    api_request('PUT', f'https://api.spotify.com/v1/me/player/play?device_id={urllib.parse.quote(device_id)}', token, payload={'uris': [uri]})
    return device_id, devices


def queue_uri(token, uri):
    device_id, devices = get_active_device_id(token)
    if not device_id:
        raise RuntimeError('No Spotify device found. Open Spotify on your phone first.')
    api_request('POST', f'https://api.spotify.com/v1/me/player/queue?uri={urllib.parse.quote(uri)}&device_id={urllib.parse.quote(device_id)}', token)
    return device_id, devices


def pause(token):
    device_id, devices = get_active_device_id(token)
    if not device_id:
        raise RuntimeError('No Spotify device found. Open Spotify on your phone first.')
    api_request('PUT', f'https://api.spotify.com/v1/me/player/pause?device_id={urllib.parse.quote(device_id)}', token, payload={})
    return device_id, devices


def next_track(token):
    device_id, devices = get_active_device_id(token)
    if not device_id:
        raise RuntimeError('No Spotify device found. Open Spotify on your phone first.')
    api_request('POST', f'https://api.spotify.com/v1/me/player/next?device_id={urllib.parse.quote(device_id)}', token, payload={})
    return device_id, devices


def previous_track(token):
    device_id, devices = get_active_device_id(token)
    if not device_id:
        raise RuntimeError('No Spotify device found. Open Spotify on your phone first.')
    api_request('POST', f'https://api.spotify.com/v1/me/player/previous?device_id={urllib.parse.quote(device_id)}', token, payload={})
    return device_id, devices


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def make_token() -> str:
    return hmac.new(SESSION_SECRET.encode('utf-8'), b'spotify-dashboard-access', hashlib.sha256).hexdigest()


def authed(cookie_header: str | None) -> bool:
    if not cookie_header:
        return False
    token = None
    for part in cookie_header.split(';'):
        part = part.strip()
        if part.startswith(COOKIE_NAME + '='):
            token = part.split('=', 1)[1]
            break
    return bool(token) and hmac.compare_digest(token, make_token())


def parse_json_body(handler):
    length = int(handler.headers.get('Content-Length', '0'))
    raw = handler.rfile.read(length)
    return json.loads(raw.decode('utf-8')) if raw else {}


def send_json(handler, payload, status=200, extra_headers=None):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    if extra_headers:
        for k, v in extra_headers.items():
            handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/spotify-api/status'):
            try:
                token = refresh_access_token(ACCOUNT)
                q = queue_state(token)
                devices = get_devices(token).get('devices', [])
                payload = {
                    'ok': True,
                    'currently_playing': compact_track(q.get('currently_playing', {}) or {}),
                    'queue': [compact_track(i) for i in (q.get('queue') or [])[:8]],
                    'devices': [
                        {
                            'name': d.get('name'),
                            'type': d.get('type'),
                            'is_active': d.get('is_active'),
                            'volume_percent': d.get('volume_percent'),
                        } for d in devices
                    ],
                }
                return send_json(self, payload)
            except Exception as e:
                return send_json(self, {'ok': False, 'error': str(e)}, 500)
        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)

    def do_POST(self):
        if self.path.startswith('/spotify-api/login'):
            try:
                data = parse_json_body(self)
                password = str(data.get('password', ''))
                if PASSWORD_SHA256 and hmac.compare_digest(sha256_hex(password), PASSWORD_SHA256):
                    return send_json(self, {'ok': True}, 200, {
                        'Set-Cookie': f'{COOKIE_NAME}={make_token()}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800'
                    })
                return send_json(self, {'ok': False, 'error': 'Wrong password'}, 403)
            except Exception as e:
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        if self.path.startswith('/spotify-api/action'):
            if not authed(self.headers.get('Cookie')):
                return send_json(self, {'ok': False, 'error': 'Unauthorized'}, 401)
            try:
                data = parse_json_body(self)
                action = str(data.get('action', '')).strip().lower()
                query = str(data.get('query', '')).strip()
                token = refresh_access_token(ACCOUNT)

                if action == 'pause':
                    device_id, _ = pause(token)
                    return send_json(self, {'ok': True, 'action': 'pause', 'device_id': device_id})
                if action == 'next':
                    device_id, _ = next_track(token)
                    return send_json(self, {'ok': True, 'action': 'next', 'device_id': device_id})
                if action == 'previous':
                    device_id, _ = previous_track(token)
                    return send_json(self, {'ok': True, 'action': 'previous', 'device_id': device_id})
                if action == 'search':
                    result = search_track(token, query)
                    tracks = [compact_track(item) for item in result.get('tracks', {}).get('items', [])]
                    return send_json(self, {'ok': True, 'results': tracks})
                if action == 'play':
                    result = search_track(token, query)
                    items = result.get('tracks', {}).get('items', [])
                    if not items:
                        raise RuntimeError(f'No track found for query: {query}')
                    first = items[0]
                    device_id, _ = play_uri(token, first['uri'])
                    return send_json(self, {'ok': True, 'action': 'play', 'device_id': device_id, 'track': compact_track(first)})
                if action in ('add', 'queue'):
                    result = search_track(token, query)
                    items = result.get('tracks', {}).get('items', [])
                    if not items:
                        raise RuntimeError(f'No track found for query: {query}')
                    first = items[0]
                    device_id, _ = queue_uri(token, first['uri'])
                    return send_json(self, {'ok': True, 'action': 'queue', 'device_id': device_id, 'track': compact_track(first)})
                return send_json(self, {'ok': False, 'error': 'Unsupported action'}, 400)
            except Exception as e:
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)


if __name__ == '__main__':
    print(f'spotify dashboard api on http://{HOST}:{PORT}')
    HTTPServer((HOST, PORT), Handler).serve_forever()
