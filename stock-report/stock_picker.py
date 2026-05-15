#!/usr/bin/env python3
"""
Stock Picker — Scan + Score + AI Recommend
Scores stocks across HK + US markets using yfinance fundamentals + technicals.
Top candidates get AI analysis via DeepSeek V4 Pro (OpenCode).
"""
import json
import os
import re
import time
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
import pandas as pd
import yfinance as yf

HOST = os.getenv('PICKER_HOST', '127.0.0.1')
PORT = int(os.getenv('PICKER_PORT', '8771'))
OPENCODE_API_KEY = os.getenv('OPENCODE_API_KEY', '')
OPENCODE_URL = 'https://opencode.ai/zen/go/v1/chat/completions'
OPENCODE_MODEL = 'deepseek-v4-pro'
CACHE_TTL = 600
MAX_WORKERS = 6

# ─── Stock Universe ───
HK_STOCKS = [
    ('0700.HK', '騰訊'), ('9988.HK', '阿里巴巴'), ('0941.HK', '中移動'),
    ('2318.HK', '平安保險'), ('0175.HK', '吉利'), ('1211.HK', '比亞迪'),
    ('1810.HK', '小米'), ('9618.HK', '京東'), ('9999.HK', '網易'),
    ('1024.HK', '快手'), ('2015.HK', '理想汽車'), ('9868.HK', '小鵬'),
    ('9866.HK', '蔚來'), ('0981.HK', '中芯國際'), ('0020.HK', '商湯'),
    ('2331.HK', '李寧'), ('6862.HK', '海底撈'), ('0992.HK', '聯想'),
    ('0388.HK', '港交所'), ('0005.HK', '滙豐'), ('1299.HK', '友邦'),
    ('0011.HK', '恒生'), ('2388.HK', '中銀香港'), ('0823.HK', '領展'),
    ('1997.HK', '九龍倉置業'), ('0002.HK', '中電'), ('0003.HK', '煤氣'),
    ('0006.HK', '電能'), ('0267.HK', '中信'), ('0177.HK', '江蘇寧滬'),
    ('0168.HK', '青島啤酒'), ('0291.HK', '華潤啤酒'), ('1876.HK', '百威亞太'),
    ('2269.HK', '藥明生物'), ('1093.HK', '石藥'), ('1177.HK', '中國生物製藥'),
    ('3690.HK', '美團'), ('9888.HK', '百度'), ('9992.HK', '泡泡瑪特'),
    ('9633.HK', '農夫山泉'), ('2018.HK', '瑞聲'), ('2382.HK', '舜宇光學'),
    ('0017.HK', '新世界發展'), ('0012.HK', '恒基'), ('0016.HK', '新鴻基'),
    ('0688.HK', '中海外'), ('1109.HK', '華潤置地'), ('0960.HK', '龍湖'),
]

US_STOCKS = [
    ('AAPL', 'Apple'), ('MSFT', 'Microsoft'), ('GOOGL', 'Alphabet'),
    ('AMZN', 'Amazon'), ('NVDA', 'NVIDIA'), ('META', 'Meta'),
    ('TSLA', 'Tesla'), ('AMD', 'AMD'), ('INTC', 'Intel'),
    ('NFLX', 'Netflix'), ('UBER', 'Uber'), ('PLTR', 'Palantir'),
    ('COIN', 'Coinbase'), ('SNOW', 'Snowflake'), ('SHOP', 'Shopify'),
    ('JPM', 'JPMorgan'), ('V', 'Visa'), ('MA', 'Mastercard'),
    ('JNJ', 'Johnson & Johnson'), ('PFE', 'Pfizer'), ('UNH', 'UnitedHealth'),
    ('XOM', 'Exxon'), ('CVX', 'Chevron'), ('BA', 'Boeing'),
    ('CAT', 'Caterpillar'), ('DIS', 'Disney'), ('NKE', 'Nike'),
    ('KO', 'Coca-Cola'), ('PEP', 'PepsiCo'), ('MCD', "McDonald's"),
    ('WMT', 'Walmart'), ('COST', 'Costco'), ('HD', 'Home Depot'),
    ('CRM', 'Salesforce'), ('ADBE', 'Adobe'), ('ORCL', 'Oracle'),
    ('NFLX', 'Netflix'), ('SPOT', 'Spotify'), ('SNAP', 'Snap'),
    ('QCOM', 'Qualcomm'), ('TXN', 'Texas Instruments'), ('AVGO', 'Broadcom'),
    ('TSM', 'TSMC'), ('ASML', 'ASML'), ('MU', 'Micron'),
]

_data_cache: dict = {}

