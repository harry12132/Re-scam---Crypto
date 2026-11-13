from __future__ import annotations

import base64
import binascii
import hmac
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .campaigns import CURRENCIES, create_campaign, qr_path
from .notifications import send_visit_alert
from .storage import get_campaign, list_campaigns, record_visit

app = FastAPI(title="Re-scam — Crypto", version="0.2.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


def page(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f5f5f3">
  <title>{escape(title)} · Re-scam</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="wordmark" href="/">re-scam<span>.</span></a>
    <span class="topbar-label">CRYPTO AWARENESS TOOL</span>
  </header>
  {content}
  <footer class="site-footer">Re-scam · Scam-awareness simulation · No real payments</footer>
</body>
</html>"""


def require_admin(request: Request) -> None:
    username = os.getenv("RESCAM_ADMIN_USERNAME")
    password = os.getenv("RESCAM_ADMIN_PASSWORD")
    if username and password:
        header = request.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "basic" or not token:
            raise HTTPException(
                status_code=401,
                detail="Admin login required",
                headers={"WWW-Authenticate": 'Basic realm="Re-scam dashboard"'},
            )
        try:
            decoded = base64.b64decode(token, validate=True).decode("utf-8")
            supplied_user, separator, supplied_password = decoded.partition(":")
        except (binascii.Error, UnicodeDecodeError):
            supplied_user, separator, supplied_password = "", "", ""
        valid = (
            bool(separator)
            and hmac.compare_digest(supplied_user.encode(), username.encode())
            and hmac.compare_digest(supplied_password.encode(), password.encode())
        )
        if not valid:
            raise HTTPException(
                status_code=401,
                detail="Invalid admin credentials",
                headers={"WWW-Authenticate": 'Basic realm="Re-scam dashboard"'},
            )
        return

    client_host = request.client.host if request.client else ""
    if client_host not in {"127.0.0.1", "::1", "localhost", "testclient"}:
        raise HTTPException(
            status_code=503,
            detail="Set RESCAM_ADMIN_USERNAME and RESCAM_ADMIN_PASSWORD before remote access.",
        )


def get_existing_campaign(campaign_id: str) -> dict:
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@app.get("/", response_class=HTMLResponse)
def dashboard(_: None = Depends(require_admin)) -> str:
    campaigns = list_campaigns()
    total_visits = sum(item["visit_count"] for item in campaigns)
    rows = ""
    for item in campaigns:
        cid = escape(item["id"])
        created = escape(item["created_at"][:10])
        rows += f"""
        <a class="campaign-row" href="/campaigns/{cid}">
          <span class="coin-mark">{escape(item['currency'][:1])}</span>
          <span class="campaign-main">
            <strong>{escape(item['amount'])} {escape(item['currency'])}</strong>
            <small>{created} · {escape(item['payment_method'])}</small>
          </span>
          <span class="visit-count">{item['visit_count']} views</span>
          <span class="row-arrow">↗</span>
        </a>"""

    if not rows:
        rows = '<div class="empty-state"><strong>No campaigns yet.</strong><p>Create a simulation to generate its share link and QR code.</p></div>'

    content = f"""
    <main class="shell">
      <section class="intro">
        <div>
          <p class="eyebrow">YOUR WORKSPACE</p>
          <h1>Campaigns</h1>
          <p class="lede">Create and manage clearly labelled crypto simulations.</p>
        </div>
        <div class="privacy-chip"><span></span> Simulation mode</div>
      </section>

      <section class="stats" aria-label="Campaign overview">
        <div class="stat"><span>CAMPAIGNS</span><strong>{len(campaigns)}</strong></div>
        <div class="stat"><span>PAGE VIEWS</span><strong>{total_visits}</strong></div>
        <div class="stat"><span>PAYMENTS VERIFIED</span><strong>0</strong></div>
      </section>

      <section class="workspace-grid">
        <section class="panel campaign-panel">
          <div class="panel-heading">
            <div><p class="eyebrow">ACTIVITY</p><h2>Recent campaigns</h2></div>
            <span class="quiet-label">{len(campaigns)} total</span>
          </div>
          <div class="campaign-list">{rows}</div>
        </section>

        <section class="panel create-panel">
          <p class="eyebrow">NEW SIMULATION</p>
          <h2>Create a campaign</h2>
          <p class="form-intro">Generate a demonstration page and QR code. No blockchain transaction is created.</p>
          <form method="post" action="/campaigns">
            <label for="currency">Cryptocurrency</label>
            <select id="currency" name="currency">
              {''.join(f'<option value="{coin}">{coin}</option>' for coin in CURRENCIES)}
            </select>
            <label for="amount">Illustrative amount</label>
            <input id="amount" name="amount" inputmode="decimal" value="0.05" required maxlength="40">
            <label for="method">Example payment method</label>
            <input id="method" name="payment_method" value="Crypto transfer" required maxlength="80">
            <label for="note">Note <span class="optional">OPTIONAL</span></label>
            <textarea id="note" name="note" rows="3" maxlength="240" placeholder="A short note shown on the simulation"></textarea>
            <p class="form-hint">Do not enter personal, financial, or identifying information.</p>
            <button class="primary-button" type="submit">Create simulation <span>↗</span></button>
          </form>
        </section>
      </section>
    </main>"""
    return page("Campaigns", content)


@app.post("/campaigns")
async def create_from_dashboard(request: Request, _: None = Depends(require_admin)):
    body = (await request.body()).decode("utf-8", errors="replace")
    form = {key: values[0] for key, values in parse_qs(body).items() if values}
    try:
        campaign = create_campaign(
            form.get("currency", "BTC"),
            form.get("amount", ""),
            form.get("payment_method", ""),
            form.get("note", ""),
        )
    except ValueError as exc:
        content = f"""
        <main class="narrow-shell">
          <section class="panel error-panel">
            <p class="eyebrow">CAMPAIGN NOT CREATED</p>
            <h1>Check those details</h1>
            <p>{escape(str(exc))}</p>
            <a class="text-link" href="/">Back to campaigns</a>
          </section>
        </main>"""
        return HTMLResponse(page("Campaign error", content), status_code=400)
    return RedirectResponse(f"/campaigns/{campaign['id']}", status_code=303)


@app.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
def campaign_detail(campaign_id: str, _: None = Depends(require_admin)) -> str:
    campaign = get_existing_campaign(campaign_id)
    cid = escape(campaign["id"])
    url = escape(campaign["public_url"])
    content = f"""
    <main class="narrow-shell">
      <a class="back-link" href="/">← All campaigns</a>
      <section class="detail-heading">
        <p class="eyebrow">CAMPAIGN CREATED</p>
        <h1>Your simulation is ready.</h1>
        <p class="lede">Share the demonstration link or use the QR code during an awareness exercise.</p>
      </section>
      <section class="panel share-panel">
        <div class="share-topline"><span class="status-dot"></span> SIMULATION LINK</div>
        <label for="share-url">Campaign URL</label>
        <div class="copy-field"><input id="share-url" value="{url}" readonly><button type="button" id="copy-button">Copy</button></div>
        <p id="copy-status" class="form-hint" aria-live="polite">This page clearly identifies itself as a simulation.</p>
        <div class="qr-wrap"><img src="/c/{cid}/qr.png" alt="QR code for campaign {cid}"><div><strong>Scan to open</strong><p>QR codes point to the campaign URL above. A localhost link only works on this Mac.</p></div></div>
      </section>
      <section class="panel detail-panel">
        <p class="eyebrow">SIMULATION DETAILS</p>
        <div class="detail-line"><span>Amount</span><strong>{escape(campaign['amount'])} {escape(campaign['currency'])}</strong></div>
        <div class="detail-line"><span>Example method</span><strong>{escape(campaign['payment_method'])}</strong></div>
        <div class="detail-line"><span>Campaign ID</span><strong class="mono">{cid}</strong></div>
        <div class="detail-line"><span>Page views</span><strong>{next((x['visit_count'] for x in list_campaigns() if x['id'] == campaign_id), 0)}</strong></div>
      </section>
      <a class="text-link" href="/">Return to dashboard</a>
    </main>
    <script>
      const copyButton = document.getElementById('copy-button');
      copyButton.addEventListener('click', async () => {{
        const field = document.getElementById('share-url');
        try {{
          await navigator.clipboard.writeText(field.value);
          copyButton.textContent = 'Copied';
          document.getElementById('copy-status').textContent = 'Link copied to clipboard.';
        }} catch (_) {{
          field.select();
          document.getElementById('copy-status').textContent = 'Select and copy the link manually.';
        }}
      }});
    </script>"""
    return page("Campaign created", content)


@app.get("/c/{campaign_id}/qr.png")
def campaign_qr(campaign_id: str):
    get_existing_campaign(campaign_id)
    path = qr_path(campaign_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="QR code not found")
    return FileResponse(path, media_type="image/png", filename=f"rescam-{campaign_id}.png")


@app.get("/c/{campaign_id}", response_class=HTMLResponse)
def campaign_page(campaign_id: str) -> str:
    campaign = get_existing_campaign(campaign_id)
    visited_at = datetime.now(timezone.utc).isoformat()
    record_visit(campaign_id, visited_at)
    try:
        send_visit_alert(campaign, visited_at)
    except Exception:
        pass

    amount = escape(str(campaign["amount"]))
    currency = escape(str(campaign["currency"]))
    method = escape(str(campaign["payment_method"]))
    note = escape(str(campaign.get("note", "")))
    note_html = f'<div class="receipt-note"><span>CAMPAIGN NOTE</span><p>{note}</p></div>' if note else ""
    created = escape(campaign["created_at"][:19].replace("T", " ") + " UTC")
    cid = escape(campaign["id"])

    content = f"""
    <main class="receipt-shell">
      <div class="simulation-banner"><span class="banner-icon">!</span><div><strong>SIMULATION — NOT A REAL PAYMENT</strong><small>Scam-awareness demonstration · No funds transferred</small></div></div>
      <section class="receipt-card">
        <div class="receipt-brand"><span class="receipt-symbol">R</span><span>RE-SCAM <small>CRYPTO AWARENESS</small></span></div>
        <div class="receipt-title">
          <p class="eyebrow">ILLUSTRATIVE RECORD</p>
          <h1>Crypto transfer<br>demonstration</h1>
          <p>This is a simulated example, not a transaction receipt.</p>
        </div>
        <div class="amount-block"><span>ILLUSTRATIVE AMOUNT</span><strong>{amount} <small>{currency}</small></strong></div>
        <div class="receipt-details">
          <div><span>Example method</span><strong>{method}</strong></div>
          <div><span>Created</span><strong>{created}</strong></div>
          <div><span>Campaign reference</span><strong class="mono">{cid}</strong></div>
          <div><span>Payment status</span><strong class="status-not-paid">Not a payment</strong></div>
        </div>
        {note_html}
        <div class="receipt-disclaimer">
          <strong>What this page means</strong>
          <p>This page was created for a scam-awareness exercise. It is not connected to a wallet, exchange, or blockchain. No payment was made or verified, and this page cannot be used as proof that funds were sent.</p>
        </div>
        <div class="receipt-bottom">RE-SCAM · EDUCATION AND AWARENESS</div>
      </section>
      <p class="privacy-note">This page does not ask for or collect personal details, identity documents, wallet credentials, or location.</p>
    </main>"""
    return page("Simulation receipt", content)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
