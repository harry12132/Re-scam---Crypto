from __future__ import annotations

import argparse
import os

from .campaigns import CURRENCIES, create_campaign, qr_path
from .storage import list_campaigns


def prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or (default or "")


def create_from_cli() -> None:
    print("\nRe-scam — create a simulated crypto campaign")
    print("Demonstration only. This is not proof of payment.\n")

    currency = prompt(f"Cryptocurrency ({'/'.join(CURRENCIES)})", "BTC").upper()
    amount = prompt("Illustrative amount", "0.05")
    payment_method = prompt("Example payment method", "Crypto transfer")
    note = prompt("Additional note (optional)")

    try:
        campaign = create_campaign(currency, amount, payment_method, note)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print("\nCampaign created.")
    print(f"ID:       {campaign['id']}")
    print(f"Page:     {campaign['public_url']}")
    print(f"QR code:  {qr_path(campaign['id'])}")
    print("\nOpen the page while the server is running.")


def serve() -> None:
    import uvicorn
    host = os.getenv("RESCAM_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("rescam.server:app", host=host, port=port, reload=False)


def main() -> None:
    parser = argparse.ArgumentParser(prog="rescam")
    parser.add_argument("command", choices=("create", "serve", "list"))
    args = parser.parse_args()

    if args.command == "create":
        create_from_cli()
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
