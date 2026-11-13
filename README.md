# Re-scam — Crypto

A scam-awareness tool for creating transparent crypto simulations and reviewing anonymous page-view activity.

Re-scam is not a payment processor, wallet, blockchain explorer, or evidence-collection service. It does not create or verify transactions. Every public campaign page is prominently marked **SIMULATION — NOT A REAL PAYMENT**.

## What works

- Browser dashboard to create and manage campaigns.
- Simulated BTC, ETH, SOL, and XRP receipt pages.
- Unique campaign links and downloadable QR codes.
- Campaign view counts and a local campaign list.
- Optional email alert when a campaign page is opened.
- SQLite storage on the machine running the app.
- Responsive layout for desktop and mobile.

The application page-view counter stores only a campaign ID and timestamp. It does not collect visitor IP addresses, browser fingerprints, names, email addresses, phone numbers, identity documents, wallet credentials, or location. A hosting provider, reverse proxy, or email provider may maintain separate infrastructure logs under its own policies.

## Run locally

Python 3.10 or newer:

```bash
git clone https://github.com/harry12132/Re-scam---Crypto.git
cd Re-scam---Crypto
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
rescam serve
```

Open http://127.0.0.1:8000. Create a campaign in the dashboard. Its detail page provides the share URL and QR code.

To create a campaign from Terminal instead:

```bash
rescam create
```

To list campaigns and their view counts:

```bash
rescam list
```

## Sharing campaigns

By default, the server binds to localhost and campaign links work only on the same computer. For a hosted deployment, set `RESCAM_HOST=0.0.0.0`, use the port supplied by your host (the app reads `PORT`), deploy behind HTTPS, and set `RESCAM_PUBLIC_URL` to the public base URL before creating campaigns.

**Do not expose the dashboard to the public internet without setting both `RESCAM_ADMIN_USERNAME` and `RESCAM_ADMIN_PASSWORD`.** The dashboard uses HTTP Basic authentication when those variables are set. The public simulation pages remain accessible without dashboard credentials. Use a strong unique password and HTTPS. For a hosted deployment, also put the dashboard behind an access-control layer such as Cloudflare Access.

Example:

```bash
export RESCAM_PUBLIC_URL="https://your-domain.example"
export RESCAM_ADMIN_USERNAME="admin"
export RESCAM_ADMIN_PASSWORD="use-a-long-unique-password"
```

Set these values in your hosting provider's environment-variable settings, not in source code or committed files. Do not use the example domain or password literally.

## Email alerts

Email is optional. Configure these environment variables:

- `RESCAM_SMTP_HOST`
- `RESCAM_SMTP_PORT` (defaults to `587`)
- `RESCAM_SMTP_USERNAME`
- `RESCAM_SMTP_PASSWORD`
- `RESCAM_ALERT_FROM`
- `RESCAM_ALERT_TO`

Use an app-specific SMTP password. Never commit credentials. If SMTP is not configured, visit counts still work locally.

## Data location

By default, campaign data and QR images are stored under `~/.rescam`. Set `RESCAM_DATA_DIR` to use another directory. Back up this directory if you need to retain campaign history.

## Safety and intended use

Use Re-scam for education, research, and scam-awareness demonstrations. Do not impersonate a real payment provider, fabricate proof of payment, solicit financial credentials, or trick visitors into disclosing personal information. If you need to report a suspected scam, preserve genuine communications and use the relevant platform or official reporting channel yourself.
