# Re-scam — Crypto

A Python-based crypto scam-awareness and research tool. It creates clearly labelled simulated crypto receipts, QR links, and anonymous visit notifications.

> **Simulation only.** Generated receipts are not proof of payment and must never be presented as genuine transaction records. The linked page identifies itself as a simulation. It does not request identity documents, contact details, wallet credentials, or location.

## Features

- Interactive CLI for creating a campaign.
- Simulated BTC, ETH, SOL, or XRP receipt details.
- QR code linking to a campaign page.
- FastAPI web server for campaign pages.
- Anonymous visit counts and optional email alerts.
- SQLite storage for campaign metadata and visit timestamps.

## Quick start

Python 3.10+

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
rescam create
```

Run the web server:

```bash
rescam serve
```

By default, the server listens on `http://127.0.0.1:8000`. For a remotely accessible test, deploy it behind HTTPS and set `RESCAM_PUBLIC_URL` to its public base URL before creating campaigns.

## Email alerts

Email is optional. Configure these environment variables to receive an alert when a campaign page is opened:

- `RESCAM_SMTP_HOST`
- `RESCAM_SMTP_PORT` (defaults to `587`)
- `RESCAM_SMTP_USERNAME`
- `RESCAM_SMTP_PASSWORD`
- `RESCAM_ALERT_FROM`
- `RESCAM_ALERT_TO`

Use an app-specific SMTP password. Do not commit credentials to this repository. If SMTP is not configured, visits are still recorded locally.

## Data and privacy

The server stores campaign details and a timestamp for each page visit. It does not store visitor IP addresses, browser fingerprints, names, email addresses, phone numbers, identity documents, or precise location. The campaign page clearly explains that it is a simulation.

## Commands

- `rescam create` — create a simulated campaign and QR code.
- `rescam serve` — run the local web server.
- `rescam list` — list locally stored campaigns.

## Disclaimer

Use this project for education, research, and scam-awareness demonstrations. Do not impersonate real payment providers, fabricate evidence for disputes, or mislead people into disclosing personal or financial information.
