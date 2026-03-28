#!/usr/bin/env python3
"""
Stock Investment Report Server
Accepts a stock ticker/name, fetches data via yfinance,
and generates a full investment report in Cantonese using MiMo.
"""

import json
import os
import traceback
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import request, error

import yfinance as yf
import pandas as pd

HOST = os.getenv('REPORT_HOST', '127.0.0.1')
PORT = int(os.getenv('REPORT_PORT', '8770'))
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
REPORT_MODEL = os.getenv('REPORT_MODEL', 'xiaomi/mimo-v2-pro')

# HK stock name → ticker mapping (common ones)
HK_NAME_MAP = {
    '騰訊': '0700.HK', '腾讯': '0700.HK', 'tencent': '0700.HK',
    '阿里巴巴': '9988.HK', '阿里': '9988.HK', 'alibaba': '9988.HK',
    '匯豐': '0005.HK', '汇丰': '0005.HK', 'hsbc': '0005.HK',
    '港交所': '0388.HK', 'hkex': '0388.HK',
    '美團': '3690.HK', '美团': '3690.HK', 'meituan': '3690.HK',
    '小米': '1810.HK', 'xiaomi': '1810.HK',
    '建設銀行': '0939.HK', '建设银行': '0939.HK', 'ccb': '0939.HK',
    '中國銀行': '3988.HK', '中国银行': '3988.HK', 'boc': '3988.HK',
    '工商銀行': '1398.HK', '工商银行': '1398.HK', 'icbc': '1398.HK',
    '友邦': '1299.HK', 'aia': '1299.HK',
    '長和': '0001.HK', '长和': '0001.HK', 'ckh': '0001.HK',
    '新鴻基': '0016.HK', '新鸿基': '0016.HK', 'shk': '0016.HK',
    '恆生銀行': '0011.HK', '恒生银行': '0011.HK', 'hang seng bank': '0011.HK',
    '中移動': '0941.HK', '中移动': '0941.HK', 'china mobile': '0941.HK',
    '比亞迪': '1211.HK', '比亚迪': '1211.HK', 'byd': '1211.HK',
    '網易': '9999.HK', '网易': '9999.HK', 'netease': '9999.HK',
    '京東': '9618.HK', '京东': '9618.HK', 'jd': '9618.HK',
    '百度': '9888.HK', 'baidu': '9888.HK',
    '泡泡瑪特': '9992.HK', '泡泡玛特': '9992.HK', 'pop mart': '9992.HK',
    '農夫山泉': '9633.HK', '农夫山泉': '9633.HK',
    '蘋果': 'AAPL', '苹果': 'AAPL', 'apple': 'AAPL',
    '英偉達': 'NVDA', '英伟达': 'NVDA', 'nvidia': 'NVDA',
    '特斯拉': 'TSLA', 'tesla': 'TSLA',
    '微軟': 'MSFT', '微软': 'MSFT', 'microsoft': 'MSFT',
    '谷歌': 'GOOGL', 'google': 'GOOGL', 'alphabet': 'GOOGL',
    '亞馬遜': 'AMZN', '亚马逊': 'AMZN', 'amazon': 'AMZN',
    'meta': 'META', 'facebook': 'META',
    '台積電': 'TSM', '台积电': 'TSM', 'tsmc': 'TSM',
}


def resolve_ticker(query: str) -> str:
    """Resolve a stock name or ticker to a yfinance ticker."""
    q = query.strip().lower()
    if q in HK_NAME_MAP:
        return HK_NAME_MAP[q]
    # If it looks like a HK stock number (e.g. "700" or "0700")
    if q.isdigit():
        padded = q.zfill(4)
        return f"{padded}.HK"
    # Return as-is (already a ticker)
    return query.strip().upper()