# ─── Data Fetch ───
def fetch_stock_snapshot(ticker: str) -> dict | None:
    """Fetch key metrics for a stock. Returns None on failure."""
    cached = _data_cache.get(f"snap:{ticker}")
    if cached and (time.time() - cached['ts']) < CACHE_TTL:
        return cached['data']
    try:
        s = yf.Ticker(ticker)
        info = s.info or {}
        if not info or 'symbol' not in info:
            return None
        end = datetime.now()
        start = end - timedelta(days=252)
        hist = s.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if hist.empty:
            return None
        close = hist['Close'].astype(float)
        vol = hist['Volume'].astype(float)
        cur = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) >= 2 else cur

        # MA
        ma50 = float(close.tail(50).mean()) if len(close) >= 50 else cur
        ma200 = float(close.tail(200).mean()) if len(close) >= 200 else cur

        # RSI
        rsi = 50
        if len(close) >= 15:
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = (-delta).clip(lower=0)
            avg_gain = gain.iloc[1:15].mean()
            avg_loss = loss.iloc[1:15].mean()
            for i in range(15, len(gain)):
                avg_gain = (avg_gain * 13 + gain.iloc[i]) / 14
                avg_loss = (avg_loss * 13 + loss.iloc[i]) / 14
            rsi = float(100 - 100 / (1 + avg_gain / avg_loss)) if avg_loss != 0 else 100

        # Volume
        avg_vol = float(vol.tail(20).mean()) if len(vol) >= 20 else 0
        vol_ratio = float(vol.iloc[-1]) / avg_vol if avg_vol > 0 else 1

        data = {
            'ticker': ticker,
            'name': info.get('longName') or info.get('shortName', ticker),
            'price': round(cur, 2),
            'change_pct': round((cur / prev - 1) * 100, 2),
            'market_cap': info.get('marketCap'),
            'pe': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg': info.get('pegRatio'),
            'pb': info.get('priceToBook'),
            'revenue_growth': info.get('revenueGrowth'),
            'earnings_growth': info.get('earningsGrowth'),
            'profit_margin': info.get('profitMargins'),
            'roe': info.get('returnOnEquity'),
            'roa': info.get('returnOnAssets'),
            'debt_equity': info.get('debtToEquity'),
            'dividend_yield': info.get('dividendYield'),
            'beta': info.get('beta'),
            'ma50': round(ma50, 2),
            'ma200': round(ma200, 2),
            'rsi_14': rsi,
            'vol_ratio': round(vol_ratio, 2),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'currency': info.get('currency', 'USD'),
            'exchange': info.get('exchange', ''),
            'target_price': info.get('targetMeanPrice'),
            'recommendation': info.get('recommendationKey'),
            'analysts': info.get('numberOfAnalystOpinions'),
        }
        _data_cache[f"snap:{ticker}"] = {'data': data, 'ts': time.time()}
        return data
    except Exception:
        return None


# ─── Scoring Engine ───
def score_stock(d: dict) -> dict:
    """Compute a 0-10 score from fundamental + technical data."""
    score = 5.0  # neutral baseline
    reasons = []

    # Value (max +2)
    pe = d.get('pe')
    pb = d.get('pb')
    peg = d.get('peg')
    if pe is not None and pe > 0:
        if pe < 12: score += 1.5; reasons.append('低PE')
        elif pe < 18: score += 0.8; reasons.append('合理PE')
        elif pe > 40: score -= 0.8; reasons.append('高PE')
    if pb is not None and pb > 0:
        if pb < 1.5: score += 0.5; reasons.append('低PB')
        elif pb > 8: score -= 0.3
    if peg is not None and peg > 0:
        if peg < 1: score += 1.0; reasons.append('PEG<1')
        elif peg > 2.5: score -= 0.5

    # Growth (max +1.5)
    rg = d.get('revenue_growth')
    eg = d.get('earnings_growth')
    if rg is not None:
        if rg > 0.15: score += 0.8; reasons.append('高收入增長')
        elif rg > 0.05: score += 0.4
        elif rg < -0.05: score -= 0.5
    if eg is not None:
        if eg > 0.20: score += 0.7; reasons.append('高盈利增長')
        elif eg > 0.05: score += 0.3
        elif eg < -0.10: score -= 0.5

    # Quality (max +1.5)
    roe = d.get('roe')
    pm = d.get('profit_margin')
    de = d.get('debt_equity')
    if roe is not None:
        if roe > 0.20: score += 0.8; reasons.append('高ROE')
        elif roe > 0.10: score += 0.4
        elif roe < 0: score -= 0.5
    if pm is not None:
        if pm > 0.20: score += 0.5; reasons.append('高利潤率')
        elif pm < 0: score -= 0.5
    if de is not None:
        if de > 200: score -= 0.4
        elif de < 30: score += 0.2

    # Momentum (max +1.5)
    price = d.get('price', 0)
    ma50 = d.get('ma50', 0)
    ma200 = d.get('ma200', 0)
    rsi = d.get('rsi_14', 50)
    if ma50 > 0: 
        if price > ma50: score += 0.5; reasons.append('價>MA50')
        else: score -= 0.3
    if ma200 > 0:
        if price > ma200: score += 0.5; reasons.append('價>MA200')
        else: score -= 0.3
    if ma50 > ma200 > 0: score += 0.3; reasons.append('黃金交叉')
    if rsi < 35: score += 0.3; reasons.append('RSI超賣')
    elif rsi > 75: score -= 0.3

    # Analyst (max +0.5)
    rec = d.get('recommendation', '')
    target = d.get('target_price')
    if rec == 'buy' or rec == 'strong_buy': score += 0.3
    elif rec == 'sell' or rec == 'strong_sell': score -= 0.4
    if target and price > 0:
        upside = (target / price - 1)
        if upside > 0.15: score += 0.2; reasons.append('目標價↑')

    # Dividend bonus
    div = d.get('dividend_yield')
    if div is not None and div > 0.03: score += 0.2; reasons.append('股息>3%')

    score = round(max(0, min(10, score)), 1)

    # Grade
    if score >= 8: grade = '🟢 強烈推薦'
    elif score >= 7: grade = '🟡 推薦'
    elif score >= 5.5: grade = '⚪ 中性'
    elif score >= 4: grade = '🟠 謹慎'
    else: grade = '🔴 避開'

    return {**d, 'score': score, 'grade': grade,
            'score_reasons': reasons[:8],
            'scored_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}


def scan_market(symbols: list) -> list:
    """Fetch + score all stocks in a list. Returns sorted by score desc."""
    results = []
    def _fetch_one(args):
        ticker, name = args
        data = fetch_stock_snapshot(ticker)
        if data:
            return score_stock(data)
        return None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(_fetch_one, s): s for s in symbols}
        for f in as_completed(futures):
            r = f.result()
            if r: results.append(r)

    results.sort(key=lambda x: x['score'], reverse=True)
    return results


