#!/usr/bin/env python3
"""
Heung Yuen Wai Parking Monitor
Consolidates 30-min slot data into readable booking windows.
"""

import json
import os
import requests
from datetime import date, timedelta, datetime as dt
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = os.getenv("PARKING_HOST", "127.0.0.1")
PORT = int(os.getenv("PARKING_PORT", "8774"))
API_BASE = "https://hywparking.com.hk"

# Vehicle types mapping
CAR_TYPES = {
    "private": {"id": 1, "zone": "1", "name": "私家車"},
    "disabled_grey": {"id": 5, "zone": "1", "name": "司機接載殘疾人士(灰證)"},
    "disabled_blue": {"id": 6, "zone": "1", "name": "傷殘人士泊車許可證(藍證)"},
    "motorcycle": {"id": 3, "zone": "1", "name": "電單車"},
    "goods": {"id": 4, "zone": "2", "name": "客貨車"},
}


class ParkingAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "zh-HK,zh;q=0.9",
        })
        self._init_session()

    def _init_session(self):
        """Warm up session to mimic a real browser visit."""
        # Step 1: Load main page to get JSESSIONID
        self.session.get(f"{API_BASE}/car-park/carParkBooking?lang=zh_TW", timeout=15)
        # Step 2: Make the same API calls the official page makes on load
        try:
            self.session.get(f"{API_BASE}/flt-booking-query/public/v1/ipinfo", timeout=10)
        except: pass
        try:
            self.session.get(f"{API_BASE}/non-pss-int/public/v1/content-management/list?lang=en&application_code=IBE&channel=web&include_keys=airportCodeToCityName", timeout=10)
        except: pass

    def get_slots(self, target_date: str, zone: str = "1", cartype: int = 1):
        """Get available parking slots for a specific date."""
        r = self.session.get(
            f"{API_BASE}/bookingApi/available-space",
            params={"zone": zone, "cartype": cartype, "in": target_date, "lang": "zh_TW"},
            timeout=15
        )
        data = r.json()
        if not data.get("success"):
            return {"error": data.get("message", "API error")}

        slots = data["data"]["AvailableSpaces"]
        return self._consolidate_slots(slots, target_date)

    def _consolidate_slots(self, slots: list, target_date: str = None) -> dict:
        """Merge consecutive available slots into booking windows for one day."""
        if not slots:
            return {"quota": 0, "windows": [], "full_day_available": False}

        quota = slots[0]["Quota"]

        # Filter to only slots for the target date
        if target_date:
            # target_date is like "2026/05/13", slot TimeSlot is "2026-05-13 00:00"
            date_filter = target_date.replace("/", "-")
            slots = [s for s in slots if s["TimeSlot"].startswith(date_filter)]

        # Filter to booking hours only: 06:00–22:00
        BOOKING_START = "06:00"
        BOOKING_END = "22:00"
        MIN_BOOKING_HOURS = 2  # Minimum booking is 2 hours
        
        slots = [s for s in slots if BOOKING_START <= s["TimeSlot"][-5:] < BOOKING_END]

        # For today: filter out slots that are < 30 min from now (must book 30 min before entry)
        now_hkt = dt.utcnow() + timedelta(hours=8)
        if target_date:
            target_d = target_date.replace("/", "-")
            today_str = now_hkt.strftime("%Y-%m-%d")
            if target_d == today_str:
                cutoff = now_hkt + timedelta(minutes=30)
                cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M")
                slots = [s for s in slots if s["TimeSlot"] >= cutoff_str]

        if not slots:
            return {"quota": quota, "total_slots": 0, "available_count": 0, 
                    "status": "full", "windows": [], "full_day_available": False}

        # Build list of (time_str, available_bool)
        times = []
        for s in slots:
            available = s["Spaces"] > 0 if "Spaces" in s else False
            times.append((s["TimeSlot"], available, s["Spaces"]))

        # Merge consecutive available blocks
        windows = []
        current_start = None
        current_end = None
        min_spaces_in_window = quota

        for time_str, available, spaces in times:
            if available:
                if current_start is None:
                    current_start = time_str
                    min_spaces_in_window = spaces
                current_end = time_str
                min_spaces_in_window = min(min_spaces_in_window, spaces)
            else:
                if current_start is not None:
                    windows.append({
                        "start": current_start[-5:],  # HH:MM
                        "end": self._add_30min(current_end),
                        "spaces": min_spaces_in_window,
                    })
                    current_start = None
                    min_spaces_in_window = quota

        # Don't forget the last window
        if current_start is not None:
            windows.append({
                "start": current_start[-5:],
                "end": self._add_30min(current_end),
                "spaces": min_spaces_in_window,
            })

        # Filter: only windows ≥ 2 hours (minimum booking)
        windows = [w for w in windows if self._window_duration(w) >= MIN_BOOKING_HOURS]

        # Calculate status
        total_slots = len(slots)
        available_count = sum(1 for _, avail, _ in times if avail)

        status = "full"
        if available_count == total_slots:
            status = "open"  # All slots available
        elif available_count > total_slots * 0.5:
            status = "available"  # Most slots available
        elif available_count > 0:
            status = "limited"  # Some slots available

        return {
            "quota": quota,
            "total_slots": total_slots,
            "available_count": available_count,
            "status": status,
            "windows": windows,
            "full_day_available": available_count == total_slots,
        }

    def _add_30min(self, time_str: str) -> str:
        """Add 30 minutes to a time slot string."""
        if " " in time_str:
            time_str = time_str.split(" ")[1]
        h, m = map(int, time_str.split(":"))
        m += 30
        if m >= 60:
            h += 1
            m -= 60
        return f"{h:02d}:{m:02d}"

    def _window_duration(self, window: dict) -> float:
        """Calculate window duration in hours."""
        sh, sm = map(int, window["start"].split(":"))
        eh, em = map(int, window["end"].split(":"))
        return (eh + em/60) - (sh + sm/60)


