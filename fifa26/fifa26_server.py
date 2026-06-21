"""
Fifa26 — World Cup dashboard server.
Run: python fifa26_server.py
"""
from __future__ import annotations
import json
import logging
import os
import threading
import time
import urllib.parse
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from providers.espn import EspnClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("fifa26")

HOST = os.getenv("FIFA26_HOST", "127.0.0.1")
PORT = int(os.getenv("FIFA26_PORT", "8773"))
ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SNAPSHOT_PATH = DATA / "snapshot.json"

POLL_INTERVAL = 60
POLL_BACKOFF = 300
UPSTREAM_TIMEOUT = 12

_QUAL_TOP2 = "top2"
_QUAL_THIRD = "third"
_QUAL_OUT = "out"

_QUAL_RULES = {
    "A": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "B": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "C": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "D": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "E": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "F": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "G": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "H": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "I": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "J": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "K": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
    "L": (_QUAL_TOP2, _QUAL_TOP2, _QUAL_THIRD),
}

_ROUND_BUCKET = {
    "group-stage": None,
    "round-of-32": "r32",
    "round-of-16": "r16",
    "quarterfinals": "qf",
    "semifinals": "sf",
    "third-place": "third",
    "final": "final",
}


class State:
    matches: list[dict] = []
    last_update: int = 0
    last_poll_ts: int = 0
    started_ts: int = 0
    errors: list[dict] = []


state = State()
_lock = threading.Lock()


def _atomic_write(path: Path, payload: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def _persist():
    try:
        snap = {
            "ts": int(time.time()),
            "last_update": state.last_update,
            "last_poll_ts": state.last_poll_ts,
            "matches": state.matches,
        }
        _atomic_write(SNAPSHOT_PATH, json.dumps(snap, ensure_ascii=False, default=str))
    except Exception as e:  # noqa: BLE001
        log.warning("persist snapshot failed: %s", e)


def _refresh(client: EspnClient) -> tuple[bool, bool]:
    """Single refresh attempt. Returns (ok, was_rate_limited)."""
    try:
        matches, was_rate_limited = client.fetch_all()
    except Exception as e:  # noqa: BLE001
        log.exception("refresh failed: %s", e)
        with _lock:
            state.errors.insert(0, {"ts": int(time.time()), "msg": str(e)})
            state.errors = state.errors[:20]
        return False, False
    with _lock:
        state.matches = matches
        state.last_update = int(time.time())
        state.last_poll_ts = state.last_update
    _persist()
    log.info("ESPN fetched %d matches", len(matches))
    return not was_rate_limited, was_rate_limited


def _poll_loop():
    client = EspnClient(timeout=UPSTREAM_TIMEOUT)
    while True:
        ok, rate_limited = _refresh(client)
        sleep_for = POLL_INTERVAL if ok else POLL_BACKOFF
        if rate_limited:
            log.warning("rate-limited (HTTP 429), backing off %ds", sleep_for)
        elif not ok:
            log.warning("refresh failed, backing off %ds", sleep_for)
        time.sleep(sleep_for)


def _initial_load():
    if SNAPSHOT_PATH.exists():
        try:
            snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
            with _lock:
                state.matches = snap.get("matches", []) or []
                state.last_update = int(snap.get("last_update", 0) or 0)
                state.last_poll_ts = int(snap.get("last_poll_ts", 0) or 0)
            if state.matches:
                log.info("loaded %d matches from snapshot.json", len(state.matches))
                return
        except Exception as e:  # noqa: BLE001
            log.warning("snapshot load failed: %s", e)
    client = EspnClient(timeout=UPSTREAM_TIMEOUT)
    _refresh(client)


def _team_key(t: dict) -> str:
    iso = t.get("iso") or ""
    if iso:
        return iso
    return str(t.get("id") or t.get("name") or "")


def _team_record(t: dict) -> dict:
    return {
        "id": t.get("id"),
        "iso": t.get("iso"),
        "name": t.get("name"),
        "short": t.get("short"),
        "logo": t.get("logo"),
        "color": t.get("color"),
        "flag": t.get("logo") or "",
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "gf": 0,
        "ga": 0,
        "gd": 0,
        "pts": 0,
    }


def _build_standings(matches: list[dict]) -> list[dict]:
    groups: dict[str, dict[str, dict]] = defaultdict(dict)
    for m in matches:
        if m.get("round_slug") != "group-stage":
            continue
        if m.get("status") != "final":
            continue
        g = m.get("group")
        if not g:
            continue
        home = m["home"]
        away = m["away"]
        hs = int(home.get("score") or 0)
        as_ = int(away.get("score") or 0)
        hkey = _team_key(home)
        akey = _team_key(away)
        rec_h = groups[g].setdefault(hkey, _team_record(home))
        rec_a = groups[g].setdefault(akey, _team_record(away))
        rec_h["played"] += 1
        rec_a["played"] += 1
        rec_h["gf"] += hs
        rec_h["ga"] += as_
        rec_a["gf"] += as_
        rec_a["ga"] += hs
        if hs > as_:
            rec_h["won"] += 1
            rec_h["pts"] += 3
            rec_a["lost"] += 1
        elif hs < as_:
            rec_a["won"] += 1
            rec_a["pts"] += 3
            rec_h["lost"] += 1
        else:
            rec_h["drawn"] += 1
            rec_a["drawn"] += 1
            rec_h["pts"] += 1
            rec_a["pts"] += 1
    out = []
    for letter in sorted(groups.keys()):
        teams = list(groups[letter].values())
        for t in teams:
            t["gd"] = t["gf"] - t["ga"]
        teams.sort(key=lambda t: (-t["pts"], -t["gd"], -t["gf"], t.get("name") or ""))
        qual = _QUAL_RULES.get(letter, (_QUAL_TOP2, _QUAL_TOP2, _QUAL_OUT))
        for i, t in enumerate(teams):
            if i < len(qual):
                t["qualified"] = qual[i]
            else:
                t["qualified"] = _QUAL_OUT
        out.append({"letter": letter, "teams": teams})
    return out


def _match_card(m: dict) -> dict:
    """Project an internal match record to the AGENTS.md reference shape."""
    home = m.get("home") or {}
    away = m.get("away") or {}
    status = m.get("status") or "scheduled"
    score = None
    if status in ("in_progress", "final"):
        score = f'{int(home.get("score") or 0)}-{int(away.get("score") or 0)}'
    return {
        "id": m.get("id"),
        "home": home.get("name") or home.get("short") or "TBD",
        "away": away.get("name") or away.get("short") or "TBD",
        "score": score,
        "status": status,
        "kickoff": m.get("date"),
        "venue": m.get("venue"),
        "round": m.get("round"),
    }


def _build_bracket(matches: list[dict]) -> list[dict]:
    buckets: dict[str, list[dict]] = {k: [] for k in ("r32", "r16", "qf", "sf", "third", "final")}
    for m in matches:
        bucket = _ROUND_BUCKET.get(m.get("round_slug") or "")
        if not bucket:
            continue
        buckets[bucket].append(_match_card(m))
    for k in buckets:
        buckets[k].sort(key=lambda x: x.get("kickoff") or "")
    labels = {"r32": "R32", "r16": "R16", "qf": "QF", "sf": "SF", "third": "3rd", "final": "F"}
    order = ("r32", "r16", "qf", "sf", "final", "third")
    return [{"label": labels[k], "key": k, "matches": buckets[k]} for k in order]


def _send_json(h, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    h.send_response(status)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(body)))
    h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(body)


