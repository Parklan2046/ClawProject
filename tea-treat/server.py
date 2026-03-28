#!/usr/bin/env python3
"""
請食 Tea - Office group order helper
POC: Create treat → Share link → Collect orders → Show summary
Storage: SQLite
"""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = os.getenv('TEA_HOST', '127.0.0.1')
PORT = int(os.getenv('TEA_PORT', '8771'))
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'tea.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS treats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT '請食 Tea',
            restaurant TEXT NOT NULL DEFAULT '',
            platform TEXT DEFAULT 'foodpanda',
            url TEXT DEFAULT '',
            menu TEXT DEFAULT '[]',
            deadline TEXT DEFAULT '',
            note TEXT DEFAULT '',
            created_by TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            status TEXT DEFAULT 'open'
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            treat_id TEXT NOT NULL,
            name TEXT NOT NULL,
            items TEXT DEFAULT '[]',
            remark TEXT DEFAULT '',
            ordered_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            FOREIGN KEY (treat_id) REFERENCES treats(id)
        );
        CREATE INDEX IF NOT EXISTS idx_orders_treat ON orders(treat_id);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_treat_name ON orders(treat_id, name);
    """)
    conn.commit()
    conn.close()


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


def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    for field in ('menu', 'items'):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except:
                d[field] = []
    return d


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
            conn = get_db()
            row = conn.execute('SELECT * FROM treats WHERE id=?', (treat_id,)).fetchone()
            conn.close()
            if row:
                return send_json(self, {'ok': True, 'treat': row_to_dict(row)})
            return send_json(self, {'ok': False, 'error': '搵唔到呢個茶記'}, 404)

        # API: Get orders for a treat
        if path.startswith('/tea-treat/api/orders/'):
            treat_id = path.split('/tea-treat/api/orders/')[-1]
            conn = get_db()
            rows = conn.execute('SELECT * FROM orders WHERE treat_id=? ORDER BY ordered_at', (treat_id,)).fetchall()
            conn.close()
            orders = [row_to_dict(r) for r in rows]
            return send_json(self, {'ok': True, 'orders': orders})

        # API: Get consolidated order (for bookmarklet)
        if path.startswith('/tea-treat/api/consolidated/'):
            treat_id = path.split('/tea-treat/api/consolidated/')[-1]
            conn = get_db()
            treat_row = conn.execute('SELECT * FROM treats WHERE id=?', (treat_id,)).fetchone()
            order_rows = conn.execute('SELECT * FROM orders WHERE treat_id=?', (treat_id,)).fetchall()
            conn.close()
            if not treat_row:
                return send_json(self, {'ok': False, 'error': '搵唔到'}, 404)

            treat = row_to_dict(treat_row)
            item_counts = {}
            for o in order_rows:
                order = row_to_dict(o)
                for item in order.get('items', []):
                    name = item.get('name', '')
                    qty = item.get('qty', 1)
                    price = item.get('price', '')
                    if name not in item_counts:
                        item_counts[name] = {'name': name, 'price': price, 'qty': 0, 'people': []}
                    item_counts[name]['qty'] += qty
                    if order['name'] not in item_counts[name]['people']:
                        item_counts[name]['people'].append(order['name'])

            consolidated = sorted(item_counts.values(), key=lambda x: -x['qty'])
            return send_json(self, {
                'ok': True,
                'treat': {'title': treat['title'], 'restaurant': treat['restaurant']},
                'consolidated': consolidated,
                'total_people': len(order_rows),
                'total_items': sum(c['qty'] for c in consolidated),
            })

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
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            menu_json = json.dumps(body.get('menu', []), ensure_ascii=False)
            conn = get_db()
            conn.execute('''INSERT INTO treats (id, title, restaurant, platform, url, menu, deadline, note, created_by, created_at, status)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                         (treat_id, body.get('title', '請食 Tea'), body.get('restaurant', ''),
                          body.get('platform', 'foodpanda'), body.get('url', ''),
                          menu_json, body.get('deadline', ''), body.get('note', ''),
                          body.get('created_by', ''), now, 'open'))
            conn.commit()
            treat_row = conn.execute('SELECT * FROM treats WHERE id=?', (treat_id,)).fetchone()
            conn.close()
            return send_json(self, {'ok': True, 'treat_id': treat_id, 'treat': row_to_dict(treat_row)})

        # API: Submit order
        if path.startswith('/tea-treat/api/order/'):
            treat_id = path.split('/tea-treat/api/order/')[-1]
            conn = get_db()
            treat = conn.execute('SELECT * FROM treats WHERE id=?', (treat_id,)).fetchone()
            if not treat:
                conn.close()
                return send_json(self, {'ok': False, 'error': '搵唔到呢個茶記'}, 404)
            if dict(treat).get('status') != 'open':
                conn.close()
                return send_json(self, {'ok': False, 'error': '茶記已經截止咗'}, 400)

            orderer = body.get('name', '').strip()
            items = body.get('items', [])
            remark = body.get('remark', '').strip()
            if not orderer:
                conn.close()
                return send_json(self, {'ok': False, 'error': '請填你個名'}, 400)
            if not items:
                conn.close()
                return send_json(self, {'ok': False, 'error': '請揀至少一樣嘢'}, 400)

            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            items_json = json.dumps(items, ensure_ascii=False)

            # Upsert: update if exists, insert if not
            existing = conn.execute('SELECT id FROM orders WHERE treat_id=? AND name=?', (treat_id, orderer)).fetchone()
            if existing:
                conn.execute('UPDATE orders SET items=?, remark=?, updated_at=? WHERE id=?',
                             (items_json, remark, now, existing['id']))
            else:
                conn.execute('INSERT INTO orders (treat_id, name, items, remark, ordered_at) VALUES (?,?,?,?,?)',
                             (treat_id, orderer, items_json, remark, now))
            conn.commit()
            conn.close()
            return send_json(self, {'ok': True, 'message': '落單成功！'})

        # API: Close treat
        if path.startswith('/tea-treat/api/close/'):
            treat_id = path.split('/tea-treat/api/close/')[-1]
            conn = get_db()
            conn.execute("UPDATE treats SET status='closed' WHERE id=?", (treat_id,))
            conn.commit()
            conn.close()
            return send_json(self, {'ok': True})

        return send_json(self, {'ok': False, 'error': 'Not found'}, 404)


if __name__ == '__main__':
    init_db()
    print(f'請食 Tea server on http://{HOST}:{PORT}')
    HTTPServer((HOST, PORT), Handler).serve_forever()
