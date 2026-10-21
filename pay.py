#!/usr/bin/env python3
"""Check USDT (TRC20) payments to a wallet and generate a QR code for receiving one.

No dependencies, no API key, no sign-up — just Python 3 and TronGrid's public API.
"""
import argparse
import http.client
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

USDT_TRC20_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

KNOWN_TOKENS = {
    "usdt": USDT_TRC20_CONTRACT,
}


def fetch_transfers(address, contract, limit=20):
    url = (
        f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
        f"?limit={limit}&contract_address={contract}&only_to=true"
    )
    with urllib.request.urlopen(url, timeout=15) as r:
        data = json.load(r)
    out = []
    for tx in data.get("data", []):
        decimals = int(tx["token_info"]["decimals"])
        amount = int(tx["value"]) / (10 ** decimals)
        out.append({
            "amount": amount,
            "token": tx["token_info"]["symbol"],
            "from": tx["from"],
            "to": tx["to"],
            "txid": tx["transaction_id"],
            "timestamp": tx["block_timestamp"] / 1000,
        })
    return out


def resolve_contract(args):
    if args.contract:
        return args.contract
    try:
        return KNOWN_TOKENS[args.token.lower()]
    except KeyError:
        known = ", ".join(sorted(KNOWN_TOKENS))
        raise ValueError(f"unknown --token '{args.token}' (known: {known}; or pass --contract directly)")


def cmd_check(args):
    contract = resolve_contract(args)
    transfers = fetch_transfers(args.address, contract, limit=args.limit)

    if args.min is not None:
        transfers = [t for t in transfers if t["amount"] >= args.min]
    if args.since:
        try:
            since_dt = datetime.fromisoformat(args.since)
        except ValueError:
            raise ValueError(f"invalid --since date '{args.since}', expected e.g. 2026-10-01")
        since_ts = since_dt.replace(tzinfo=timezone.utc).timestamp()
        transfers = [t for t in transfers if t["timestamp"] >= since_ts]

    if args.json:
        print(json.dumps(transfers, indent=2))
        return

    if not transfers:
        print("No matching incoming transfers found.")
        return

    for t in transfers:
        when = datetime.fromtimestamp(t["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"{t['amount']:>12.2f} {t['token']}  {when}  from {t['from']}  tx={t['txid']}")


def cmd_qr(args):
    payload = args.address
    if args.amount:
        payload += f"?amount={args.amount}"
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?" + urllib.parse.urlencode({
        "size": "300x300",
        "data": payload,
    })
    print(qr_url)
    if args.open:
        import webbrowser
        webbrowser.open(qr_url)


def main():
    parser = argparse.ArgumentParser(
        description="Check crypto payments and generate receive QR codes for freelancers."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="List incoming token transfers to an address")
    p_check.add_argument("address", help="Wallet address to check")
    p_check.add_argument("--token", default="usdt", help="Known token name (default: usdt)")
    p_check.add_argument("--contract", help="Override: raw TRC20 contract address")
    p_check.add_argument("--min", type=float, help="Only show transfers >= this amount")
    p_check.add_argument("--since", help="Only show transfers after this ISO date, e.g. 2026-10-01")
    p_check.add_argument("--limit", type=int, default=20, help="Max transfers to fetch (default 20)")
    p_check.add_argument("--json", action="store_true", help="Output as JSON")
    p_check.set_defaults(func=cmd_check)

    p_qr = sub.add_parser("qr", help="Generate a QR code image URL for an address")
    p_qr.add_argument("address", help="Wallet address to receive payment")
    p_qr.add_argument("--amount", help="Optional amount to embed as a hint")
    p_qr.add_argument("--open", action="store_true", help="Open the QR code in a browser")
    p_qr.set_defaults(func=cmd_qr)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)
    except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
        print(f"error: couldn't reach TronGrid ({e})", file=sys.stderr)
        raise SystemExit(1)
