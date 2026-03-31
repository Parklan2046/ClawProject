#!/usr/bin/env python3
import json, os, re, sys, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = os.getenv("MENU_EXT_HOST", "127.0.0.1")
PORT = int(os.getenv("MENU_EXT_PORT", "8773"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

EXTRACT_JS = """(function() {
    var items = [];
    document.querySelectorAll("[data-testid=menu-product]").forEach(function(el) {
        var n = el.querySelector("[data-testid=menu-product-name]");
        var p = el.querySelector("[data-testid=menu-product-price]");
        var d = el.querySelector("[data-testid=menu-product-description]");
        if (n) {
            items.push({
                name: n.innerText.trim(),
                price: p ? p.innerText.replace(/[^0-9.]/g, "") : "",
                desc: d ? d.innerText.trim() : "",
                has_options: d ? (d.innerText.indexOf("\\u9078\\u64c7") > -1 || d.innerText.indexOf("\\u51b0") > -1 || d.innerText.indexOf("\\u7cd6") > -1) : false,
                category: ""
            });
        }
    });
    return items;
})()"""

def extract_menu(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url, timeout=30000, wait_until="networkidle")
        
        # Wait for menu to load
        try:
            page.wait_for_selector("[data-testid=menu-product]", timeout=30000)
        except:
            pass
        page.wait_for_timeout(3000)
        
        # Extract restaurant name
        restaurant = page.evaluate("document.querySelector('h1')?.innerText || ''")
        
        # Extract menu items
        items = page.evaluate(EXTRACT_JS)
        
        browser.close()
        return {"restaurant": restaurant, "items": items, "url": url}


def parse_options(items):
    if not items:
        return items
    prompt = json.dumps(
        [{"name": i["name"], "desc": i.get("desc", ""), "price": i.get("price", "")} for i in items[:25]],
        ensure_ascii=False
    )
    try:
        payload = {
            "model": "xiaomi/mimo-v2-pro",
            "max_tokens": 3000,
            "messages": [
                {"role": "system", "content": "你係香港茶餐廳menu分析師。淨係回JSON array。"},
                {"role": "user", "content": (
                    "以下係menu項目，請為每個項目補齊options（冰度、甜度等）。"
                    "回JSON array格式：name, price, options(title,required,choices[name,price])。\\n\\n"
                    + prompt
                )}
            ]
        }
        req = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(payload).encode(),
            headers={
                "content-type": "application/json",
                "authorization": "Bearer " + OPENROUTER_API_KEY
            }
        )
        resp = urllib.request.urlopen(req, timeout=60)
        raw = json.loads(resp.read())
        content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
        m = re.search(r"\\[.*\\]", content, re.DOTALL)
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
        if self.path != "/menu-ext/api/extract":
            return send_json(self, {"ok": False, "error": "Not found"}, 404)
        try:
            l = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(l).decode()) if l else {}
            url = body.get("url", "").strip()
            if not url or "foodpanda" not in url.lower():
                return send_json(self, {"ok": False, "error": "請提供Foodpanda連結"}, 400)
            raw = extract_menu(url)
            items = raw.get("items", [])
            if not items:
                return send_json(self, {"ok": False, "error": "搵唔到menu"}, 400)
            enhanced = parse_options(items)
            return send_json(self, {"ok": True, "restaurant": raw.get("restaurant", ""), "items": enhanced, "url": url})
        except Exception as e:
            return send_json(self, {"ok": False, "error": str(e)}, 500)


if __name__ == "__main__":
    print(f"Menu Extractor on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
