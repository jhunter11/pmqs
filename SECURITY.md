# Security policy

## Credentials

PMQS never stores, transmits, or logs your API credentials beyond signing the
requests you explicitly initiate. The `.gitignore` refuses `*.pem`, `*.key`,
and `.env*` files by default. Keep your Kalshi private key outside the
repository and pass its path via `--private-key`.

## Live trading surface

There is none. PMQS contains no order-placement code. If you build execution
on top of it, that code and its risks are yours.

## Reporting a vulnerability

Open a GitHub issue with the label `security` (for sensitive reports, note in
the issue that you need a private channel and a maintainer will provide one).
Please include reproduction steps.
