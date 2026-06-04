"""Debug Google Sheets webhook logging.

Usage:
    .venv\\Scripts\\python scripts\\test_sheet_logging.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def main() -> int:
    url = os.environ.get("SHEETS_WEBHOOK_URL", "").strip()
    secret = os.environ.get("SHEETS_WEBHOOK_SECRET", "").strip()

    print("=== Sheet logging debug ===")
    print(f".env path: {ROOT / '.env'}")
    print(f"SHEETS_WEBHOOK_URL set: {bool(url)}")
    print(f"SHEETS_WEBHOOK_SECRET set: {bool(secret)}")

    if not url or not secret:
        print("\nFAIL: Missing SHEETS_WEBHOOK_URL or SHEETS_WEBHOOK_SECRET in .env")
        print("Add both lines to .env, save the file, then rerun this script.")
        return 1

    print(f"URL host: {url.split('/')[2] if '://' in url else 'invalid'}")
    print(f"URL ends with /exec: {url.rstrip('/').endswith('/exec')}")

    payload = {
        "secret": secret,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "industry": "FDA Food Packaging",
        "product": "Dairy",
        "brand_styling": "Stand up pouch",
        "scene": "grocery store shelf",
        "prompt": "Debug test prompt from scripts/test_sheet_logging.py",
        "action": "debug_test",
        "has_reference": True,
    }

    print("\nSending POST request...")
    try:
        response = requests.post(url, json=payload, timeout=15)
    except requests.RequestException as exc:
        print(f"\nFAIL: Network error: {exc}")
        return 1

    print(f"HTTP status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Response body (first 500 chars): {response.text[:500]}")

    if response.status_code >= 400:
        print("\nFAIL: HTTP error from webhook.")
        return 1

    try:
        data = response.json()
        print(f"JSON response: {json.dumps(data)}")
        if data.get("ok") is False:
            print("\nFAIL: Apps Script rejected the request (wrong secret?).")
            return 1
    except json.JSONDecodeError:
        print("\nWARN: Response is not JSON. Check Apps Script deployment URL uses /exec")

    print("\nOK: Request completed. Refresh your Google Sheet for a new row.")
    print("If no row appears, open Apps Script -> Executions for runtime errors.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
