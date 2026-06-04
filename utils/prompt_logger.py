import os
from datetime import datetime, timezone

import requests


def log_prompt_to_sheet(
    *,
    prompt: str,
    industry: str,
    product: str,
    brand_styling: str,
    scene: str,
    action: str,
    has_reference: bool,
) -> bool:
    url = os.environ.get("SHEETS_WEBHOOK_URL", "").strip()
    secret = os.environ.get("SHEETS_WEBHOOK_SECRET", "").strip()
    if not url or not secret:
        return False

    try:
        response = requests.post(
            url,
            json={
                "secret": secret,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "industry": industry,
                "product": product,
                "brand_styling": brand_styling,
                "scene": scene,
                "prompt": prompt,
                "action": action,
                "has_reference": has_reference,
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception:
        return False
