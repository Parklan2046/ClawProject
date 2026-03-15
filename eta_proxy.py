from flask import Flask, jsonify, Response
import requests
import os

app = Flask(__name__)

CITYBUS_BASE = "https://rt.data.gov.hk/v1/transport/citybus-nlb/eta"

@app.after_request
def add_cors_headers(response: Response):
    """Allow browser frontends (e.g. GitHub Pages) to call this API."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/eta/<company>/<stop_id>", methods=["GET"])
def eta_by_stop(company: str, stop_id: str):
    """Proxy to data.gov.hk Citybus/NLB ETA API.

    Example:
      GET /eta/CTB/001272
        -> https://rt.data.gov.hk/v1/transport/citybus-nlb/eta/CTB/001272
    """
    company = company.upper()
    if company not in ("CTB", "NLB"):
        return jsonify({"error": "unsupported company", "company": company}), 400

    upstream_url = f"{CITYBUS_BASE}/{company}/{stop_id}"

    try:
        r = requests.get(upstream_url, timeout=5)
    except requests.RequestException as e:
        return jsonify({"error": "upstream_request_failed", "detail": str(e)}), 502

    # Pass through status + body, but normalise content-type
    return (r.content, r.status_code, {
        "Content-Type": r.headers.get("Content-Type", "application/json")
    })


if __name__ == "__main__":
    # Bind 0.0.0.0 so your browser can reach it via VPS IP/hostname
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
