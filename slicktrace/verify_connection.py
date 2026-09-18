"""
SlickTrace v2 — Frontend & Backend Connectivity Verification Script
"""
import json
import urllib.request

print("--- SLICKTRACE INTEGRATION & CONNECTIVITY CHECK ---")

# 1. Backend Health
try:
    with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as resp:
        data = json.loads(resp.read().decode())
        mode = data.get("mode")
        version = data.get("version")
        print(f"[BACKEND] Health Check: HTTP {resp.status} OK | Mode: {mode} | Version: {version}")
except Exception as e:
    print(f"[BACKEND] Error: {e}")

# 2. CORS check from Frontend origin
try:
    req = urllib.request.Request(
        "http://localhost:8000/health",
        headers={"Origin": "http://localhost:3000"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        cors_hdr = resp.headers.get("access-control-allow-origin")
        matched = (cors_hdr == "http://localhost:3000")
        print(f"[CORS] Access-Control-Allow-Origin: {cors_hdr} (Allowed: {matched})")
except Exception as e:
    print(f"[CORS] Error: {e}")

# 3. Ocean Status endpoint
try:
    with urllib.request.urlopen("http://localhost:8000/api/v1/ocean/status", timeout=5) as resp:
        data = json.loads(resp.read().decode())
        prov_count = len(data.get("providers", {}))
        print(f"[BACKEND] Ocean Status: HTTP {resp.status} OK | Providers Checked: {prov_count}")
except Exception as e:
    print(f"[BACKEND] Ocean Status Error: {e}")

# 4. Frontend UI
try:
    req = urllib.request.Request("http://localhost:3000", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        has_title = "SlickTrace" in html
        print(f"[FRONTEND] UI Root Page: HTTP {resp.status} OK | HTML Length: {len(html)} bytes | Title Matched: {has_title}")
except Exception as e:
    print(f"[FRONTEND] Error: {e}")

print("----------------------------------------------------")
