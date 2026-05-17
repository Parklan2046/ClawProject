#!/usr/bin/env python3
"""
Stock Investment Report Server
Accepts a stock ticker/name, fetches data via yfinance + web search,
and generates a full investment report in Cantonese via OpenCode Go (DeepSeek V4 Pro).
"""

import json
import os
import re
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import request, error, parse

_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_env_path):
    with open(_env_path, 'r', encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import numpy as np
import pandas as pd
import yfinance as yf

HOST = os.getenv('REPORT_HOST', '127.0.0.1')
PORT = int(os.getenv('REPORT_PORT', '8770'))
OPENCODE_GO_API_KEY = os.getenv('OPENCODE_API_KEY', '')
OPENCODE_GO_URL = 'https://opencode.ai/zen/go/v1/chat/completions'
REPORT_MODEL = os.getenv('REPORT_MODEL', 'deepseek-v4-pro')

CACHE_TTL = int(os.getenv('REPORT_CACHE_TTL', '300'))
_data_cache: dict = {}
REPORTS_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports_log.json')

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
    '快手': '1024.HK', 'kuaishou': '1024.HK',
    '中芯國際': '0981.HK', '中芯国际': '0981.HK', 'smic': '0981.HK',
    '平安保險': '2318.HK', '平安': '2318.HK', 'ping an': '2318.HK',
    '吉利': '0175.HK', 'geely': '0175.HK',
    '海底撈': '6862.HK', '海底捞': '6862.HK', 'haidilao': '6862.HK',
    '聯想': '0992.HK', '联想': '0992.HK', 'lenovo': '0992.HK',
    '商湯': '0020.HK', '商汤': '0020.HK', 'sensetime': '0020.HK',
    '李寧': '2331.HK', '李宁': '2331.HK', 'li ning': '2331.HK',
    '理想汽車': '2015.HK', '理想汽车': '2015.HK', 'li auto': '2015.HK',
    '小鵬': '9868.HK', '小鹏': '9868.HK', 'xpeng': '9868.HK',
    '蔚來': '9866.HK', '蔚来': '9866.HK', 'nio': '9866.HK',
    '蘋果': 'AAPL', '苹果': 'AAPL', 'apple': 'AAPL',
    '英偉達': 'NVDA', '英伟达': 'NVDA', 'nvidia': 'NVDA',
    '特斯拉': 'TSLA', 'tesla': 'TSLA',
    '微軟': 'MSFT', '微软': 'MSFT', 'microsoft': 'MSFT',
    '谷歌': 'GOOGL', 'google': 'GOOGL', 'alphabet': 'GOOGL',
    '亞馬遜': 'AMZN', '亚马逊': 'AMZN', 'amazon': 'AMZN',
    'meta': 'META', 'facebook': 'META',
    '台積電': 'TSM', '台积电': 'TSM', 'tsmc': 'TSM',
    'amd': 'AMD', 'intel': 'INTC', 'netflix': 'NFLX',
    'uber': 'UBER', 'palantir': 'PLTR', 'coinbase': 'COIN',
    'snap': 'SNAP', 'shopify': 'SHOP',
    'spy': 'SPY', 'qqq': 'QQQ', 'iwm': 'IWM',
}


def resolve_ticker(query: str) -> str:
    q = query.strip().lower()
    if q in HK_NAME_MAP:
        return HK_NAME_MAP[q]
    if q.isdigit():
        return f"{q.zfill(4)}.HK"
    return query.strip().upper()


def cache_get(key: str):
    entry = _data_cache.get(key)
    if entry and (time.time() - entry['ts']) < CACHE_TTL:
        return entry['data']
    return None


def cache_set(key: str, data):
    _data_cache[key] = {'data': data, 'ts': time.time()}


