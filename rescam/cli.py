from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import qrcode

from .storage import DATA_DIR, list_campaigns, save_campaign

CURRENCIES = ("BTC", "ETH", "SOL", "XRP")


def prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


def create_campaign() -> None:
    print("\nRe-scam — create a simulated crypto receipt")
    print("This creates a demonstration only, not proof of payment.\n")

    currency = prompt("Cryptocurrency (BTC/ETH/SOL/XRP)", "BTC").upper()
    if currency not in CURRENCIES:
        raise SystemExit(f"Unsupported currency: {currency}")

    amount = prompt("Amount", "0.05")
    try:
        if float(amount) <= 0:
            raise ValueError
    except ValueError:
        raise SystemExit("Amount must be a positive number.")

    payment_method = prompt("Payment method", "Crypto transfer")
    note = prompt("Additional note (optional)")
    created_at = datetime.now(timezone.utc).isoformat()
    campaign_id = uuid.uuid4().hex[:12]
    public_url = os.getenv("RESCAM_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")
    campaign = {
        "id": campaign_id,
        "created_at": created_at,
        "currency": currency,
        "amount": amount,
        "payment_method": payment_method,
        "note": note,
        "public_url": f"{public_url}/c/{campaign_id}",
        "simulation": True,
    }

    save_campaign(campaign)
    output_dir = DATA_DIR / "campaigns"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{campaign_id}.json"
    qr_path = output_dir / f"{campaign_id}.png"
    json_path.write_text(json.dumps(campaign, indent=2), encoding="utf-8")
    qrcode.make(campaign["public_url"]).save(qr_path)

    print("\nCampaign created.")
    print(f"ID:       {campaign_id}")
    print(f"Page:     {campaign['public_url']}")
    print(f"Details:  {json_path}")
    print(f"QR code:  {qr_path}")
    print("\nStart the server with: rescam serve")


def serve() -> None:
    import uvicorn
    uvicorn.run("rescam.server:app", host="127.0.0.1", port=8000, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(prog="rescam")
    parser.add_argument("command", choices=("create", "serve", "list"))
    args = parser.parse_args()

    if args.command == "create":
        create_campaign()
    elif args.command == "serve":
        serve()
    elif args.command == "list":
        campaigns = list_campaigns()
        if not campaigns:
            print("No campaigns yet.")
            return
        for item in campaigns:
            print(
                f"{item['id']} | {item['amount']} {item['currency']} | "
                f"{item['visit_count']} visits | {item['created_at']}"
            )


if __name__ == "__main__":
    main()