def _send_file(h, path: Path, ctype: str):
    if not path.exists() or not path.is_file():
        h.send_response(404)
        h.send_header("Content-Type", "text/plain; charset=utf-8")
        h.end_headers()
        h.wfile.write(b"not found")
        return
    body = path.read_bytes()
    h.send_response(200)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(body)))
    if path.name in ("index.html", "sw.js"):
        h.send_header("Cache-Control", "no-cache")
    else:
        h.send_header("Cache-Control", "no-store")
    h.end_headers()
    h.wfile.write(body)


_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".webmanifest": "application/manifest+json",
    ".txt": "text/plain; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info("%s - %s", self.address_string(), fmt % args)

    def do_GET(self):
        try:
            self._route()
        except Exception as e:  # noqa: BLE001
            log.exception("handler error: %s", e)
            try:
                _send_json(self, {"ok": False, "error": str(e)}, 500)
            except Exception:
                pass

    def _route(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            return _send_file(self, ROOT / "index.html", "text/html; charset=utf-8")

        if path == "/api/health":
            with _lock:
                now = int(time.time())
                return _send_json(self, {
                    "ok": True,
                    "ts": now,
                    "uptime_s": now - state.started_ts if state.started_ts else 0,
                    "last_update": state.last_update,
                    "last_poll": state.last_poll_ts,
                    "match_count": len(state.matches),
                    "errors": state.errors[:5],
                })

        if path == "/api/snapshot":
            if not SNAPSHOT_PATH.exists():
                return _send_json(self, {"matches": [], "last_update": 0, "last_poll_ts": 0})
            try:
                raw = SNAPSHOT_PATH.read_text(encoding="utf-8")
                body = raw.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:  # noqa: BLE001
                return _send_json(self, {"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/standings":
            with _lock:
                matches = list(state.matches)
                last = state.last_update
            return _send_json(self, {
                "groups": _build_standings(matches),
                "updated_at": last,
            })

        if path == "/api/bracket":
            with _lock:
                matches = list(state.matches)
                last = state.last_update
            return _send_json(self, {
                "rounds": _build_bracket(matches),
                "updated_at": last,
            })

        if path.startswith("/static/"):
            rel = urllib.parse.unquote(path[len("/static/"):])
            target = (ROOT / rel).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                return _send_file(self, Path("notfound"), "text/plain; charset=utf-8")
            ext = target.suffix.lower()
            ctype = _MIME.get(ext, "application/octet-stream")
            return _send_file(self, target, ctype)

        if path in ("/favicon.ico", "/robots.txt", "/sw.js", "/manifest.webmanifest", "/icon.svg"):
            return _send_file(
                self,
                ROOT / path.lstrip("/"),
                _MIME.get(Path(path).suffix.lower(), "application/octet-stream"),
            )

        return _send_json(self, {"ok": False, "error": "not found"}, 404)


def main():
    state.started_ts = int(time.time())
    _initial_load()
    t = threading.Thread(target=_poll_loop, daemon=True, name="espn-poll")
    t.start()
    log.info("Fifa26 dashboard on http://%s:%d", HOST, PORT)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()