def fetch_stock_data(ticker: str) -> dict:
    """Fetch comprehensive stock data using yfinance."""
    stock = yf.Ticker(ticker)
    info = stock.info or {}

    # Price history (6 months)
    end = datetime.now()
    start = end - timedelta(days=180)
    hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))

    # Technical indicators
    tech = {}
    if len(hist) > 0:
        close = hist['Close']
        tech['current_price'] = round(float(close.iloc[-1]), 2)
        tech['price_6m_ago'] = round(float(close.iloc[0]), 2)
        tech['change_6m_pct'] = round((tech['current_price'] / tech['price_6m_ago'] - 1) * 100, 2)
        tech['high_6m'] = round(float(close.max()), 2)
        tech['low_6m'] = round(float(close.min()), 2)

        # Moving averages
        if len(close) >= 20:
            tech['ma20'] = round(float(close.tail(20).mean()), 2)
        if len(close) >= 50:
            tech['ma50'] = round(float(close.tail(50).mean()), 2)

        # Volume
        vol = hist['Volume']
        tech['avg_volume'] = int(vol.tail(20).mean())
        tech['latest_volume'] = int(vol.iloc[-1])

        # RSI (14-day)
        if len(close) >= 14:
            delta = close.diff()
            gain = delta.clip(lower=0).tail(14).mean()
            loss = (-delta.clip(upper=0)).tail(14).mean()
            if loss != 0:
                rs = gain / loss
                tech['rsi_14'] = round(float(100 - (100 / (1 + rs))), 1)

        # Recent price trend (last 5 days)
        if len(close) >= 5:
            last5 = close.tail(5).tolist()
            tech['recent_prices'] = [round(float(p), 2) for p in last5]

    # Fundamentals
    fund = {
        'name': info.get('longName') or info.get('shortName') or ticker,
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'market_cap': info.get('marketCap'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'pb_ratio': info.get('priceToBook'),
        'dividend_yield': info.get('dividendYield'),
        'eps': info.get('trailingEps'),
        'forward_eps': info.get('forwardEps'),
        'revenue': info.get('totalRevenue'),
        'profit_margin': info.get('profitMargins'),
        'roe': info.get('returnOnEquity'),
        'debt_to_equity': info.get('debtToEquity'),
        'current_ratio': info.get('currentRatio'),
        'beta': info.get('beta'),
        'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
        'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        'recommendation': info.get('recommendationKey'),
        'target_price': info.get('targetMeanPrice'),
        'target_high': info.get('targetHighPrice'),
        'target_low': info.get('targetLowPrice'),
        'num_analysts': info.get('numberOfAnalystOpinions'),
        'currency': info.get('currency', 'USD'),
        'exchange': info.get('exchange', ''),
    }

    # Recent news (from yfinance)
    news = []
    try:
        raw_news = stock.news or []
        for n in raw_news[:5]:
            content = n.get('content', n)
            news.append({
                'title': content.get('title', ''),
                'publisher': content.get('publisher', content.get('provider', {}).get('displayName', '')),
                'link': content.get('clickThroughUrl', content.get('canonicalUrl', {}).get('url', '')),
            })
    except Exception:
        pass

    return {
        'ticker': ticker,
        'fundamentals': fund,
        'technicals': tech,
        'news': news,
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }


def format_number(n):
    """Format large numbers with units."""
    if n is None:
        return 'N/A'
    if abs(n) >= 1e12:
        return f"{n/1e12:.2f} 萬億"
    if abs(n) >= 1e8:
        return f"{n/1e8:.2f} 億"
    if abs(n) >= 1e4:
        return f"{n/1e4:.2f} 萬"
    return f"{n:,.2f}"


def build_analysis_prompt(data: dict) -> str:
    """Build the analysis prompt from stock data."""
    f = data['fundamentals']
    t = data['technicals']
    currency = f.get('currency', 'USD')

    lines = [
        f"股票代號: {data['ticker']}",
        f"公司名稱: {f['name']}",
        f"行業: {f['sector']} / {f['industry']}",
        f"貨幣: {currency}",
        "",
        "== 基本面 ==",
        f"現價: {t.get('current_price', 'N/A')} {currency}",
        f"市值: {format_number(f['market_cap'])} {currency}",
        f"市盈率 (PE): {f['pe_ratio']}",
        f"預測市盈率 (Forward PE): {f['forward_pe']}",
        f"市淨率 (PB): {f['pb_ratio']}",
        f"每股盈利 (EPS): {f['eps']}",
        f"預測EPS: {f['forward_eps']}",
        f"股息率: {f'{f['dividend_yield']*100:.2f}%' if f['dividend_yield'] else 'N/A'}",
        f"淨利潤率: {f'{f['profit_margin']*100:.2f}%' if f['profit_margin'] else 'N/A'}",
        f"ROE: {f'{f['roe']*100:.2f}%' if f['roe'] else 'N/A'}",
        f"負債/股東權益比: {f['debt_to_equity']}",
        f"Beta: {f['beta']}",
        f"收入: {format_number(f['revenue'])} {currency}",
        "",
        "== 技術面 ==",
        f"現價: {t.get('current_price', 'N/A')} {currency}",
        f"半年最高: {t.get('high_6m', 'N/A')} {currency}",
        f"半年最低: {t.get('low_6m', 'N/A')} {currency}",
        f"半年升跌: {t.get('change_6m_pct', 'N/A')}%",
        f"20天線: {t.get('ma20', 'N/A')} {currency}",
        f"50天線: {t.get('ma50', 'N/A')} {currency}",
        f"RSI(14): {t.get('rsi_14', 'N/A')}",
        f"52週高位: {f['fifty_two_week_high']} {currency}",
        f"52週低位: {f['fifty_two_week_low']} {currency}",
        f"平均成交量(20日): {format_number(t.get('avg_volume', 0))}",
        "",
        "== 分析師評級 ==",
        f"評級: {f['recommendation']}",
        f"目標價: {f['target_price']} {currency} (高: {f['target_high']}, 低: {f['target_low']})",
        f"分析師人數: {f['num_analysts']}",
    ]

    if t.get('recent_prices'):
        lines.append(f"\n最近5日價格: {' → '.join(str(p) for p in t['recent_prices'])} {currency}")

    if data['news']:
        lines.append("\n== 最新新聞 ==")
        for n in data['news']:
            lines.append(f"- {n['title']} ({n['publisher']})")

    return '\n'.join(lines)


def generate_report(data: dict) -> str:
    """Generate investment report via OpenRouter/MiMo."""
    stock_info = build_analysis_prompt(data)

    system_prompt = (
        "你係一位資深港股同美股投資分析師，專門用香港廣東話（繁體中文）撰寫投資報告。\n"
        "請根據以下股票資料，撰寫一份完整嘅投資分析報告。\n\n"
        "報告結構必須包括以下章節（用 ## 標題）：\n"
        "## 公司簡介\n"
        "## 基本面分析\n"
        "## 技術面分析\n"
        "## 市場情緒\n"
        "## 風險因素\n"
        "## 投資建議\n"
        "## 綜合評分\n\n"
        "要求：\n"
        "- 用香港廣東話書面語，可以用少少口語化表達\n"
        "- 數字要清晰，用港式表達（如「$XX蚊」、「XX億」）\n"
        "- 建議要具體，唔好模稜兩可\n"
        "- 投資建議必須明確講「買入」/「持有」/「賣出」其中一個\n"
        "- 綜合評分係必須嘅最後一節，必須用「X/10」格式（例如 7/10），並附上簡短評分理由\n"
        "- 如果資料不足，要講明邊度資料唔夠\n"
        "- 唔好用 markdown 粗體（**），直接用普通文字\n"
        "- 唔好寫太長，每節精簡扼要，確保寫到最尾嘅綜合評分"
    )

    payload = {
        'model': REPORT_MODEL,
        'max_tokens': 3500,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'請分析以下股票並撰寫投資報告：\n\n{stock_info}'},
        ],
    }

    req = request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode('utf-8'),
        method='POST',
        headers={
            'content-type': 'application/json',
            'authorization': f'Bearer {OPENROUTER_API_KEY}',
        },
    )
    with request.urlopen(req, timeout=120) as resp:
        raw = json.loads(resp.read().decode('utf-8', 'ignore'))

    choices = raw.get('choices') or []
    if choices:
        return choices[0].get('message', {}).get('content', '').strip()
    return '報告生成失敗，請稍後再試。'


