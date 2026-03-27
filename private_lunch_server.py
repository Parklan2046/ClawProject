#!/usr/bin/env python3
import hashlib
import hmac
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.getenv('LUNCH_AUTH_HOST', '127.0.0.1')
PORT = int(os.getenv('LUNCH_AUTH_PORT', '8766'))
PASSWORD_SHA256 = os.getenv('LUNCH_PASSWORD_SHA256', '')
SESSION_SECRET = os.getenv('LUNCH_SESSION_SECRET', 'change-me')
ROOT = Path('/var/www/on9claw/lunch-wallet')
COOKIE_NAME = 'lunch_wallet_session'

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Lunch Wallet · Private Access</title>
  <style>
    :root {
      color-scheme: dark;
      --bg1:#060915; --bg2:#0b1225; --text:#eef4ff; --muted:#96a6c7;
      --line:rgba(255,255,255,.12); --glass:rgba(18,25,48,.58);
    }
    *{box-sizing:border-box} body{margin:0;min-height:100vh;display:grid;place-items:center;
      font-family:Inter,system-ui,sans-serif;color:var(--text);
      background:radial-gradient(circle at top left,rgba(103,217,255,.18),transparent 25%),
      linear-gradient(180deg,var(--bg2),var(--bg1)); padding:18px;}
    .card{width:min(420px,100%); padding:22px; border-radius:28px; background:linear-gradient(180deg,rgba(20,28,52,.66),rgba(14,19,36,.4)); border:1px solid var(--line); backdrop-filter:blur(20px); box-shadow:0 24px 80px rgba(0,0,0,.34)}
    .mark{width:52px;height:52px;border-radius:18px;display:grid;place-items:center;font-size:24px;background:linear-gradient(135deg,#5b85ff,#67d9ff);box-shadow:0 14px 36px rgba(91,133,255,.28);margin-bottom:16px}
    h1{margin:0 0 8px;font-size:1.6rem;letter-spacing:-.03em} p{margin:0 0 16px;color:var(--muted);line-height:1.7}
    label{display:block;margin:0 0 8px;color:var(--muted);font-size:.9rem}
    input{width:100%;padding:12px 14px;border-radius:14px;border:1px solid var(--line);background:rgba(255,255,255,.06);color:var(--text);font:inherit;outline:none}
    button{margin-top:12px;width:100%;padding:12px 14px;border-radius:14px;border:1px solid rgba(125,161,255,.28);background:linear-gradient(135deg,rgba(125,161,255,.18),rgba(103,217,255,.12));color:var(--text);font:inherit;font-weight:800;cursor:pointer}
    .error{margin-top:10px;color:#ffb4b4;font-size:.92rem}
    a{color:#9fc0ff;text-decoration:none} a:hover{text-decoration:underline}
  </style>
</head>
<body>
  <form class="card" method="post" action="/lunch-login">
    <div class="mark">🔒</div>
    <h1>Lunch Wallet</h1>
    <p>Private project access. Enter the password to continue.</p>
    <label for="password">Password</label>
    <input id="password" name="password" type="password" placeholder="Enter password" autofocus />
    <button type="submit">Enter</button>
    {error_html}
    <p style="margin-top:14px"><a href="/">← Back to Clawhub</a></p>
  </form>
</body>
</html>'''


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def make_token() -> str:
    msg = b'lunch-wallet-access'
    return hmac.new(SESSION_SECRET.encode('utf-8'), msg, hashlib.sha256).hexdigest()


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


def send_bytes(h, body: bytes, status=200, ctype='text/html; charset=utf-8', headers=None):
    h.send_response(status)
    h.send_header('Content-Type', ctype)
    h.send_header('Content-Length', str(len(body)))
    if headers:
        for k, v in headers.items():
            h.send_header(k, v)
    h.end_headers()
    h.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/lunch-login', '/lunch-login/'):
            error_html = '<div class="error">Wrong password. Please try again.</div>' if 'error=1' in self.path else ''
            return send_bytes(self, LOGIN_HTML.format(error_html=error_html).encode('utf-8'))
        if path.startswith('/lunch-wallet'):
            if not authed(self.headers.get('Cookie')):
                return self.redirect('/lunch-login')
            rel = path[len('/lunch-wallet'):].lstrip('/') or 'index.html'
            target = (ROOT / rel).resolve()
            if not str(target).startswith(str(ROOT.resolve())) or not target.exists() or target.is_dir():
                target = ROOT / 'index.html'
            ctype = 'text/html; charset=utf-8'
            if target.suffix == '.js': ctype = 'application/javascript; charset=utf-8'
            elif target.suffix == '.css': ctype = 'text/css; charset=utf-8'
            elif target.suffix == '.json': ctype = 'application/json; charset=utf-8'
            return send_bytes(self, target.read_bytes(), ctype=ctype)
        return self.redirect('/')

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ('/lunch-login', '/lunch-login/'):
            return self.redirect('/')
        length = int(self.headers.get('Content-Length', '0'))
        data = self.rfile.read(length).decode('utf-8', 'ignore')
        form = parse_qs(data)
        password = (form.get('password') or [''])[0]
        if PASSWORD_SHA256 and hmac.compare_digest(sha256_hex(password), PASSWORD_SHA256):
            token = make_token()
            self.send_response(302)
            self.send_header('Location', '/lunch-wallet/')
            self.send_header('Set-Cookie', f'{COOKIE_NAME}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800')
            self.end_headers()
            return
        return self.redirect('/lunch-login?error=1')

    def redirect(self, to: str):
        self.send_response(302)
        self.send_header('Location', to)
        self.end_headers()


if __name__ == '__main__':
    print(f'private lunch auth on http://{HOST}:{PORT}')
    HTTPServer((HOST, PORT), Handler).serve_forever()
