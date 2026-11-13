from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import qrcode

from .storage import DATA_DIR, save_campaign

CURRENCIES = ("BTC", "ETH", "SOL", "XRP")


def normalize_amount(value: str) -> str:
    try:
        amount = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Enter a valid amount.") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Amount must be a finite number greater than zero.")
    parts = amount.as_tuple()
    if len(value) > 40 or parts.exponent < -18 or len(parts.digits) > 36 or amount.adjusted() > 18:
        raise ValueError("Amount is too precise or too large.")
    normalized = format(amount, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized


def create_campaign(
    currency: str,
    amount: str,
    payment_method: str,
    note: str = "",
) -> dict[str, Any]:
    currency = currency.strip().upper()
    payment_method = payment_method.strip()
    note = note.strip()

    if currency not in CURRENCIES:
        raise ValueError("Choose BTC, ETH, SOL, or XRP.")
    normalized_amount = normalize_amount(amount)
    if not payment_method or len(payment_method) > 80:
        raise ValueError("Payment method must be between 1 and 80 characters.")
    if len(note) > 240:
        raise ValueError("The note must be 240 characters or fewer.")

    public_url = os.getenv("RESCAM_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")
    campaign_id = uuid.uuid4().hex[:12]
    campaign = {
        "id": campaign_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "currency": currency,
        "amount": normalized_amount,
        "payment_method": payment_method,
        "note": note,
        "public_url": f"{public_url}/c/{campaign_id}",
        "simulation": True,
    }

    save_campaign(campaign)
    output_dir = DATA_DIR / "campaigns"
    output_dir.mkdir(parents=True, exist_ok=True)
    qrcode.make(campaign["public_url"]).save(output_dir / f"{campaign_id}.png")
    return campaign


def qr_path(campaign_id: str) -> Path:
    return DATA_DIR / "campaigns" / f"{campaign_id}.png"