api = ParkingAPI()


def send_json(h, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    h.send_response(status)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(body)))
    h.send_header("Access-Control-Allow-Origin", "*")
    h.end_headers()
    h.wfile.write(body)


def send_html(h, path):
    base = os.path.dirname(__file__)
    filepath = os.path.join(base, path)
    if not os.path.exists(filepath):
        h.send_response(404)
        h.end_headers()
        return
    with open(filepath, "rb") as f:
        data = f.read()
    h.send_response(200)
    h.send_header("Content-Type", "text/html; charset=utf-8")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.rstrip("/").split("?")[0]
        params = {}
        if "?" in self.path:
            from urllib.parse import parse_qs, urlparse
            params = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

        # Dashboard page
        if path in ("", "/parking"):
            return send_html(self, "index.html")

        # API: Get availability for a single date
        if path == "/parking/api/slots":
            target = params.get("date", date.today().strftime("%Y/%m/%d"))
            car_type = params.get("type", "private")
            ct = CAR_TYPES.get(car_type, CAR_TYPES["private"])

            try:
                result = api.get_slots(target, ct["zone"], ct["id"])
                result["date"] = target
                result["vehicle"] = ct["name"]
                result["car_type_key"] = car_type
                return send_json(self, {"ok": True, **result})
            except Exception as e:
                return send_json(self, {"ok": False, "error": str(e)}, 500)

        # API: Get availability for a date range
        if path == "/parking/api/availability":
            car_type = params.get("type", "private")
            ct = CAR_TYPES.get(car_type, CAR_TYPES["private"])
            
            from_date = params.get("from")
            to_date = params.get("to")
            
            if from_date and to_date:
                # Parse yyyy-MM-dd from the picker
                from_d = date.fromisoformat(from_date)
                to_d = date.fromisoformat(to_date)
            else:
                days = int(params.get("days", "7"))
                from_d = date.today()
                to_d = from_d + timedelta(days=days - 1)

            results = []
            d = from_d
            while d <= to_d:
                date_str = d.strftime("%Y/%m/%d")
                try:
                    day_data = api.get_slots(date_str, ct["zone"], ct["id"])
                    day_data["date"] = date_str
                    day_data["day_name"] = d.strftime("%a")
                    day_data["day_label"] = d.strftime("%m月%d日")
                    results.append(day_data)
                except Exception as e:
                    results.append({
                        "date": date_str,
                        "day_name": d.strftime("%a"),
                        "day_label": d.strftime("%m月%d日"),
                        "error": str(e),
                        "status": "error",
                    })
                d += timedelta(days=1)

            return send_json(self, {
                "ok": True,
                "vehicle": ct["name"],
                "car_type_key": car_type,
                "zone": ct["zone"],
                "days": results,
            })

        # Booking redirect - proxies official page with auto-fill injection
        if path == "/parking/book":
            ct_key = params.get("type", "private")
            ct = CAR_TYPES.get(ct_key, CAR_TYPES["private"])
            date_str = params.get("date", "")
            start_time = params.get("start", "")
            end_time = params.get("end", "")
            
            radio_map = {"private": 0, "disabled_grey": 1, "motorcycle": 2, "disabled_blue": 3, "goods": 10}
            radio_idx = radio_map.get(ct_key, 0)
            
            try:
                r = api.session.get(f"{API_BASE}/car-park/carParkBooking?lang=zh_TW", timeout=15)
                html = r.text
                
                # Inject <base> tag so relative URLs resolve to official domain
                html = html.replace("<head>", "<head><base href='https://hywparking.com.hk/'>")
                
                auto_fill_js = """
<script>
(function() {
    var attempts = 0;
    var iv = setInterval(function() {
        attempts++;
        var radio = document.getElementById('bookRadio0""" + str(radio_idx) + """');
        if (!radio && attempts < 30) return;
        clearInterval(iv);
        if (!radio) return;
        radio.checked = true;
        radio.dispatchEvent(new Event('change', {bubbles: true}));
        if (typeof $ !== 'undefined') $(radio).trigger('change');
        console.log('[Auto-fill] """ + ct["name"] + """ | """ + date_str + """ """ + start_time + """-""" + end_time + """');
    }, 300);
})();
</script>
"""
                html = html.replace("</body>", auto_fill_js + "\n</body>")
                
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            except Exception as e:
                return send_json(self, {"ok": False, "error": str(e)}, 500)

        return send_json(self, {"ok": False, "error": "Not found"}, 404)

    def do_POST(self):
        path = self.path.rstrip("/").split("?")[0]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode()) if length else {}
        except:
            body = {}

        # Proxy: Calculate fee
        if path == "/parking/api/calc":
            try:
                r = api.session.get(f"{API_BASE}/bookingApi/calc", params={
                    "zone": body.get("zone", "1"),
                    "cartype": body.get("cartype", "1"),
                    "in": body["in"].replace("-","/"),
                    "out": body["out"].replace("-","/"),
                    "lang": "zh_TW"
                }, timeout=15)
                return send_json(self, r.json())
            except Exception as e:
                return send_json(self, {"ok": False, "error": str(e)}, 500)

        # Proxy: Send SMS
        if path == "/parking/api/sendsms":
            try:
                phone = body["phone"]
                # Official API expects 8-digit HK number (no +852 prefix)
                if phone.startswith("852"):
                    phone = phone[3:]
                elif phone.startswith("+852"):
                    phone = phone[4:]
                r = api.session.get(f"{API_BASE}/bookingApi/sendsms", params={
                    "phone": phone,
                    "lang": "zh_TW"
                }, timeout=15)
                return send_json(self, r.json())
            except Exception as e:
                return send_json(self, {"ok": False, "error": str(e)}, 500)

        # Proxy: Create booking
        if path == "/parking/api/book":
            try:
                booking = {
                    "zoneCode": body.get("zoneCode", "1"),
                    "carTypeId": int(body.get("carTypeId", 1)),
                    "carTypeCode": int(body.get("carTypeCode", 1)),
                    "enterTime": body["enterTime"].replace("-","/"),
                    "leaveTime": body["leaveTime"].replace("-","/"),
                    "phone": body["phone"],
                    "permitNumber": body.get("permitNumber", ""),
                    "permitType": body.get("permitType"),
                    "verifyCode": body["verifyCode"],
                    "amount": float(body.get("amount", 0)),
                    "email": body.get("email", ""),
                    "lang": "zh_TW",
                    "cardNumber": body.get("cardNumber", ""),
                    "entryMethod": int(body.get("entryMethod", 1)),
                    "payGateway": "Cybersource",
                    "existsBooking": body.get("existsBooking"),
                    "carPlate": body.get("carPlate", ""),
                }
                r = api.session.post(f"{API_BASE}/bookingApi/create",
                    json=booking,
                    headers={"Content-Type": "application/json"},
                    timeout=15)
                return send_json(self, r.json())
            except Exception as e:
                return send_json(self, {"success": False, "message": str(e)}, 500)

        return send_json(self, {"ok": False, "error": "Not found"}, 404)


if __name__ == "__main__":
    print(f"Parking Monitor on http://{HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