def send_json(h, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    h.send_response(status)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Content-Length', str(len(body)))
    h.send_header('Access-Control-Allow-Origin', '*')
    h.send_header('Access-Control-Allow-Headers', 'Content-Type')
    h.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    h.end_headers()
    h.wfile.write(body)


def search_stocks(query: str) -> list:
    """Search for stocks using yfinance search API."""
    results = []
    try:
        import yfinance as yf
        search = yf.Search(query, max_results=8)
        quotes = getattr(search, 'quotes', []) or []
        for q in quotes:
            results.append({
                'ticker': q.get('symbol', ''),
                'name': q.get('longname') or q.get('shortname') or q.get('symbol', ''),
                'exchange': q.get('exchDisp', q.get('exchange', '')),
                'type': q.get('typeDisp', q.get('quoteType', '')),
                'currency': q.get('currency', ''),
            })
    except Exception:
        pass

    # Also check our local name map
    q_lower = query.strip().lower()
    for name, ticker in HK_NAME_MAP.items():
        if q_lower in name and ticker not in [r['ticker'] for r in results]:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info or {}
                results.insert(0, {
                    'ticker': ticker,
                    'name': info.get('longName') or info.get('shortName') or name,
                    'exchange': info.get('exchange', ''),
                    'type': info.get('quoteType', ''),
                    'currency': info.get('currency', ''),
                })
            except Exception:
                results.insert(0, {
                    'ticker': ticker,
                    'name': name,
                    'exchange': 'HKG',
                    'type': 'EQUITY',
                    'currency': 'HKD',
                })
            break

    return results[:8]


def validate_ticker(ticker: str) -> dict:
    """Validate a ticker exists and return basic info."""
    try:
        import yfinance as yf
        resolved = resolve_ticker(ticker)
        stock = yf.Ticker(resolved)
        info = stock.info or {}
        name = info.get('longName') or info.get('shortName')
        if name:
            return {
                'valid': True,
                'ticker': resolved,
                'name': name,
                'currency': info.get('currency', ''),
                'exchange': info.get('exchange', ''),
            }
    except Exception:
        pass
    return {'valid': False}


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.end_headers()

    def do_POST(self):
        if self.path == '/stock-report/api/search':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
                query = str(body.get('query', '')).strip()
                if len(query) < 1:
                    return send_json(self, {'ok': True, 'results': []})
                results = search_stocks(query)
                return send_json(self, {'ok': True, 'results': results})
            except Exception as e:
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        if self.path == '/stock-report/api/validate':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
                ticker = str(body.get('ticker', '')).strip()
                if not ticker:
                    return send_json(self, {'valid': False})
                result = validate_ticker(ticker)
                return send_json(self, result)
            except Exception as e:
                return send_json(self, {'valid': False, 'error': str(e)}, 500)

        if self.path == '/stock-report/api/analyze':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
                query = str(body.get('ticker', '')).strip()
                if not query:
                    return send_json(self, {'ok': False, 'error': '請輸入股票代號或名稱'}, 400)

                ticker = resolve_ticker(query)
                data = fetch_stock_data(ticker)
                report = generate_report(data)

                return send_json(self, {
                    'ok': True,
                    'ticker': ticker,
                    'company_name': data['fundamentals']['name'],
                    'report': report,
                    'data': {
                        'current_price': data['technicals'].get('current_price'),
                        'currency': data['fundamentals'].get('currency', 'USD'),
                        'market_cap': data['fundamentals'].get('market_cap'),
                        'pe_ratio': data['fundamentals'].get('pe_ratio'),
                    },
                    'fetch_time': data['fetch_time'],
                })

            except Exception as e:
                traceback.print_exc()
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)


if __name__ == '__main__':
    print(f'stock report server on http://{HOST}:{PORT}')
    HTTPServer((HOST, PORT), Handler).serve_forever()
