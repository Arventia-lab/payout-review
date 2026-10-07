# Payout Review

A browser-based fraud & risk review tool for online payment and marketplace data.
Upload your CSV exports and get a ranked risk assessment per account — no
integration needed, and no data ever leaves the browser.

**Live demo:** https://arventia-lab.github.io/payout-review/

## What it does

- Reconciles account funding (pay-ins) against order/spend activity and
  promotional-credit terms
- Flags suspicious accounts and explains exactly why each one was flagged
- Scores every account **LOW / MEDIUM / HIGH** from the sum of the rules it
  triggered (capped at 100)
- Hard-stop rules (for example a failed KYC check) that force a HIGH rating on
  their own

## Signals checked

- Gift-card / digital-code concentration (obscured value)
- Self-dealing / offsetting orders
- Single-merchant concentration
- Goodwill-credit abuse
- Refund rate
- Chargebacks
- Payout velocity
- New payment method

## How to use

1. Open the [live demo](https://arventia-lab.github.io/payout-review/)
2. Upload your CSV files — `accounts` and `payouts` are required; `orders`,
   `promotions` and `kyc` are optional and the related checks switch off quietly
   when a file is missing
3. Review the ranked results and the reason behind each score

It handles messy real-world CSVs: byte-order marks, comma / semicolon / tab
delimiters, both `1.234,56` and `1,234.56` number formats, `dd.mm.yyyy` and ISO
dates, and loose column-name matching. Files are parsed in the browser and are
never uploaded anywhere.

## How it's built

- Single-file HTML/JS front end — the demo runs with no build step
- `generate.py` — synthetic data generator with a `verify()` consistency pass
  that refuses to write inconsistent data
- `build.py` — bundles everything into one shareable HTML file
- `sample-csv/` — deliberately hard example files to test the parser

## Note

This is a self-contained demonstration tool, not a hosted service. All
processing happens locally in the browser.
