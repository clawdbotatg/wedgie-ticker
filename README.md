# Crypto Ticker

A [wedgie](https://wedgie.dev) app: live prices of the coins you pick, every 30 seconds. Up from the last
price is green, down is red.

- **Green button:** pick coins (green adds or removes one, red is done). Your pick is saved.
- **Grey button next to green:** update now.
- Joystick up/down: scroll when you picked more than 6.

Coins: BTC ETH SOL XRP BNB DOGE ADA AVAX LINK DOT LTC UNI AAVE ARB OP POL SUI NEAR TON HYPE SHIB PEPE, and
Base tokens DEGEN AERO BRETT. Add any token: put its chain and address in `TOKENS` in ticker.py.

A wedgie has no internet of its own. This app gets it from the computer it's plugged into: keep its page on
wedgie.dev open (wedgie.dev/connect, pick your wedgie), or run `python3 wedgie.py net`. It uses the
firmware's `net` module (firmware 0.3.61+). Prices come from Alchemy through wedgie.dev (wedgie.json
`"net": ["chain"]`; the key stays on wedgie.dev): coins by symbol in one call, tokens by address on their chain.

How to write an app like it: https://wedgie.dev/code.md

MIT
