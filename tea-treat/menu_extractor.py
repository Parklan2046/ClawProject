#!/usr/bin/env python3
import json, os, re, sys, time, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = os.getenv("MENU_EXT_HOST", "127.0.0.1")
PORT = int(os.getenv("MENU_EXT_PORT", "8773"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Default Hong Kong address for delivery
DEFAULT_LAT = 22.28
DEFAULT_LNG = 114.17

def extract_menu(url):
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="zh-HK"
        )
        page = context.new_page()
        
        # Set delivery address via cookie/localStorage injection
        # Navigate to restaurant
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        # Try to click "Enter address manually" or similar
        try:
            # Look for address input
            addr_input = page.query_selector("input[placeholder*=address], input[placeholder*=地址], input[data-testid*=address]")
            if addr_input:
                addr_input.fill("Central, Hong Kong")
                page.wait_for_timeout(1000)
                # Press enter or click search
                addr_input.press("Enter")
                page.wait_for_timeout(3000)
        except:
            pass
        
        # Try to dismiss any popups/modals
        try:
            close_btns = page.query_selector_all("button[class*=close], button[aria-label*=close], button[aria-label*=Close]")
            for btn in close_btns[:3]:
                try:
                    btn.click()
                    page.wait_for_timeout(500)
                except:
                    pass
        except:
            pass
        
        page.wait_for_timeout(5000)
        
        # Extract menu from __PRELOADED_STATE__ or DOM
        items = []
        restaurant = ""
        
        # Method 1: __PRELOADED_STATE__
        state_js = 'document.querySelector("script[id*=PRELOADED]") != null'
        try:
            has_state = page.evaluate(state_js)
            if has_state:
                state_text = page.evaluate('document.querySelector("script[id*=PRELOADED]").textContent.substring(0, 50000)')
                if state_text:
                    try:
                        state = json.loads(state_text)
                        v = state.get("vendor", {}).get("data", {})
                        restaurant = v.get("name", "")
                        for m in v.get("menus", []):
                            for cat in m.get("menuCategories", []):
                                for prod in cat.get("products", []):
                                    items.append({
                                        "name": prod.get("name", ""),
                                        "price": str(prod.get("minimumPrice", prod.get("price", 0))),
                                        "desc": prod.get("description", ""),
                                        "has_options": len(prod.get("modifierGroups", [])) > 0,
                                        "category": cat.get("name", "")
                                    })
                    except:
                        pass
        except:
            pass
        
        # Method 2: DOM extraction
        if not items:
            try:
                page.wait_for_selector("[data-testid*=product]", timeout=10000)
            except:
                pass
            page.wait_for_timeout(2000)
            
            dom_js = """
            (function() {
                var items = [];
                document.querySelectorAll("[data-testid*=product]").forEach(function(el) {
                    var n = el.querySelector("[data-testid*=name], [data-testid*=title]");
                    var p = el.querySelector("[data-testid*=price]");
                    var d = el.querySelector("[data-testid*=description]");
                    if (n && n.innerText.trim().length > 1) {
                        items.push({
                            name: n.innerText.trim(),
                            price: p ? p.innerText.replace(/[^0-9.]/g, "") : "",
                            desc: d ? d.innerText.trim() : "",
                            has_options: false,
                            category: ""
                        });
                    }
                });
                return items;
            })()
            """
            try:
                items = page.evaluate(dom_js)
            except:
                items = []
        
        # Method 3: Try with class selectors
        if not items:
            dom_js2 = """
            (function() {
                var items = [];
                document.querySelectorAll(".product-tile, [class*=product-card]").forEach(function(el) {
                    var n = el.querySelector("[class*=name], [class*=title]");
                    var p = el.querySelector("[class*=price]");
                    if (n && n.innerText.trim().length > 1) {
                        items.push({
                            name: n.innerText.trim(),
                            price: p ? p.innerText.replace(/[^0-9.]/g, "") : "",
                            desc: "",
                            has_options: false,
                            category: ""
                        });
                    }
                });
                return items;
            })()
            """
            try:
                items = page.evaluate(dom_js2)
            except:
                items = []
        
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
                    "回JSON array格式：name, price, options(title,required,choices[name,price])。\n\n"
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
                return send_json(self, {"ok": False, "error": "搵唔到menu - 請確認餐廳連結正確，或用手動貼JSON方式"}, 400)
            enhanced = parse_options(items)
            return send_json(self, {"ok": True, "restaurant": raw.get("restaurant", ""), "items": enhanced, "url": url})
        except Exception as e:
            return send_json(self, {"ok": False, "error": str(e)}, 500)


if __name__ == "__main__":
    print(f"Menu Extractor on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), H).serve_forever()
