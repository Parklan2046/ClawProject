#!/usr/bin/env python3
"""
Geocode restaurant addresses by fetching Google Maps embed pages and
extracting coordinates from the HTML. No API key required.

Updates fehd-dog-restaurants/_geocache.json and rewrites dog-restaurants/data.js
with real lat/lng values.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_JS = os.path.join(BASE, "dog-restaurants", "data.js")
GEOCACHE = os.path.join(BASE, "fehd-dog-restaurants", "_geocache.json")

def load_geocache():
    if os.path.exists(GEOCACHE):
        with open(GEOCACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_geocache(cache):
    os.makedirs(os.path.dirname(GEOCACHE), exist_ok=True)
    with open(GEOCACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def geocode_google_embed(query):
    """Fetch a Google Maps embed page and extract coordinates."""
    embed_url = f"https://www.google.com/maps?q={urllib.parse.quote(query)}&output=embed"
    req = urllib.request.Request(embed_url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        # Find all decimal numbers, look for HK coordinate pairs
        nums = re.findall(r"(-?\d+\.\d{4,})", raw)
        for i in range(0, len(nums) - 1, 2):
            lat, lng = float(nums[i]), float(nums[i+1])
            if 22.0 < lat < 22.7 and 113.7 < lng < 114.7:
                return lat, lng
        # Try odd offset
        for i in range(1, len(nums) - 1, 2):
            lat, lng = float(nums[i]), float(nums[i+1])
            if 22.0 < lat < 22.7 and 113.7 < lng < 114.7:
                return lat, lng
    except Exception:
        pass
    return None, None

def main():
    # Load current data.js
    with open(DATA_JS, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse DOG_DATA
    ts_match = re.search(r"const DOG_DATA_UPDATED='([^']+)';", content)
    timestamp = ts_match.group(1) if ts_match else ""
    
    data_match = re.search(r"const DOG_DATA=(\{.*\});\s*$", content, re.DOTALL)
    if not data_match:
        print("ERROR: Could not parse data.js")
        sys.exit(1)
    
    data = json.loads(data_match.group(1))
    rows = data["r"]
    print(f"Loaded {len(rows)} restaurants from data.js")
    
    cache = load_geocache()
    
    # Count how many need geocoding
    need_geocoding = []
    for row in rows:
        licence = row[6]
        if licence in cache:
            entry = cache[licence]
            if entry.get("lat") is not None:
                row[7] = entry["lat"]
                row[8] = entry["lng"]
            else:
                need_geocoding.append(row)
        else:
            need_geocoding.append(row)
    
    cached_ok = sum(1 for r in rows if r[7] is not None)
    print(f"Cache: {cached_ok} already geocoded, {len(need_geocoding)} to geocode")
    
    if not need_geocoding:
        print("All restaurants geocoded!")
    else:
        success = 0
        fail = 0
        total = len(need_geocoding)
        for i, row in enumerate(need_geocoding, 1):
            licence = row[6]
            en_name = row[0]
            address_en = row[5] if len(row) > 5 else ""
            address_zh = row[4] if len(row) > 4 else ""
            
            # Try English address first, fall back to Chinese
            query = f"{address_en}, Hong Kong" if address_en else f"{address_zh}, Hong Kong"
            query = " ".join(query.split())
            
            lat, lng = geocode_google_embed(query)
            
            if lat is None and address_zh and address_zh != address_en:
                # Try Chinese address
                query2 = f"{address_zh} {row[1]} Hong Kong"
                lat, lng = geocode_google_embed(query2)
            
            cache[licence] = {"lat": lat, "lng": lng}
            row[7] = lat
            row[8] = lng
            
            if lat is not None:
                success += 1
            else:
                fail += 1
            
            safe_name = en_name[:35].encode("ascii", "replace").decode("ascii")
            status = f"{lat:.4f}, {lng:.4f}" if lat else "null"
            if i % 10 == 0 or i == total:
                print(f"  [{i}/{total}] {safe_name:35s} -> {status} (ok:{success} fail:{fail})")
            
            # Save cache periodically
            if i % 50 == 0:
                save_geocache(cache)
            
            time.sleep(0.5)  # Be polite to Google
        
        save_geocache(cache)
        print(f"\nGeocoding complete: {success} success, {fail} failed out of {total}")
    
    # Rewrite data.js with coordinates
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    ts_line = f"const DOG_DATA_UPDATED='{timestamp}';\n" if timestamp else ""
    new_content = f"{ts_line}const DOG_DATA={compact};\n"
    
    with open(DATA_JS, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    geocoded = sum(1 for r in rows if r[7] is not None)
    print(f"data.js rewritten: {len(rows)} restaurants, {geocoded} geocoded, {len(rows) - geocoded} missing coords")

if __name__ == "__main__":
    main()
