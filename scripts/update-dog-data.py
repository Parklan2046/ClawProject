#!/usr/bin/env python3
"""
Fetch live data from FEHD's public API and regenerate dog-restaurants/data.js.

Data source: https://www.fehd.gov.hk/english/licensing/dog_restaurants/getData.php

Schema: [en, zh, district_zh, district_en, address_zh, address_en, licence, lat, lng]
Features: Geocoding (Nominatim, cached), changelog, timestamp header.
"""

import datetime
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter

API_URL = "https://www.fehd.gov.hk/english/licensing/dog_restaurants/getData.php"
REFERER = "https://www.fehd.gov.hk/tc_chi/licensing/dog_restaurants/dog_restaurants_list.html"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_UA = "ClawProject-dog-restaurants-updater/1.0"

_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUTPUT_PATH = os.path.join(_BASE, "dog-restaurants", "data.js")
HASH_PATH = os.path.join(_BASE, "dog-restaurants", ".data-hash")
CHANGELOG_PATH = os.path.join(_BASE, "dog-restaurants", "changelog.js")
GEOCACHE_PATH = os.path.join(_BASE, "fehd-dog-restaurants", "_geocache.json")
PREV_LICENCES_PATH = os.path.join(_BASE, "fehd-dog-restaurants", "_prev-licences.json")


def fetch_api():
    req = urllib.request.Request(API_URL)
    req.add_header("User-Agent", "Mozilla/5.0 (ClawProject dog-restaurants updater)")
    req.add_header("Referer", REFERER)
    req.add_header("Accept", "application/json")
    print(f"Fetching {API_URL} ...")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8-sig")
    except Exception as e:
        print(f"ERROR: Failed to fetch API: {e}")
        sys.exit(1)
    print(f"Downloaded {len(raw)} bytes")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        sys.exit(2)
    if not isinstance(data, list):
        print(f"ERROR: Expected a JSON array, got {type(data).__name__}")
        sys.exit(2)
    print(f"Parsed {len(data)} restaurant records")
    return data


def transform(records):
    districts = []
    district_seen = set()
    rows = []
    for r in records:
        en = (r.get("shop_sign_en") or "").strip().replace("\n", " ")
        zh = (r.get("shop_sign_tc") or en).strip().replace("\n", " ")
        district_zh = (r.get("district_tc") or "").strip()
        district_en = (r.get("district_en") or "").strip()
        address_zh = (r.get("address_tc") or "").strip().replace("\n", " ")
        address_en = (r.get("address_en") or "").strip().replace("\n", " ")
        licence = (r.get("licence") or "").strip()
        if not en and not zh:
            continue
        if district_zh and district_zh not in district_seen:
            districts.append(district_zh)
            district_seen.add(district_zh)
        rows.append([en, zh, district_zh, district_en, address_zh, address_en, licence, None, None])
    return districts, rows


