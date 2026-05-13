#!/usr/bin/env python3
"""
Tea Treat Menu Extractor v2
Extracts menus from Foodpanda / Keeta using Playwright with stealth.
If blocked by captcha, returns instructions for bookmarklet fallback.
"""

import json
import os
import re
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = os.getenv("MENU_EXT_HOST", "127.0.0.1")
PORT = int(os.getenv("MENU_EXT_PORT", "8773"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

STEALTH_JS = """
// Remove automation traces
Object.defineProperty(navigator, 'webdriver', { get: () => false });
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-HK','zh-TW','en'] });
window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {} };
// Override permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (params) => (
  params.name === 'notifications' ? 
    Promise.resolve({state: Notification.permission}) :
    originalQuery(params)
);
"""

EXTRACT_JS = """
(function() {
    // Strategy: find all visible menu items by price pattern
    var pricePattern = /\\$\\s*(\\d+(?:\\.\\d{1,2})?)/;
    var items = [];
    var seenNames = {};
    
    // Walk all elements, find ones with a single price
    document.querySelectorAll('*').forEach(function(el) {
        var text = (el.textContent || '').trim();
        if (text.length > 200 || text.length < 3) return;
        if (el.children.length > 5) return;
        
        var match = text.match(pricePattern);
        if (!match) return;
        var price = match[1];
        
        // Walk up to find the item card
        var container = el;
        for (var i = 0; i < 4; i++) {
            var parent = container.parentElement;
            if (!parent) break;
            var fullText = parent.textContent || '';
            if (fullText.length > 30 && fullText.length < 300) {
                container = parent;
                break;
            }
            container = parent;
        }
        
        var fullText = (container.textContent || '').replace(/\\s+/g, ' ').trim();
        var name = fullText.split('$')[0].replace(/\\$\\d+(\\.\\d+)?/g, '').trim();
        if (!name || name.length < 2 || name.length > 80) return;
        
        var key = name.toLowerCase();
        if (!seenNames[key]) {
            seenNames[key] = true;
            items.push({ name: name, price: price, category: '' });
        }
    });
    
    return { items: items.slice(0, 50), url: window.location.href };
})()
"""


def extract_menu_stealth(url):
    """Try to extract menu using Playwright with stealth."""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1400,900",
            ]
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="zh-HK",
            viewport={"width": 1400, "height": 900},
            extra_http_headers={
                "Accept-Language": "zh-HK,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Ch-Ua": '"Chromium";v="126", "Google Chrome";v="126", "Not?A_Brand";v="99"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
            }
        )
        page = ctx.new_page()
        page.add_init_script(STEALTH_JS)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(8000)  # Wait for React to render menu
            
            # Check if we hit a captcha
            body = page.text_content("body")
            if "captcha" in body.lower() or "denied" in body.lower():
                browser.close()
                return {"ok": False, "error": "captcha", "raw_items": []}
            
            # Extract menu using JS
            result = page.evaluate(EXTRACT_JS)
            browser.close()
            
            items = result.get("items", [])
            if items:
                return {"ok": True, "items": items, "url": url}
            else:
                return {"ok": False, "error": "no_items", "raw_items": []}
                
        except Exception as e:
            browser.close()
            return {"ok": False, "error": str(e), "raw_items": []}


def parse_options(items):
    """Use LLM to enhance menu items with options (ice, sugar, size)."""
    if not items or not OPENROUTER_API_KEY:
        return [{"name": i["name"], "price": str(i.get("price", "")), "options": []} for i in items]
    
    prompt = json.dumps(
        [{"name": i["name"], "price": i.get("price", "")} for i in items[:30]],
        ensure_ascii=False
    )
    try:
        payload = {
            "model": "google/gemini-2.5-flash",
            "max_tokens": 3000,
            "messages": [
                {"role": "system", "content": (
                    "你係香港餐廳menu分析師。每個飲品/食品可能有：冰度(走冰/少冰/正常冰/多冰)、"
                    "甜度(走甜/微糖/半糖/正常甜)、大細(細/中/大)、加配料等選項。"
                    "回JSON array，每個item: name, price, options[{title, required, choices[{name, price:'0'}]}]"
                )},
                {"role": "user", "content": "分析以下menu並補齊選項:\\n" + prompt}
            ]
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + OPENROUTER_API_KEY
            }
        )
        resp = urllib.request.urlopen(req, timeout=60)
        raw = json.loads(resp.read())
        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Extract JSON array from response
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
    
    return [{"name": i["name"], "price": str(i.get("price", "")), "options": []} for i in items]


def send_json(h, p, s=200):
    b = json.dumps(p, ensure_ascii=False).encode()
    h.send_response(s)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(b)))
    h.send_header("Access-Control-Allow-Origin", "*")
    h.end_headers()
    h.wfile.write(b)


class H(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        path = self.path.rstrip("/")
        
        # Caddy strips /menu-ext prefix when proxying
        if path in ("/api/extract", "/menu-ext/api/extract"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode()) if length else {}
                url = body.get("url", "").strip()
                
                if not url:
                    return send_json(self, {"ok": False, "error": "請提供連結"})
                
                is_foodpanda = "foodpanda" in url.lower()
                is_keeta = "keeta" in url.lower()
                
                if not (is_foodpanda or is_keeta):
                    return send_json(self, {"ok": False, "error": "目前只支援 Foodpanda / Keeta"})
                
                # Try Playwright extraction
                result = extract_menu_stealth(url)
                
                if result.get("ok"):
                    items = result["items"]
                    enhanced = parse_options(items)
                    return send_json(self, {
                        "ok": True,
                        "source": "auto",
                        "items": enhanced,
                        "url": url
                    })
                else:
                    # Captcha or no items found - tell client to use bookmarklet
                    return send_json(self, {
                        "ok": False, 
                        "error": result.get("error", "unknown"),
                        "fallback": "bookmarklet",
                        "message": (
                            "Foodpanda/Keeta blocked our automated scanner. "
                            "Please use the bookmarklet to extract the menu:\n\n"
                            "1. Visit the restaurant page in your browser\n"
                            "2. Click the '🧋 Scrape Menu' bookmarklet\n"
                            "3. Copy the JSON result\n"
                            "4. Paste it below"
                        )
                    })
            except Exception as e:
                return send_json(self, {"ok": False, "error": str(e)}, 500)

        if path in ("/api/manual", "/menu-ext/api/manual"):
            # Accept manually pasted JSON menu
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode()) if length else {}
                items = body.get("items", [])
                if not items:
                    return send_json(self, {"ok": False, "error": "請貼上JSON menu數據"})
                enhanced = parse_options(items)
                return send_json(self, {"ok": True, "source": "manual", "items": enhanced})
            except json.JSONDecodeError:
                return send_json(self, {"ok": False, "error": "JSON格式錯誤，請重新貼上"}, 400)
            except Exception as e:
                return send_json(self, {"ok": False, "error": str(e)}, 500)

        return send_json(self, {"ok": False, "error": "Not found"}, 404)


if __name__ == "__main__":
    print(f"Menu Extractor v2 on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
