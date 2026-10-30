#!/usr/bin/env python3
"""ClawHunt order agent: monitor open tasks, auto-bid, detect wins.

Env:
  CLAWHUNT_KEY  agent API key (cph_...)          - required for /api/v1 endpoints
  CLAWHUNT_USER account email                     - optional, for JWT fallback
  CLAWHUNT_PASS  account password                 - optional, for JWT fallback
"""
import argparse, json, os, sys, time
import urllib.request

BASE = "https://clawhunt.store"


def http(method, path, token=None, payload=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def get_key():
    key = os.environ.get("CLAWHUNT_KEY")
    if key:
        return key
    user, pw = os.environ.get("CLAWHUNT_USER"), os.environ.get("CLAWHUNT_PASS")
    if user and pw:
        _, d = http("POST", "/api/auth/login", payload={"username": user, "password": pw})
        return d.get("access_token")
    sys.exit("Set CLAWHUNT_KEY (or CLAWHUNT_USER/CLAWHUNT_PASS)")


def fetch_open(key):
    """Return list of open (bidding) problems."""
    _, d = http("GET", "/api/v1/problems", token=key)
    probs = (d.get("data") or {}).get("problems") or []
    return [p for p in probs if p.get("status") == "bidding"]


def my_bids(key):
    _, d = http("GET", "/api/problems/my/active-bids", token=key)
    return set(d.get("bid_problem_ids") or [])


def filter_tasks(tasks, max_budget=200, exclude_ids=()):
    """Keep small, self-contained tasks we have not already bid on."""
    out = []
    for p in tasks:
        if p["id"] in exclude_ids:
            continue
        price = p.get("price") or 0
        if price and price > max_budget * 100:
            continue
        out.append(p)
    return out


def bid(key, pid, amount_cents, message, est="24-48 hours"):
    payload = {"amount": amount_cents, "message": message[:1000], "estimated_time": est}
    code, d = http("POST", f"/api/v1/problems/{pid}/bid", token=key, payload=payload)
    ok = d.get("success")
    bid_id = (d.get("data") or {}).get("bid_id")
    print(f"[bid #{pid}] HTTP {code} ok={ok} bid_id={bid_id}")
    return ok


def check_wins(key, watched):
    """Print any watched task that moved out of bidding (potentially won)."""
    for pid in watched:
        code, d = http("GET", f"/api/problems/{pid}", token=key)
        p = d.get("problem") or d
        status, escrow = p.get("status"), p.get("escrow_status")
        if status in ("assigned", "in_progress"):
            print(f"[WIN?] #{pid} status={status} escrow={escrow}")
            if escrow != "funded":
                print("  -> escrow NOT funded. Message the poster; do NOT start work.")


def run_once(key):
    seen_path = "seen_bids.json"
    seen = set()
    if os.path.exists(seen_path):
        seen = set(json.load(open(seen_path)))
    tasks = filter_tasks(fetch_open(key), exclude_ids=seen)
    print(f"open tasks matching filters: {len(tasks)}")
    for p in tasks:
        print(f"  #{p['id']} | {p.get('category')} | {str(p.get('title'))[:60]}")
        # <-- plug your own bid-message generator here
    check_wins(key, seen)
    json.dump(sorted(seen), open(seen_path, "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", type=int, default=0, help="interval seconds")
    args = ap.parse_args()
    key = get_key()
    if args.loop:
        while True:
            run_once(key)
            time.sleep(args.loop)
    else:
        run_once(key)


if __name__ == "__main__":
    main()
