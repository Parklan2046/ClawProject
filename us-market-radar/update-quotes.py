#!/usr/bin/env python3
import json
import pathlib
import sys
import time
import urllib.request

SYMBOLS = ['OPEN', 'SPY', 'QQQ', 'DIA', 'IWM', '^VIX']
BASE = pathlib.Path('/home/ubuntu/.openclaw/workspace/ClawProject/us-market-radar')
OUT = BASE / 'data' / 'quotes.json'


def fetch_quote(symbol: str):
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1m'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    meta = data['chart']['result'][0]['meta']
    return {
        'symbol': symbol,
        'price': meta.get('regularMarketPrice'),
        'prevClose': meta.get('previousClose'),
        'volume': meta.get('regularMarketVolume'),
        'marketTime': meta.get('regularMarketTime'),
    }


def main():
    quotes = {}
    updated_at = int(time.time())
    for symbol in SYMBOLS:
        quotes[symbol] = fetch_quote(symbol)
    payload = {
        'updatedAt': updated_at,
        'source': 'yahoo-finance-server-side',
        'quotes': quotes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'ok': False, 'error': str(e)}, indent=2), file=sys.stderr)
        raise