# ─── AI Analysis (DeepSeek V4 Pro via OpenCode) ───
def ai_analyze_top(stocks: list, limit: int = 8) -> str:
    """Send top stocks to DeepSeek for a Cantonese investment summary."""
    if not OPENCODE_API_KEY:
        return None
    top = stocks[:limit]
    lines = []
    for i, s in enumerate(top):
        lines.append(
            f"{i+1}. {s['ticker']} {s['name']} — 評分 {s['score']}/10 ({s['grade']})\n"
            f"   現價 {s['price']} {s.get('currency','')} | PE {s.get('pe','N/A')} | "
            f"ROE {_pct(s.get('roe'))} | 市值 {_fmt(s.get('market_cap'))}\n"
            f"   原因: {', '.join(s.get('score_reasons',[]))}"
        )

    prompt = f"""你係一個專業嘅股票分析師。以下係篩選出最高評分嘅股票，請用廣東話寫一個簡潔嘅投資摘要（300字內）：

{chr(10).join(lines)}

請回答：
1. 頭3名最值得留意嘅股票同原因
2. 有冇邊隻潛在風險要小心
3. 整體市場建議（一句）"""

    try:
        req = urllib.request.Request(
            OPENCODE_URL,
            data=json.dumps({
                'model': OPENCODE_MODEL,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 800, 'temperature': 0.5,
                'stream': False,
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENCODE_API_KEY}',
                'User-Agent': 'Mozilla/5.0',
            }
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read())
            choice = body['choices'][0]
            content = choice.get('message', {}).get('content', '').strip()
            if not content:
                content = choice.get('message', {}).get('reasoning_content', '').strip()
            return content or '(AI 分析暫無內容)'
    except Exception as e:
        return f"(AI 分析暫時未能生成: {e})"


# ─── Helpers ───
def _fmt(n):
    if n is None: return 'N/A'
    n = float(n)
    if abs(n) >= 1e12: return f'{n/1e12:.2f}T'
    if abs(n) >= 1e8: return f'{n/1e8:.1f}B'
    if abs(n) >= 1e4: return f'{n/1e4:.1f}M'
    return f'{n:,.0f}'

def _pct(n):
    return f'{n*100:.1f}%' if n is not None else 'N/A'


# ─── HTTP API ───
class PickerHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.end_headers()

    def do_POST(self):
        body = self._read_body()
        if self.path in ('/stock-picker/api/scan', '/scan'):
            self._handle_scan(body)
        else:
            self._json(404, {'error': 'Not found'})

    def _handle_scan(self, body):
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return self._json(400, {'error': 'Invalid JSON'})

        market = data.get('market', 'hk')
        ai = data.get('ai', False)

        if market == 'hk':
            symbols = HK_STOCKS
        elif market == 'us':
            symbols = US_STOCKS
        elif market == 'all':
            symbols = HK_STOCKS + US_STOCKS
        else:
            return self._json(400, {'error': 'market must be hk, us, or all'})

        results = scan_market(symbols)
        ai_text = None
        if ai and results:
            ai_text = ai_analyze_top(results)

        self._json(200, {
            'market': market,
            'total_scanned': len(results),
            'total_attempted': len(symbols),
            'top10': results[:10],
            'all_scored': results,
            'ai_analysis': ai_text,
            'scanned_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })

    def _read_body(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            return self.rfile.read(length).decode('utf-8') if length else ''
        except Exception:
            return ''

    def _json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())

    def log_message(self, format, *args):
        pass  # quiet


def main():
    print(f"📊 Stock Picker on {HOST}:{PORT}")
    print(f"   HK stocks: {len(HK_STOCKS)} | US stocks: {len(US_STOCKS)}")
    print(f"   POST /stock-picker/api/scan")
    HTTPServer((HOST, PORT), PickerHandler).serve_forever()

if __name__ == '__main__':
    main()