def load_geocache():
    if os.path.exists(GEOCACHE_PATH):
        try:
            with open(GEOCACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            if isinstance(cache, dict):
                return cache
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_geocache(cache):
    os.makedirs(os.path.dirname(GEOCACHE_PATH), exist_ok=True)
    with open(GEOCACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode_one(query):
    encoded = urllib.parse.quote(query)
    url = f"{NOMINATIM_URL}?q={encoded}&format=json&limit=1&countrycodes=hk"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", GEOCODER_UA)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            results = json.loads(resp.read().decode("utf-8"))
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None, None


def geocode_rows(rows):
    cache = load_geocache()
    to_geocode = [row for row in rows if row[6] not in cache]
    cached_count = sum(1 for row in rows if row[6] in cache)
    print(f"Geocache: {len(cache)} total, {cached_count} cached, {len(to_geocode)} new to geocode.")

    for row in rows:
        licence = row[6]
        if licence in cache:
            entry = cache[licence]
            row[7] = entry.get("lat")
            row[8] = entry.get("lng")

    if not to_geocode:
        print("All restaurants already geocoded.")
        return

    geocoded_ok = 0
    geocoded_fail = 0
    total = len(to_geocode)
    for idx, row in enumerate(to_geocode, 1):
        licence = row[6]
        query = f"{row[5]} {row[0]} Hong Kong".strip()  # English address + English name
        query = " ".join(query.split())
        if not query or query == "Hong Kong":
            cache[licence] = {"lat": None, "lng": None}
            geocoded_fail += 1
            continue
        lat, lng = geocode_one(query)
        cache[licence] = {"lat": lat, "lng": lng}
        row[7] = lat
        row[8] = lng
        if lat is not None:
            geocoded_ok += 1
        else:
            geocoded_fail += 1
        status = f"{lat:.4f}, {lng:.4f}" if lat else "null"
        safe_name = row[0][:40].encode("ascii", "replace").decode("ascii")
        print(f"  [{idx}/{total}] {safe_name:40s} -> {status}")
        time.sleep(1)

    print(f"Geocoding complete: {geocoded_ok} success, {geocoded_fail} failed/null out of {total} new.")
    save_geocache(cache)
    print(f"Geocache saved: {len(cache)} total entries.")


def generate_js(data, timestamp_iso):
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"const DOG_DATA_UPDATED='{timestamp_iso}';\nconst DOG_DATA={compact};\n"


def get_data_hash(data):
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


def load_prev_licences():
    if os.path.exists(PREV_LICENCES_PATH):
        try:
            with open(PREV_LICENCES_PATH, "r", encoding="utf-8") as f:
                prev = json.load(f)
            if isinstance(prev, list):
                return prev
        except (json.JSONDecodeError, IOError):
            pass
    return []


def generate_changelog(rows, prev_licences, timestamp_iso):
    by_licence = {}
    current_licences = []
    for row in rows:
        licence = row[6]
        current_licences.append(licence)
        by_licence[licence] = row
    prev_set = set(prev_licences)
    curr_set = set(current_licences)
    added_licences = curr_set - prev_set
    removed_licences = prev_set - curr_set
    added = []
    for lic in sorted(added_licences):
        row = by_licence.get(lic)
        if row:
            added.append([row[0], row[1], row[2], row[4], row[6]])
    removed = sorted(removed_licences)
    return {"lastUpdate": timestamp_iso, "added": added, "removed": removed, "totalAdded": len(added)}


def save_changelog(changelog):
    os.makedirs(os.path.dirname(CHANGELOG_PATH), exist_ok=True)
    compact = json.dumps(changelog, ensure_ascii=False, separators=(",", ":"))
    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"const DOG_CHANGELOG={compact};\n")


def save_prev_licences(licences):
    os.makedirs(os.path.dirname(PREV_LICENCES_PATH), exist_ok=True)
    with open(PREV_LICENCES_PATH, "w", encoding="utf-8") as f:
        json.dump(licences, f, ensure_ascii=False)


def main():
    records = fetch_api()
    districts, rows = transform(records)
    geocode_rows(rows)
    data = {"d": districts, "r": rows}

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    new_hash = get_data_hash(data)
    old_hash = ""
    if os.path.exists(HASH_PATH):
        with open(HASH_PATH, "r") as f:
            old_hash = f.read().strip()

    print(f"Old hash: {old_hash or '(none)'}")
    print(f"New hash: {new_hash}")

    if new_hash == old_hash:
        print("No data changes detected. Skipping data.js write.")
    else:
        js_content = generate_js(data, timestamp_iso)
        js_size = len(js_content.encode("utf-8"))
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(js_content)
        with open(HASH_PATH, "w") as f:
            f.write(new_hash)
        print(f"data.js written: {js_size} bytes, {len(data['r'])} restaurants, {len(data['d'])} districts")

    prev_licences = load_prev_licences()
    changelog = generate_changelog(rows, prev_licences, timestamp_iso)
    print(f"Changelog: +{changelog['totalAdded']} added, -{len(changelog['removed'])} removed (prev: {len(prev_licences)} licences)")
    save_changelog(changelog)
    print("changelog.js written.")

    current_licences = [row[6] for row in rows]
    save_prev_licences(current_licences)

    district_counts = Counter(r[2] for r in data["r"] if r[2])
    print("District breakdown:")
    for d, c in sorted(district_counts.items(), key=lambda x: -x[1]):
        safe_d = d.encode("ascii", "replace").decode("ascii")
        print(f"  {safe_d}: {c}")

    geocoded = sum(1 for r in data["r"] if r[7] is not None)
    print(f"\nDone! {len(data['r'])} restaurants, {geocoded} geocoded, {len(data['r']) - geocoded} missing coords.")


if __name__ == "__main__":
    main()
