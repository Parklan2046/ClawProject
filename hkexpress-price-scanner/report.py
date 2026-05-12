"""
HKExpress Price Scanner - HTML Report Generator
Generates a dashboard page showing price history for all routes.
"""
import json
import os
from datetime import datetime


def generate_report(db, config, output_path: str):
    """Generate an HTML dashboard with all price data."""
    routes = config.get("routes", [])
    thresholds = config.get("thresholds", {})

    # Build route data
    routes_data = []
    for route in routes:
        rkey = f"{route['from']}-{route['to']}"
        prices = db.get_latest_prices(route["from"], route["to"], limit=30)
        threshold = thresholds.get(rkey)

        # Calculate stats
        valid_prices = [p for p in prices if p.get("lowest_price")]
        stats = {
            "min": min(p["lowest_price"] for p in valid_prices) if valid_prices else None,
            "max": max(p["lowest_price"] for p in valid_prices) if valid_prices else None,
            "avg": sum(p["lowest_price"] for p in valid_prices) / len(valid_prices) if valid_prices else None,
            "count": len(valid_prices),
        }

        routes_data.append({
            "name": route["name"],
            "from": route["from"],
            "to": route["to"],
            "key": rkey,
            "threshold": threshold,
            "stats": stats,
            "prices": [{
                "date": p["flight_date"],
                "price": p["lowest_price"],
                "scanned": p["scraped_at"] if p.get("scraped_at") else None
            } for p in prices]
        })

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>HKExpress Price Scanner</title>
<style>
:root {{
  --bg: #0f0f1a;
  --card: #1a1a2e;
  --accent: #e94560;
  --text: #eaeaea;
  --dim: #8888aa;
  --green: #00d68f;
  --yellow: #ffaa00;
  --blue: #00b4d8;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  padding: 20px;
  min-height: 100vh;
}}
h1 {{
  text-align: center;
  font-size: 1.8em;
  margin-bottom: 8px;
  color: var(--accent);
}}
.subtitle {{
  text-align: center;
  color: var(--dim);
  margin-bottom: 30px;
  font-size: 0.9em;
}}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}}
.card {{
  background: var(--card);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(233,69,96,0.15);
}}
.card h2 {{
  font-size: 1.1em;
  margin-bottom: 4px;
}}
.route-code {{
  color: var(--dim);
  font-size: 0.85em;
  margin-bottom: 12px;
}}
.stats {{
  display: flex;
  gap: 15px;
  margin-bottom: 16px;
  font-size: 0.9em;
}}
.stat {{
  background: rgba(255,255,255,0.05);
  padding: 8px 14px;
  border-radius: 8px;
}}
.stat-label {{
  color: var(--dim);
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.stat-value {{
  font-weight: 700;
  font-size: 1.15em;
}}
.stat-value.low {{ color: var(--green); }}
.stat-value.med {{ color: var(--yellow); }}
.stat-value.high {{ color: var(--accent); }}
.price-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88em;
}}
.price-table th {{
  text-align: left;
  color: var(--dim);
  font-weight: 500;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}}
.price-table td {{
  padding: 5px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}}
.price-table tr:hover td {{
  background: rgba(255,255,255,0.03);
}}
.price-low {{ color: var(--green); font-weight: 700; }}
.price-ok {{ color: var(--text); }}
.price-na {{ color: var(--dim); font-style: italic; }}
.threshold-line {{
  color: var(--yellow);
  font-size: 0.78em;
  margin-top: 6px;
}}
footer {{
  text-align: center;
  color: var(--dim);
  margin-top: 40px;
  padding: 15px;
  font-size: 0.8em;
}}
.back {{ 
  display: block; 
  text-align: center; 
  color: var(--blue); 
  margin-top: 15px; 
  text-decoration: none; 
  font-size: 0.9em;
}}
.back:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<h1>✈️ HKExpress Price Scanner</h1>
<p class="subtitle">Last updated: {now} · Scans every 6 hours</p>

<div class="grid">
"""

    for rd in routes_data:
        s = rd["stats"]
        prices_html = ""
        for p in rd["prices"][:15]:
            if p["price"]:
                cls = "price-low" if rd["threshold"] and p["price"] <= rd["threshold"] else "price-ok"
                prices_html += f'<tr><td>{p["date"]}</td><td class="{cls}">HK${p["price"]:,.0f}</td></tr>\n'
            else:
                prices_html += f'<tr><td>{p["date"]}</td><td class="price-na">—</td></tr>\n'

        low_cls = "low" if rd["threshold"] and s["min"] and s["min"] <= rd["threshold"] else "med"

        html += f"""
<div class="card">
  <h2>{rd['name']}</h2>
  <div class="route-code">{rd['key']}</div>
  <div class="stats">
    <div class="stat"><div class="stat-label">Lowest</div><div class="stat-value {low_cls}">{f"HK${s['min']:,.0f}" if s['min'] else '—'}</div></div>
    <div class="stat"><div class="stat-label">Avg</div><div class="stat-value">{f"HK${s['avg']:,.0f}" if s['avg'] else '—'}</div></div>
    <div class="stat"><div class="stat-label">Data Points</div><div class="stat-value">{s['count']}</div></div>
  </div>
  <table class="price-table">
    <tr><th>Date</th><th>Price</th></tr>
    {prices_html}
  </table>
  {"<div class='threshold-line'>🎯 Alert threshold: HK$" + f"{rd['threshold']:,.0f}" + "</div>" if rd['threshold'] else ""}
</div>
"""

    html += f"""
</div>

<a class="back" href="/">← Back to Parklan Clawhub</a>
<footer>
  HKExpress Price Scanner · Powered by OpenClaw · {now}
</footer>

</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)

    return output_path
