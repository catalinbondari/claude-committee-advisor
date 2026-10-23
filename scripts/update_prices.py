"""Write the latest Yahoo Finance prices into the page.

The page cannot call Yahoo itself: the Claude artifact only reaches its own files, and Yahoo does
not answer browsers from other sites. So this script runs outside the page (by hand, or daily on
GitHub Actions), looks up every ISIN in the page's universe, and embeds a snapshot:

    const PRICES = {"<isin>": {"p": price in euro, "m": typical daily move %, "d": "YYYY-MM-DD", "s": "SYMBOL"}}

- Listing: a euro listing is preferred (Xetra, Amsterdam, Milan, Paris); US shares use their US
  listing, converted at the day's EUR/USD.
- Daily move: the standard deviation of the last 60 daily returns, in %.
- data/yahoo_symbols.json keeps the ISIN -> symbol choices so they don't change from run to run;
  edit it to override one.

    pip install yfinance requests
    python3 scripts/update_prices.py && python3 build.py
"""

from __future__ import annotations

import json
import math
import re
import sys
from datetime import date
from pathlib import Path

import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "src" / "page.html"
SYMBOLS = ROOT / "data" / "yahoo_symbols.json"
OUT = ROOT / "data" / "prices.json"
UA = {"User-Agent": "Mozilla/5.0 (committee-room price snapshot)"}
EUR_VENUES = ["GER", "AMS", "MIL", "PAR", "BRU", "FRA", "VIE", "MCE", "LIS"]
US_VENUES = ["NMS", "NYQ", "NGM", "NCM", "ASE", "PCX", "BTS"]
BEGIN, END = "/* PRICES:BEGIN */", "/* PRICES:END */"


def universe() -> list[tuple[str, str, str, str]]:
    text = PAGE.read_text(encoding="utf-8")
    return re.findall(r'\["([A-Z]{2}[A-Z0-9]{9}\d)", "([^"]*)", "([^"]*)", "(fund|stock)"\]', text)


def search(isin: str, kind: str) -> str | None:
    r = requests.get("https://query2.finance.yahoo.com/v1/finance/search",
                     params={"q": isin, "quotesCount": 20, "newsCount": 0}, headers=UA, timeout=20)
    quotes = [q for q in (r.json().get("quotes") or []) if q.get("symbol")]
    venues = US_VENUES if isin.startswith("US") else EUR_VENUES
    for v in venues:
        for q in quotes:
            if q.get("exchange") == v:
                return q["symbol"]
    return quotes[0]["symbol"] if quotes else None


def main() -> int:
    rows = universe()
    try:
        known = json.loads(SYMBOLS.read_text())
    except (OSError, ValueError):
        known = {}
    for isin, ticker, name, kind in rows:
        if isin not in known:
            try:
                known[isin] = {"symbol": search(isin, kind), "name": name}
            except Exception as exc:                                     # noqa: BLE001
                print(f"  search failed for {isin} {name}: {exc}")
                known[isin] = {"symbol": None, "name": name}
            print(f"  {isin} {name[:40]:40} -> {known[isin]['symbol']}")
    # A fund found only on London is looked for again on the euro exchanges under its own code,
    # so the limit price matches the line a euro investor actually trades.
    for isin, ticker, name, kind in rows:
        v = known.get(isin) or {}
        if kind != "fund" or v.get("checked") or (v.get("symbol") or "").split(".")[-1] in ("DE", "AS", "MI", "PA", "F"):
            continue
        for cand in (f"{ticker}.DE", f"{ticker}.AS", f"{ticker}.MI"):
            try:
                if yf.Ticker(cand).fast_info["currency"] == "EUR":
                    print(f"  {isin} {name[:40]:40} -> {cand} (euro listing)")
                    v.update(symbol=cand, currency="EUR"); break
            except Exception:                                            # noqa: BLE001
                continue
        v["checked"] = True
    SYMBOLS.parent.mkdir(parents=True, exist_ok=True)
    SYMBOLS.write_text(json.dumps(known, indent=1, sort_keys=True))

    syms = sorted({v["symbol"] for v in known.values() if v.get("symbol")})
    # Every listing currency other than the euro needs its EUR rate (USD, GBP for London, DKK, CHF...).
    for v in known.values():
        if v.get("symbol") and not v.get("currency"):
            try:
                v["currency"] = yf.Ticker(v["symbol"]).fast_info["currency"]
            except Exception:                                            # noqa: BLE001
                v["currency"] = "EUR"
    ccys = sorted({("GBP" if v["currency"] in ("GBp", "GBX") else v["currency"]) for v in known.values()
                   if v.get("symbol") and v.get("currency") and v["currency"] != "EUR"})
    pairs = [f"EUR{c}=X" for c in ccys]
    data = yf.download(syms + pairs, period="6mo", auto_adjust=False, progress=False, threads=True)["Close"]
    fx = {c: float(data[f"EUR{c}=X"].dropna().iloc[-1]) for c in ccys}
    prices = {}
    for isin, ticker, name, kind in rows:
        sym = (known.get(isin) or {}).get("symbol")
        if not sym or sym not in data or data[sym].dropna().empty:
            print(f"  no price for {isin} {name}")
            continue
        series = data[sym].dropna()
        cur = known[isin].get("currency") or "EUR"
        last = float(series.iloc[-1])
        if cur in ("GBp", "GBX"):
            last, cur = last / 100, "GBP"                                # London quotes in pence
        eur = last if cur == "EUR" else last / fx[cur]
        rets = series.pct_change().dropna().tail(60)
        move = float(rets.std() * 100) if len(rets) > 10 else None
        if not math.isfinite(eur) or eur <= 0:
            continue
        prices[isin] = {"p": round(eur, 4 if eur < 1 else 2), "m": round(move, 2) if move else None,
                        "d": series.index[-1].date().isoformat(), "s": sym}
    SYMBOLS.write_text(json.dumps(known, indent=1, sort_keys=True))
    OUT.write_text(json.dumps({"asOf": date.today().isoformat(), "prices": prices}, indent=1, sort_keys=True))

    page = PAGE.read_text(encoding="utf-8")
    a, b = page.index(BEGIN), page.index(END) + len(END)
    block = f"{BEGIN}\nconst PRICES = {json.dumps(prices, separators=(',', ':'), sort_keys=True)};\n{END}"
    PAGE.write_text(page[:a] + block + page[b:], encoding="utf-8")
    print(f"prices for {len(prices)} of {len(rows)} ISINs written into {PAGE.relative_to(ROOT)}")
    return 0 if prices else 1


if __name__ == "__main__":
    sys.exit(main())