def fetch_web_news(company_name: str, ticker: str) -> list:
    """Fetch latest news from Google News RSS for the given company/ticker."""
    news = []
    queries = [company_name, ticker.replace('.HK', '')]
    seen = set()
    for query in queries:
        if not query or query in seen:
            continue
        seen.add(query)
        try:
            encoded = parse.quote(f"{query} stock")
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
            req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with request.urlopen(req, timeout=10) as resp:
                root = ET.fromstring(resp.read().decode('utf-8', 'ignore'))
                for item in root.iter('item'):
                    title = item.findtext('title', '')
                    link = item.findtext('link', '')
                    source = item.findtext('source', '')
                    pubdate = item.findtext('pubDate', '')
                    if title and link:
                        news.append({
                            'title': title,
                            'link': link,
                            'source': source,
                            'date': pubdate,
                            'provider': 'google_news',
                        })
        except Exception:
            pass
    return news[:10]


def fetch_stock_data(ticker: str) -> dict:
    """Fetch comprehensive stock data using yfinance."""
    cached = cache_get(f"stock:{ticker}")
    if cached:
        return cached

    stock = yf.Ticker(ticker)
    info = stock.info or {}

    end = datetime.now()
    start = end - timedelta(days=365)
    hist = stock.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))

    tech = {}
    if len(hist) > 0:
        close = hist['Close'].astype(float)
        vol = hist['Volume'].astype(float)

        tech['current_price'] = round(float(close.iloc[-1]), 2)
        tech['prev_close'] = round(float(close.iloc[-2]), 2) if len(close) >= 2 else None
        tech['change_pct'] = round(float((close.iloc[-1] / close.iloc[-2] - 1) * 100), 2) if len(close) >= 2 else None
        tech['price_1y_ago'] = round(float(close.iloc[0]), 2)
        tech['change_1y_pct'] = round((tech['current_price'] / tech['price_1y_ago'] - 1) * 100, 2) if tech['price_1y_ago'] else None
        tech['high_1y'] = round(float(close.max()), 2)
        tech['low_1y'] = round(float(close.min()), 2)

        if len(close) >= 20:
            tech['ma20'] = round(float(close.tail(20).mean()), 2)
        if len(close) >= 50:
            tech['ma50'] = round(float(close.tail(50).mean()), 2)
        if len(close) >= 200:
            tech['ma200'] = round(float(close.tail(200).mean()), 2)

        tech['avg_volume'] = int(vol.tail(20).mean()) if len(vol) >= 20 else None
        tech['latest_volume'] = int(vol.iloc[-1]) if len(vol) > 0 else None

        # Volume ratio
        if tech['avg_volume'] and tech['latest_volume'] and tech['avg_volume'] > 0:
            tech['vol_ratio'] = round(tech['latest_volume'] / tech['avg_volume'], 2)

        # RSI (14-day, Wilder's smoothing)
        if len(close) >= 15:
            tech['rsi_14'] = _calc_rsi(close, 14)

        # MACD
        if len(close) >= 26:
            macd_line, signal_line, macd_hist = _calc_macd(close)
            tech['macd'] = round(float(macd_line.iloc[-1]), 4) if not macd_line.empty else None
            tech['macd_signal'] = round(float(signal_line.iloc[-1]), 4) if not signal_line.empty else None
            tech['macd_hist'] = round(float(macd_hist.iloc[-1]), 4) if not macd_hist.empty else None
            tech['macd_bullish'] = bool(tech['macd'] and tech['macd_signal'] and tech['macd'] > tech['macd_signal'])

        # Bollinger Bands (20,2)
        if len(close) >= 20:
            bb_upper, bb_mid, bb_lower = _calc_bollinger(close)
            tech['bb_upper'] = round(float(bb_upper.iloc[-1]), 2) if not bb_upper.empty else None
            tech['bb_mid'] = round(float(bb_mid.iloc[-1]), 2) if not bb_mid.empty else None
            tech['bb_lower'] = round(float(bb_lower.iloc[-1]), 2) if not bb_lower.empty else None
            if tech['bb_lower'] and tech['bb_upper'] and tech['bb_lower'] != tech['bb_upper']:
                tech['bb_position'] = round((tech['current_price'] - tech['bb_lower']) / (tech['bb_upper'] - tech['bb_lower']) * 100, 1)

        # ATR (14)
        if len(hist) >= 15:
            tech['atr_14'] = round(float(_calc_atr(hist, 14).iloc[-1]), 2)

        # Historical prices for chart (last 60 trading days)
        chart_close = close.tail(60).tolist()
        tech['chart_prices'] = [round(float(p), 2) for p in chart_close]

        # Recent 5-day trend
        if len(close) >= 5:
            last5 = close.tail(5).tolist()
            tech['recent_prices'] = [round(float(p), 2) for p in last5]

    fund = {
        'name': info.get('longName') or info.get('shortName') or ticker,
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'market_cap': info.get('marketCap'),
        'enterprise_value': info.get('enterpriseValue'),
        'pe_ratio': info.get('trailingPE'),
        'forward_pe': info.get('forwardPE'),
        'peg_ratio': info.get('pegRatio'),
        'pb_ratio': info.get('priceToBook'),
        'dividend_yield': info.get('dividendYield'),
        'eps': info.get('trailingEps'),
        'forward_eps': info.get('forwardEps'),
        'revenue': info.get('totalRevenue'),
        'revenue_growth': info.get('revenueGrowth'),
        'earnings_growth': info.get('earningsGrowth'),
        'profit_margin': info.get('profitMargins'),
        'operating_margin': info.get('operatingMargins'),
        'roe': info.get('returnOnEquity'),
        'roa': info.get('returnOnAssets'),
        'debt_to_equity': info.get('debtToEquity'),
        'current_ratio': info.get('currentRatio'),
        'beta': info.get('beta'),
        'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
        'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
        'fifty_day_avg': info.get('fiftyDayAverage'),
        'two_hundred_day_avg': info.get('twoHundredDayAverage'),
        'recommendation': info.get('recommendationKey'),
        'target_price': info.get('targetMeanPrice'),
        'target_high': info.get('targetHighPrice'),
        'target_low': info.get('targetLowPrice'),
        'num_analysts': info.get('numberOfAnalystOpinions'),
        'currency': info.get('currency', 'USD'),
        'exchange': info.get('exchange', ''),
        'pre_market_price': info.get('preMarketPrice'),
        'post_market_price': info.get('postMarketPrice'),
        'regular_market_previous_close': info.get('regularMarketPreviousClose'),
    }

    # yfinance built-in news
    yf_news = []
    try:
        raw_news = getattr(stock, 'news', None) or []
        for n in raw_news[:8]:
            content = n.get('content', n)
            yf_news.append({
                'title': content.get('title', ''),
                'source': content.get('publisher', content.get('provider', {}).get('displayName', '')),
                'link': content.get('clickThroughUrl', content.get('canonicalUrl', {}).get('url', '')),
                'provider': 'yfinance',
            })
    except Exception:
        pass

    # Web news
    web_news = fetch_web_news(fund['name'], ticker)

    # Merge & deduplicate
    all_news = []
    seen_titles = set()
    for n in web_news + yf_news:
        key = n['title'][:80].lower()
        if key not in seen_titles:
            seen_titles.add(key)
            all_news.append(n)

    result = {
        'ticker': ticker,
        'fundamentals': fund,
        'technicals': tech,
        'news': all_news[:12],
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    cache_set(f"stock:{ticker}", result)
    return result


def _calc_rsi(series: pd.Series, period: int = 14) -> float:
    """RSI using Wilder's smoothing."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.iloc[1:period + 1].mean()
    avg_loss = loss.iloc[1:period + 1].mean()
    for i in range(period + 1, len(gain)):
        avg_gain = (avg_gain * (period - 1) + gain.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss.iloc[i]) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    if avg_gain == 0:
        return 0.0
    rs = avg_gain / avg_loss
    return round(float(100 - (100 / (1 + rs))), 1)


def _calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist


def _calc_bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    mid = series.rolling(window=period).mean()
    std_dev = series.rolling(window=period).std()
    upper = mid + std * std_dev
    lower = mid - std * std_dev
    return upper, mid, lower


def _calc_atr(hist: pd.DataFrame, period: int = 14):
    high = hist['High'].astype(float)
    low = hist['Low'].astype(float)
    close = hist['Close'].astype(float)
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr


def format_number(n):
    if n is None:
        return 'N/A'
    if abs(n) >= 1e12:
        return f"{n/1e12:.2f} 萬億"
    if abs(n) >= 1e8:
        return f"{n/1e8:.2f} 億"
    if abs(n) >= 1e4:
        return f"{n/1e4:.2f} 萬"
    return f"{n:,.2f}"


def safe_pct(n):
    """Safely format a ratio as percentage string. Returns 'N/A' if None."""
    if n is None:
        return 'N/A'
    return f"{n * 100:.2f}%"


def build_analysis_prompt(data: dict) -> str:
    f = data['fundamentals']
    t = data['technicals']
    currency = f.get('currency', 'USD')

    lines = [
        f"▸ 股票代號: {data['ticker']}",
        f"▸ 公司名稱: {f['name']}",
        f"▸ 行業: {f['sector']} / {f['industry']}",
        f"▸ 交易所: {f['exchange']}  貨幣: {currency}",
        f"▸ 數據時間: {data['fetch_time']}",
        "",
        "═══ 基本面 ═══",
        f"- 現價: {t.get('current_price', 'N/A')} {currency}",
        f"- 前收: {t.get('prev_close', 'N/A')} {currency}  變動: {t.get('change_pct', 'N/A')}%",
        f"- 市值: {format_number(f['market_cap'])} {currency}",
        f"- 市盈率 (PE): {f['pe_ratio'] or 'N/A'}",
        f"- 預測市盈率: {f['forward_pe'] or 'N/A'}",
        f"- PEG: {f['peg_ratio'] or 'N/A'}",
        f"- 市淨率 (PB): {f['pb_ratio'] or 'N/A'}",
        f"- 每股盈利 (EPS): {f['eps'] or 'N/A'}",
        f"- 預測 EPS: {f['forward_eps'] or 'N/A'}",
        f"- 股息率: {safe_pct(f['dividend_yield'])}",
        f"- 淨利潤率: {safe_pct(f['profit_margin'])}",
        f"- 營業利潤率: {safe_pct(f['operating_margin'])}",
        f"- ROE: {safe_pct(f['roe'])}",
        f"- ROA: {safe_pct(f['roa'])}",
        f"- 負債/權益比: {f['debt_to_equity'] or 'N/A'}",
        f"- 流動比率: {f['current_ratio'] or 'N/A'}",
        f"- Beta: {f['beta'] or 'N/A'}",
        f"- 收入: {format_number(f['revenue'])} {currency}",
        f"- 收入增長: {safe_pct(f['revenue_growth'])}",
        f"- 盈利增長: {safe_pct(f['earnings_growth'])}",
        "",
        "═══ 技術面 ═══",
        f"- 現價: {t.get('current_price', 'N/A')} {currency}",
        f"- 1年最高: {t.get('high_1y', 'N/A')} {currency}",
        f"- 1年最低: {t.get('low_1y', 'N/A')} {currency}",
        f"- 1年升跌: {t.get('change_1y_pct', 'N/A')}%",
        f"- 20天線 (MA20): {t.get('ma20', 'N/A')} {currency}",
        f"- 50天線 (MA50): {t.get('ma50', 'N/A')} {currency}",
        f"- 200天線 (MA200): {t.get('ma200', 'N/A')} {currency}",
        f"- 52週高位: {f['fifty_two_week_high'] or 'N/A'} {currency}",
        f"- 52週低位: {f['fifty_two_week_low'] or 'N/A'} {currency}",
        f"- RSI(14): {t.get('rsi_14', 'N/A')}",
        f"- MACD: {t.get('macd', 'N/A')}  Signal: {t.get('macd_signal', 'N/A')}  柱: {t.get('macd_hist', 'N/A')}  {'(黃金交叉 bullish)' if t.get('macd_bullish') else '(死亡交叉 bearish)'}",
        f"- Bollinger 上軌: {t.get('bb_upper', 'N/A')}  中軌: {t.get('bb_mid', 'N/A')}  下軌: {t.get('bb_lower', 'N/A')}  位置: {t.get('bb_position', 'N/A')}%",
        f"- ATR(14): {t.get('atr_14', 'N/A')} {currency}",
        f"- 平均成交量(20日): {format_number(t.get('avg_volume', 0))}  最新: {format_number(t.get('latest_volume', 0))}  比率: {t.get('vol_ratio', 'N/A')}x",
    ]

    pre = f.get('pre_market_price')
    post = f.get('post_market_price')
    if pre or post:
        lines.append(f"- 盤前價: {pre or 'N/A'} / 盤後價: {post or 'N/A'} {currency}")

    if t.get('recent_prices'):
        trend = ' → '.join(str(p) for p in t['recent_prices'])
        lines.append(f"\n最近5日走勢: {trend} {currency}")

    if data['news']:
        lines.append("\n═══ 最新新聞 (網路搜尋) ═══")
        for n in data['news']:
            lines.append(f"- [{n.get('source', '')}] {n['title']}")

    lines.append("\n═══ 分析師評級 ═══")
    lines.append(f"- 評級: {f.get('recommendation', 'N/A')}")
    lines.append(f"- 目標價: {f.get('target_price', 'N/A')} {currency} (高: {f.get('target_high', 'N/A')}, 低: {f.get('target_low', 'N/A')})")
    lines.append(f"- 分析師人數: {f.get('num_analysts', 'N/A')}")

    return '\n'.join(lines)


def generate_report(data: dict) -> str:
    stock_info = build_analysis_prompt(data)

    system_prompt = (
        "你係一位資深港股同美股投資分析師，專門用香港廣東話（繁體中文）撰寫投資報告。\n"
        "你嘅分析會考慮基本面、技術面、最新新聞、市場情緒同宏觀因素。\n\n"
        "報告結構必須包括以下章節（用 ## 標題）：\n"
        "## 公司簡介\n"
        "## 基本面分析\n"
        "## 技術面分析\n"
        "## 市場情緒同新聞分析\n"
        "## 風險因素\n"
        "## 投資建議\n"
        "## 綜合評分\n\n"
        "要求：\n"
        "- 用香港廣東話書面語，可以適量用口語化表達\n"
        "- 引述具體數字，用港式表達（如「$XX蚊」、「XX億」）\n"
        "- 技術分析要講清楚趨勢、支持位、阻力位\n"
        "- 新聞部分要綜合最新消息，講出對股價嘅潛在影響\n"
        "- 投資建議要具體明確，唔好模稜兩可\n"
        "- 投資建議必須明確講「買入」/「持有」/「賣出」，唔可以用「中性」\n"
        "- 綜合評分係必須嘅最後一節，必須用「X/10」格式（例如 7/10），並附上簡短評分理由同結論\n"
        "- 如果資料不足，要講明邊度資料唔夠同原因\n"
        "- 唔好用 markdown 粗體（**），直接用普通文字\n"
        "- 唔好寫太長，每節精簡扼要，但必須寫到最尾嘅綜合評分"
    )

    payload = {
        'model': REPORT_MODEL,
        'max_tokens': 4000,
        'temperature': 0.3,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'請根據以下股票數據同最新新聞，撰寫一份完整嘅投資報告：\n\n{stock_info}'},
        ],
    }

    req = request.Request(
        OPENCODE_GO_URL,
        data=json.dumps(payload).encode('utf-8'),
        method='POST',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENCODE_GO_API_KEY}',
            'User-Agent': 'Mozilla/5.0',
        },
    )
    with request.urlopen(req, timeout=150) as resp:
        raw = json.loads(resp.read().decode('utf-8', 'ignore'))

    choices = raw.get('choices') or []
    if choices:
        content = choices[0].get('message', {}).get('content', '').strip()
        cached = cache_get(f"report:{data['ticker']}")
        if not cached:
            cache_set(f"report:{data['ticker']}", content)
        return content
    return '報告生成失敗，請稍後再試。'


def search_stocks(query: str) -> list:
    results = []
    try:
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

    q_lower = query.strip().lower()
    matched_tickers = set(r['ticker'] for r in results)
    for name, ticker in HK_NAME_MAP.items():
        if q_lower in name and ticker not in matched_tickers:
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


def send_json(h, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    h.send_response(status)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Content-Length', str(len(body)))
    h.send_header('Access-Control-Allow-Origin', '*')
    h.send_header('Access-Control-Allow-Headers', 'Content-Type')
    h.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    h.end_headers()
    h.wfile.write(body)


def load_report_log() -> dict:
    if os.path.exists(REPORTS_LOG_FILE):
        try:
            with open(REPORTS_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_report_to_log(ticker: str, company_name: str, report: str, price_data: dict, fetch_time: str):
    log = load_report_log()
    score = None
    score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', report)
    if score_match:
        try:
            score = float(score_match.group(1))
        except ValueError:
            pass
    rec = '持有'
    if re.search(r'(?:強烈建議買入|建議買入|買入|強力買入)', report):
        rec = '買入'
    elif re.search(r'(?:建議賣出|賣出|減持)', report):
        rec = '賣出'
    log[ticker] = {
        'ticker': ticker,
        'company_name': company_name,
        'report': report,
        'score': score,
        'recommendation': rec,
        'current_price': price_data.get('current_price'),
        'change_pct': price_data.get('change_pct'),
        'currency': price_data.get('currency', 'USD'),
        'fetch_time': fetch_time,
    }
    if len(log) > 200:
        sorted_items = sorted(log.items(), key=lambda x: x[1].get('fetch_time', ''), reverse=True)
        log = dict(sorted_items[:200])
    with open(REPORTS_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()

    def do_GET(self):
        if self.path == '/stock-report/api/history':
            try:
                log = load_report_log()
                items = sorted(log.values(), key=lambda x: x.get('fetch_time', ''), reverse=True)
                return send_json(self, {'ok': True, 'reports': items})
            except Exception as e:
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        if self.path.startswith('/stock-report/api/report/'):
            try:
                ticker = parse.unquote(self.path.split('/')[-1])
                log = load_report_log()
                if ticker in log:
                    return send_json(self, {'ok': True, 'report': log[ticker]})
                return send_json(self, {'ok': False, 'error': 'Report not found'}, 404)
            except Exception as e:
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)

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

                cached_report = cache_get(f"report:{ticker}")
                if cached_report:
                    report = cached_report
                else:
                    report = generate_report(data)

                # Save report to persistent log
                fetch_time = data['fetch_time']
                save_report_to_log(ticker, data['fundamentals']['name'], report, {
                    'current_price': data['technicals'].get('current_price'),
                    'change_pct': data['technicals'].get('change_pct'),
                    'currency': data['fundamentals'].get('currency', 'USD'),
                }, fetch_time)

                return send_json(self, {
                    'ok': True,
                    'ticker': ticker,
                    'company_name': data['fundamentals']['name'],
                    'report': report,
                    'data': {
                        'current_price': data['technicals'].get('current_price'),
                        'prev_close': data['technicals'].get('prev_close'),
                        'change_pct': data['technicals'].get('change_pct'),
                        'currency': data['fundamentals'].get('currency', 'USD'),
                        'market_cap': data['fundamentals'].get('market_cap'),
                        'pe_ratio': data['fundamentals'].get('pe_ratio'),
                        'exchange': data['fundamentals'].get('exchange', ''),
                        'sector': data['fundamentals'].get('sector', ''),
                        'chart_prices': data['technicals'].get('chart_prices', []),
                        'ma20': data['technicals'].get('ma20'),
                        'ma50': data['technicals'].get('ma50'),
                        'rsi_14': data['technicals'].get('rsi_14'),
                        'macd_bullish': data['technicals'].get('macd_bullish'),
                        'bb_upper': data['technicals'].get('bb_upper'),
                        'bb_lower': data['technicals'].get('bb_lower'),
                    },
                    'fetch_time': data['fetch_time'],
                })

            except Exception as e:
                traceback.print_exc()
                return send_json(self, {'ok': False, 'error': str(e)}, 500)

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)


if __name__ == '__main__':
    print(f'🦞 stock report server on http://{HOST}:{PORT}')
    print(f'   model: {REPORT_MODEL} (OpenCode Go)  |  cache TTL: {CACHE_TTL}s')
    HTTPServer((HOST, PORT), Handler).serve_forever()
