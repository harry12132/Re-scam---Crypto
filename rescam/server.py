from __future__ import annotations

from datetime import datetime, timezone
from html import escape

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .notifications import send_visit_alert
from .storage import get_campaign, record_visit

app = FastAPI(title="Re-scam Crypto", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Re-scam — Crypto</title>
<body style="font:16px system-ui;max-width:680px;margin:12vh auto;padding:24px;color:#202124">
<h1>Re-scam — Crypto</h1>
<p>A crypto scam-awareness simulation tool.</p>
<p>Campaign links on this server display simulated receipt details and are
clearly labelled as demonstrations. No payment is made or verified.</p>
</body></html>"""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/c/{campaign_id}", response_class=HTMLResponse)
def campaign_page(campaign_id: str) -> str:
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    visited_at = datetime.now(timezone.utc).isoformat()
    record_visit(campaign_id, visited_at)
    try:
        send_visit_alert(campaign, visited_at)
    except Exception:
        # A mail provider outage must not prevent the page from loading.
        pass

    amount = escape(str(campaign["amount"]))
    currency = escape(str(campaign["currency"]))
    method = escape(str(campaign["payment_method"]))
    note = escape(str(campaign.get("note", "")))
    note_html = f"<p>{note}</p>" if note else ""

    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Simulated crypto receipt</title>
<body style="font:16px system-ui;max-width:620px;margin:10vh auto;padding:24px;color:#202124">
<main style="border:1px solid #ddd;border-radius:16px;padding:28px">
<p style="font-size:12px;font-weight:700;letter-spacing:.08em;color:#a15c00">SIMULATION — NOT A REAL PAYMENT</p>
<h1>Crypto transfer demonstration</h1>
<p><strong>Illustrative amount:</strong> {amount} {currency}</p>
<p><strong>Example method:</strong> {method}</p>
{note_html}
<hr style="border:0;border-top:1px solid #ddd;margin:24px 0">
<p>This page is part of a scam-awareness simulation. It is not a transaction receipt,
does not prove that funds were sent, and is not connected to a wallet or exchange.</p>
<p>No personal information, identity documents, wallet details, or location are requested
or collected by this page.</p>
</main></body></html>"""
