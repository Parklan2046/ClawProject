#!/usr/bin/env python3
import json
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse, request, error

HOST = '127.0.0.1'
PORT = 8769
HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json,text/plain,*/*',
    'Origin': 'https://polymarket.com',
    'Referer': 'https://polymarket.com/',
}


def extract_slug(url_or_slug: str) -> str:
    value = (url_or_slug or '').strip()
    if not value:
        return ''
    m = re.search(r'/event/([^/?#]+)', value)
    if m:
        return m.group(1)
    return value.strip('/ ')




def candidate_btc_5m_slugs():
    now = int(time.time())
    base = now - (now % 300)
    candidates = [base, base - 300, base + 300, base - 600, base + 600]
    return [f'btc-updown-5m-{ts}' for ts in candidates]


def resolve_market_slug(raw: str) -> str:
    slug = extract_slug(raw)
    is_btc_5m = (not slug) or slug in ('current-btc-5m', 'auto', 'btc-5m-current') or slug.startswith('btc-updown-5m-')
    if is_btc_5m:
        now = int(time.time())
        base = now - (now % 300)
        candidates = [base + d for d in range(-7200, 7201, 300)]
        candidates.sort(key=lambda ts: abs(ts - base))
        for ts in candidates:
            cand = f'btc-updown-5m-{ts}'
            try:
                fetch_json(f'https://gamma-api.polymarket.com/events/slug/{parse.quote(cand)}')
                return cand
            except Exception:
                continue
    return slug

def fetch_json(url: str):
    req = request.Request(url, headers=HEADERS)
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8', 'ignore'))


def send_json(h, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    h.send_response(status)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Content-Length', str(len(body)))
    h.send_header('Access-Control-Allow-Origin', '*')
    h.send_header('Access-Control-Allow-Headers', 'Content-Type')
    h.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
    h.end_headers()
    h.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.end_headers()

    def do_GET(self):
        parts = parse.urlparse(self.path)
        if parts.path != '/strategy-api/polymarket':
            return send_json(self, {'ok': False, 'error': 'Not found'}, 404)
        q = parse.parse_qs(parts.query)
        slug = extract_slug((q.get('slug') or q.get('url') or [''])[0])
        if not slug:
            return send_json(self, {'ok': False, 'error': 'Missing slug/url'}, 400)
        try:
            event = fetch_json(f'https://gamma-api.polymarket.com/events/slug/{parse.quote(slug)}')
            markets = fetch_json(f'https://gamma-api.polymarket.com/markets?slug={parse.quote(slug)}')
            market = markets[0] if isinstance(markets, list) and markets else {}
            outcomes = market.get('outcomes') or []
            outcome_prices = market.get('outcomePrices') or []
            prices = {}
            for idx, out in enumerate(outcomes):
                try:
                    prices[out] = float(outcome_prices[idx])
                except Exception:
                    prices[out] = outcome_prices[idx] if idx < len(outcome_prices) else None
            return send_json(self, {
                'ok': True,
                'slug': slug,
                'title': event.get('title') or market.get('question'),
                'description': event.get('description') or market.get('description'),
                'active': market.get('active'),
                'closed': market.get('closed'),
                'startDate': market.get('startDate'),
                'endDate': market.get('endDate'),
                'outcomes': outcomes,
                'prices': prices,
                'bestBid': market.get('bestBid'),
                'bestAsk': market.get('bestAsk'),
                'lastTradePrice': market.get('lastTradePrice'),
                'spread': market.get('spread'),
                'volume': market.get('volume'),
                'icon': event.get('icon') or market.get('icon') or event.get('image') or market.get('image'),
                'resolutionSource': event.get('resolutionSource') or market.get('resolutionSource'),
            })
        except error.HTTPError as e:
            detail = e.read().decode('utf-8', 'ignore')[:1000]
            return send_json(self, {'ok': False, 'error': f'HTTP {e.code}: {detail}'}, 500)
        except Exception as e:
            return send_json(self, {'ok': False, 'error': str(e)}, 500)


if __name__ == '__main__':
    print(f'btc strategy api on http://{HOST}:{PORT}')
    HTTPServer((HOST, PORT), Handler).serve_forever()
