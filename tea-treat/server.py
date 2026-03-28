#!/usr/bin/env python3
"""
請食 Tea - Office group order helper
POC: Create treat → Share link → Collect orders → Show summary
"""

import json
import os
import uuid
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

HOST = os.getenv('TEA_HOST', '127.0.0.1')
PORT = int(os.getenv('TEA_PORT', '8771'))
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def load_treats():
    path = os.path.join(DATA_DIR, 'treats.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_treats(data):
    path = os.path.join(DATA_DIR, 'treats.json')
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_orders():
    path = os.path.join(DATA_DIR, 'orders.json')
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def save_orders(data):
    path = os.path.join(DATA_DIR, 'orders.json')
    with open(path, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_json(h, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    h.send_response(status)
    h.send_header('Content-Type', 'application/json; charset=utf-8')
    h.send_header('Content-Length', str(len(body)))
    h.send_header('Access-Control-Allow-Origin', '*')
    h.send_header('Access-Control-Allow-Headers', 'Content-Type')
    h.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    h.end_headers()
    h.wfile.write(body)


def send_file(h, filepath, content_type='text/html'):
    if not os.path.exists(filepath):
        h.send_response(404)
        h.end_headers()
        return
    with open(filepath, 'rb') as f:
        data = f.read()
    h.send_response(200)
    h.send_header('Content-Type', content_type + '; charset=utf-8')
    h.send_header('Content-Length', str(len(data)))
    h.end_headers()
    h.wfile.write(data)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.end_headers()

    def do_GET(self):
        base = os.path.dirname(__file__)
        path = self.path.rstrip('/')

        if path == '' or path == '/tea-treat':
            return send_file(h, os.path.join(base, 'index.html'))
        if path == '/tea-treat/setup':
            return send_file(h, os.path.join(base, 'setup.html'))
        if path.startswith('/tea-treat/order/'):
            return send_file(h, os.path.join(base, 'order.html'))
        if path.startswith('/tea-treat/summary/'):
            return send_file(h, os.path.join(base, 'summary.html'))

        # API: Get treat info
        if path.startswith('/tea-treat/api/treat/'):
            treat_id = path.split('/tea-treat/api/treat/')[-1]
            treats = load_treats()
            if treat_id in treats:
                return send_json(self, {'ok': True, 'treat': treats[treat_id]})
            return send_json(self, {'ok': False, 'error': '搵唔到呢個茶記'}, 404)

        # API: Get orders for a treat
        if path.startswith('/tea-treat/api/orders/'):
            treat_id = path.split('/tea-treat/api/orders/')[-1]
            orders = load_orders()
            treat_orders = orders.get(treat_id, [])
            return send_json(self, {'ok': True, 'orders': treat_orders})

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            body = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
        except:
            body = {}

        path = self.path.rstrip('/')

        # API: Create treat
        if path == '/tea-treat/api/create':
            treat_id = uuid.uuid4().hex[:8]
            treat = {
                'id': treat_id,
                'title': body.get('title', '請食 Tea'),
                'restaurant': body.get('restaurant', ''),
                'platform': body.get('platform', 'foodpanda'),
                'url': body.get('url', ''),
                'menu': body.get('menu', []),
                'deadline': body.get('deadline', ''),
                'note': body.get('note', ''),
                'created_by': body.get('created_by', ''),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'status': 'open',
            }
            treats = load_treats()
            treats[treat_id] = treat
            save_treats(treats)
            # Init empty orders
            orders = load_orders()
            orders[treat_id] = []
            save_orders(orders)
            return send_json(self, {'ok': True, 'treat_id': treat_id, 'treat': treat})

        # API: Submit order
        if path.startswith('/tea-treat/api/order/'):
            treat_id = path.split('/tea-treat/api/order/')[-1]
            treats = load_treats()
            if treat_id not in treats:
                return send_json(self, {'ok': False, 'error': '搵唔到呢個茶記'}, 404)
            if treats[treat_id].get('status') != 'open':
                return send_json(self, {'ok': False, 'error': '茶記已經截止咗'}, 400)

            orderer = body.get('name', '').strip()
            items = body.get('items', [])
            remark = body.get('remark', '').strip()
            if not orderer:
                return send_json(self, {'ok': False, 'error': '請填你個名'}, 400)
            if not items:
                return send_json(self, {'ok': False, 'error': '請揀至少一樣嘢'}, 400)

            orders = load_orders()
            treat_orders = orders.get(treat_id, [])

            # Check if already ordered - update instead of duplicate
            existing = next((o for o in treat_orders if o['name'] == orderer), None)
            if existing:
                existing['items'] = items
                existing['remark'] = remark
                existing['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            else:
                treat_orders.append({
                    'name': orderer,
                    'items': items,
                    'remark': remark,
                    'ordered_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                })

            orders[treat_id] = treat_orders
            save_orders(orders)
            return send_json(self, {'ok': True, 'message': '落單成功！'})

        # API: Close treat
        if path.startswith('/tea-treat/api/close/'):
            treat_id = path.split('/tea-treat/api/close/')[-1]
            treats = load_treats()
            if treat_id in treats:
                treats[treat_id]['status'] = 'closed'
                save_treats(treats)
                return send_json(self, {'ok': True})
            return send_json(self, {'ok': False}, 404)

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)


if __name__ == '__main__':
    print(f'請食 Tea server on http://{HOST}:{PORT}')
    HTTPServer((HOST, PORT), Handler).serve_forever()
