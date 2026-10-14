# crypto-pay-cli

Check incoming USDT (TRC20) payments to a wallet, and generate a QR code so a client can pay you. No API key, no sign-up, no dependencies — just Python 3 and TronGrid's public API.

Built for freelancers and indie sellers who accept crypto directly instead of going through a payment processor that may not pay out to their country.

```bash
python3 pay.py check TSomeAddressHere
```

```
      338.00 USDT  2026-08-10 20:43 UTC  from TLY8r7...  tx=b4473970...
      118.00 USDT  2026-06-10 16:14 UTC  from TLY8r7...  tx=4d854802...
```

### Install (optional)

```bash
pip install git+https://github.com/kleogeos/crypto-pay-cli
crypto-pay check TSomeAddressHere
```

### Check for a specific invoice

```bash
crypto-pay check TSomeAddressHere --min 15 --since 2026-10-14
```

Filters out everything smaller than the invoice amount and everything older than the invoice date — the common case of "did my client's payment land yet."

### Generate a receive QR code

```bash
crypto-pay qr TSomeAddressHere --amount 15
```

Prints a URL to a QR code image your client can scan from a wallet app. Drop it on an invoice page or in a chat.

### Options — `check`

| Flag | Default | Meaning |
|---|---|---|
| `address` | required | Wallet address to check |
| `--token` | `usdt` | Known token name |
| `--contract` | — | Override: raw TRC20 contract address, for other tokens |
| `--min` | — | Only show transfers at or above this amount |
| `--since` | — | Only show transfers after this ISO date |
| `--limit` | 20 | Max transfers to fetch |
| `--json` | off | Output as JSON instead of text |

### Options — `qr`

| Flag | Default | Meaning |
|---|---|---|
| `address` | required | Wallet address to receive payment |
| `--amount` | — | Optional amount hint embedded in the QR payload |
| `--open` | off | Open the QR code in a browser immediately |

### Why TRC20 / USDT first

TRC20 USDT is widely used for freelance payments because transaction fees are near zero and it settles in seconds. Support for other chains (ERC20, Solana, etc.) can be added the same way — TronGrid's API shape generalizes to most block explorer APIs with public endpoints.

### Part of a small toolkit for freelancers

- [freelance-invoice-cli](https://github.com/kleogeos/freelance-invoice-cli) — generate HTML invoices from JSON
- [freelance-rate-cli](https://github.com/kleogeos/freelance-rate-cli) — calculate your required hourly rate
- [contract-checklist-cli](https://github.com/kleogeos/contract-checklist-cli) — scan a contract for missing clauses
- More free tools + a paid starter kit: [kleogeos.github.io/freelancer-tools](https://kleogeos.github.io/freelancer-tools/)

## License

MIT
