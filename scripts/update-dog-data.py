#!/usr/bin/env python3
"""
Fetch live data from FEHD's public API and regenerate dog-restaurants/data.js.

Data source: https://www.fehd.gov.hk/english/licensing/dog_restaurants/getData.php
Old source (dead): .../dog_restaurants/fulllist.pdf (returns 404 now)

The API returns richer data than the PDF ever did:
  - English + Traditional Chinese + Simplified Chinese for name, district, address
  - house_rule field (currently empty but may be populated later)

This script produces data.js in the SAME format the templates expect:
  const DOG_DATA = {d:[districts], r:[[en,zh,district_zh,address_zh,licence],...]}

Exit codes:
  0 = data unchanged (or updated successfully)
  1 = fetch error
  2 = parse error
"""

import hashlib
import json
import os
import sys
import urllib.request

API_URL = "https://www.fehd.gov.hk/english/licensing/dog_restaurants/getData.php"
REFERER = "https://www.fehd.gov.hk/tc_chi/licensing/dog_restaurants/dog_restaurants_list.html"
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "dog-restaurants", "data.js")
HASH_PATH = os.path.join(os.path.dirname(__file__), "..", "dog-restaurants", ".data-hash")


def fetch_api():
    """Fetch the live JSON array from FEHD's API."""
    req = urllib.request.Request(API_URL)
    req.add_header("User-Agent", "Mozilla/5.0 (ClawProject dog-restaurants updater)")
    req.add_header("Referer", REFERER)
    req.add_header("Accept", "application/json")

    print(f"Fetching {API_URL} ...")
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8-sig")

    print(f"Downloaded {len(raw)} bytes")
    data = json.loads(raw)

    if not isinstance(data, list):
        print(f"ERROR: Expected a JSON array, got {type(data).__name__}")
        sys.exit(2)

    print(f"Parsed {len(data)} restaurant records")
    return data


def transform(records):
    """Convert API records to the compact DOG_DATA format."""
    districts = []
    district_seen = set()
    rows = []

    for r in records:
        en = (r.get("shop_sign_en") or "").strip().replace("\n", " ")
        zh = (r.get("shop_sign_tc") or en).strip().replace("\n", " ")
        district = (r.get("district_tc") or "").strip()
        address = (r.get("address_tc") or "").strip().replace("\n", " ")
        licence = (r.get("licence") or "").strip()

        if not en and not zh:
            continue

        if district and district not in district_seen:
            districts.append(district)
            district_seen.add(district)

        rows.append([en, zh, district, address, licence])

    return {"d": districts, "r": rows}


def generate_js(data):
    """Produce the data.js file content."""
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"const DOG_DATA={compact};\n"


def get_data_hash(data):
    """Stable hash of the transformed data for change detection."""
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def main():
    records = fetch_api()
    data = transform(records)

    new_hash = get_data_hash(data)
    old_hash = ""
    if os.path.exists(HASH_PATH):
        with open(HASH_PATH, "r") as f:
            old_hash = f.read().strip()

    print(f"Old hash: {old_hash or '(none)'}")
    print(f"New hash: {new_hash}")

    if new_hash == old_hash:
        print("No changes detected. Skipping file write.")
        return

    js_content = generate_js(data)
    js_size = len(js_content.encode("utf-8"))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(js_content)

    with open(HASH_PATH, "w") as f:
        f.write(new_hash)

    # District counts for the commit message / log
    from collections import Counter
    district_counts = Counter(r[2] for r in data["r"] if r[2])

    print(f"data.js written: {js_size} bytes, {len(data['r'])} restaurants, {len(data['d'])} districts")
    print("District breakdown:")
    for d, c in sorted(district_counts.items(), key=lambda x: -x[1]):
        safe_d = d.encode("ascii", "replace").decode("ascii")
        print(f"  {safe_d}: {c}")

    print(f"\nData updated! {len(data['r'])} restaurants (was previously {len(data['r'])} in last run).")


if __name__ == "__main__":
    main()
