#!/usr/bin/env python3
"""
BYDFi Swap Trading CLI - 合约交易命令行工具
通过环境变量配置 API Key，支持所有合约交易操作。

Setup (first time):
  python3 bydfi_swap.py setup <api_key> <secret_key> [test|prod] [wallet]
  # Or interactive: python3 bydfi_swap.py setup
  # Config saved to ~/.bydfi/config.json (chmod 600)
  # Env vars override config file if set.

Usage:
  python3 bydfi_swap.py <command> [options]

Commands:
  setup [api_key] [secret_key]            # Configure API keys
  # Market Data
  price BTC-USDT                          # Get latest price
  depth BTC-USDT [limit]                  # Order book
  ticker [symbol]                         # 24h ticker (all if no symbol)
  klines BTC-USDT 1m [limit]             # K-line data
  funding BTC-USDT                        # Funding rate
  exchange_info [symbol]                  # Trading rules

  # Account
  balance [asset]                         # Contract account balance
  assets spot|fund USDT                   # Spot/fund account balance
  transfer SPOT SWAP USDT 10             # Transfer between accounts
  positions [symbol]                      # Current positions

  # Trading
  buy BTC-USDT 1 [price]                 # Buy (market if no price)
  sell BTC-USDT 1 [price]                # Sell (market if no price)
  close BTC-USDT BUY [qty]              # Close position
  cancel BTC-USDT                        # Cancel all orders
  orders BTC-USDT                        # Open orders
  history [symbol] [limit]               # Order history

  # Settings
  leverage BTC-USDT [value]              # Get/set leverage
  margin_type BTC-USDT CROSS|ISOLATED    # Set margin type
  position_mode HEDGE|ONEWAY             # Set position mode
"""
import hashlib
import hmac
import json
import os
import sys
import time
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("Error: requests library required. Run: pip3 install requests")
    sys.exit(1)


# === Configuration ===
# Priority: environment variables > config file > defaults
# Config file: ~/.bydfi/config.json

CONFIG_PATH = os.path.expanduser("~/.bydfi/config.json")


def load_config():
    """Load config from ~/.bydfi/config.json, merge with env vars."""
    conf = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            conf = json.load(f)
    return {
        "api_key": os.environ.get("BYDFI_API_KEY", conf.get("api_key", "")),
        "secret_key": os.environ.get("BYDFI_SECRET_KEY", conf.get("secret_key", "")),
        "env": os.environ.get("BYDFI_ENV", conf.get("env", "test")),
        "wallet": os.environ.get("BYDFI_WALLET", conf.get("wallet", "W001")),
    }


def cmd_setup(args):
    """Interactive setup: create ~/.bydfi/config.json"""
    config_dir = os.path.dirname(CONFIG_PATH)
    os.makedirs(config_dir, mode=0o700, exist_ok=True)

    existing = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            existing = json.load(f)

    if len(args) >= 2:
        # Non-interactive: setup <api_key> <secret_key> [env] [wallet]
        existing["api_key"] = args[0]
        existing["secret_key"] = args[1]
        if len(args) > 2:
            existing["env"] = args[2]
        if len(args) > 3:
            existing["wallet"] = args[3]
    else:
        print("BYDFi Swap Trader - Setup")
        print("=" * 40)
        existing["api_key"] = input(f"API Key [{existing.get('api_key', '')[:8]}...]: ").strip() or existing.get("api_key", "")
        existing["secret_key"] = input(f"Secret Key [{existing.get('secret_key', '')[:8]}...]: ").strip() or existing.get("secret_key", "")
        existing["env"] = input(f"Environment (test/prod) [{existing.get('env', 'test')}]: ").strip() or existing.get("env", "test")
        existing["wallet"] = input(f"Wallet [{existing.get('wallet', 'W001')}]: ").strip() or existing.get("wallet", "W001")

    with open(CONFIG_PATH, "w") as f:
        json.dump(existing, f, indent=2)
    os.chmod(CONFIG_PATH, 0o600)

    print(f"\nConfig saved to {CONFIG_PATH} (permissions: 600)")
    print(f"  API Key:    {existing['api_key'][:8]}...{existing['api_key'][-4:]}")
    print(f"  Secret Key: {existing['secret_key'][:8]}...{existing['secret_key'][-4:]}")
    print(f"  Env:        {existing['env']}")
    print(f"  Wallet:     {existing['wallet']}")
    print("\nReady to trade! Try: python3 bydfi_swap.py price BTC-USDT")


cfg = load_config()
API_KEY = cfg["api_key"]
SECRET_KEY = cfg["secret_key"]
ENV = cfg["env"]
WALLET = cfg["wallet"]

if ENV == "prod":
    BASE_URL = "https://api.bydfi.com/api"
else:
    BASE_URL = "https://api.bydtms.com/api"


# === Auth ===

def sign(query_string="", body=""):
    ts = str(int(time.time() * 1000))
    input_str = API_KEY + ts + (query_string or body)
    sig = hmac.new(SECRET_KEY.encode(), input_str.encode(), hashlib.sha256).hexdigest()
    return {
        "X-API-KEY": API_KEY,
        "X-API-TIMESTAMP": ts,
        "X-API-SIGNATURE": sig,
        "Content-Type": "application/json",
        "Accept-Language": "en-US",
    }


def api_get(path, params=None):
    if params:
        qs = urlencode(sorted(params.items()))
    else:
        qs = ""
    headers = sign(query_string=qs)
    resp = requests.get(f"{BASE_URL}{path}", params=params, headers=headers, timeout=10)
    return resp.json()


def api_post(path, body_dict):
    body_str = json.dumps(body_dict, separators=(",", ":"), sort_keys=False)
    headers = sign(body=body_str)
    resp = requests.post(f"{BASE_URL}{path}", data=body_str, headers=headers, timeout=10)
    return resp.json()


def extract(resp):
    if isinstance(resp, dict) and "data" in resp:
        return resp.get("code", 0), resp["data"]
    return resp.get("code", 0), resp


def output(data, title=None):
    if title:
        print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def check_keys():
    if not API_KEY or not SECRET_KEY:
        print("Error: API keys not configured.")
        print()
        print("Run setup first:")
        print("  python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py setup <api_key> <secret_key>")
        print()
        print("Or set environment variables:")
        print("  export BYDFI_API_KEY='your-key'")
        print("  export BYDFI_SECRET_KEY='your-secret'")
        print()
        print(f"Config file: {CONFIG_PATH}")
        sys.exit(1)


# === Market Data ===

def cmd_price(args):
    symbol = args[0] if args else "BTC-USDT"
    resp = api_get("/v1/swap/market/ticker/price", {"symbol": symbol})
    code, data = extract(resp)
    if code == 200:
        if isinstance(data, dict):
            print(f"{symbol}: {data.get('price', data)}")
        else:
            output(data)
    else:
        output(resp, "Error")


def cmd_depth(args):
    symbol = args[0] if args else "BTC-USDT"
    limit = int(args[1]) if len(args) > 1 else 10
    resp = api_get("/v1/swap/market/depth", {"symbol": symbol, "limit": limit})
    code, data = extract(resp)
    output(data, f"Depth {symbol}")


def cmd_ticker(args):
    params = {"symbol": args[0]} if args else {}
    resp = api_get("/v1/swap/market/ticker/24hr", params)
    code, data = extract(resp)
    if code == 200 and isinstance(data, list):
        for t in data[:20]:
            s = t.get("symbol", t.get("s", "?"))
            c = t.get("lastPrice", t.get("c", "?"))
            chg = t.get("priceChangePercent", "?")
            print(f"  {s:15s}  price={c}  change={chg}%")
    else:
        output(data, "Ticker")


def cmd_klines(args):
    symbol = args[0] if args else "BTC-USDT"
    interval = args[1] if len(args) > 1 else "1m"
    limit = int(args[2]) if len(args) > 2 else 10
    now = int(time.time() * 1000)
    start = now - limit * 60 * 1000 * 10
    resp = api_get("/v1/swap/market/klines", {
        "symbol": symbol, "interval": interval,
        "startTime": start, "endTime": now, "limit": limit,
    })
    code, data = extract(resp)
    output(data, f"Klines {symbol} {interval}")


def cmd_funding(args):
    symbol = args[0] if args else "BTC-USDT"
    resp = api_get("/v1/swap/market/funding_rate", {"symbol": symbol})
    code, data = extract(resp)
    output(data, f"Funding Rate {symbol}")


def cmd_exchange_info(args):
    resp = api_get("/v1/swap/market/exchange_info")
    code, data = extract(resp)
    if code == 200 and isinstance(data, list):
        if args:
            data = [d for d in data if d.get("symbol") == args[0]]
        for d in data[:30]:
            s = d.get("symbol", "?")
            cf = d.get("contractFactor", "?")
            print(f"  {s:15s}  contractFactor={cf}")
    else:
        output(data)


# === Account ===

def cmd_balance(args):
    check_keys()
    params = {"wallet": WALLET}
    if args:
        params["asset"] = args[0]
    resp = api_get("/v1/swap/account/balance", params)
    code, data = extract(resp)
    if code == 200 and isinstance(data, list):
        for b in data:
            a = b.get("asset", "?")
            bal = b.get("balance", "?")
            avail = b.get("availableBalance", "?")
            frozen = b.get("frozen", "0")
            print(f"  {a:8s}  balance={bal}  available={avail}  frozen={frozen}")
    else:
        output(resp, "Balance")


def cmd_assets(args):
    check_keys()
    if len(args) < 2:
        print("Usage: assets <spot|fund> <asset>")
        return
    resp = api_get("/v1/account/assets", {"walletType": args[0], "asset": args[1]})
    code, data = extract(resp)
    output(data, f"Assets {args[0]} {args[1]}")


def cmd_transfer(args):
    check_keys()
    if len(args) < 4:
        print("Usage: transfer <fromType> <toType> <asset> <amount>")
        print("  Types: SPOT, SWAP, FUND")
        return
    resp = api_post("/v1/account/transfer", {
        "asset": args[2], "fromType": args[0], "toType": args[1], "amount": args[3],
    })
    output(resp, "Transfer")


def cmd_positions(args):
    check_keys()
    params = {"contractType": "FUTURE"}
    if args:
        params["symbol"] = args[0]
    resp = api_get("/v1/swap/trade/positions", params)
    code, data = extract(resp)
    if code == 200 and isinstance(data, list):
        positions = [p for p in data if float(p.get("volume", 0)) > 0]
        if not positions:
            print("  No open positions")
        for p in positions:
            s = p.get("symbol", "?")
            side = p.get("side", "?")
            vol = p.get("volume", "0")
            avg = p.get("avgPrice", "?")
            pnl = p.get("unPnl", "0")
            mark = p.get("markPrice", "?")
            print(f"  {s:15s}  {side:4s}  vol={vol}  avgPrice={avg}  markPrice={mark}  PnL={pnl}")
    else:
        output(resp, "Positions")


# === Trading ===

def get_contract_factor(symbol):
    """Get contractFactor for a symbol to convert coin amount to contracts."""
    resp = api_get("/v1/swap/market/exchange_info")
    code, data = extract(resp)
    if code == 200 and isinstance(data, list):
        for item in data:
            if item.get("symbol") == symbol:
                return float(item.get("contractFactor", 1))
    return None


def cmd_buy(args):
    check_keys()
    if len(args) < 2:
        print("Usage: buy <symbol> <quantity> [price]")
        print("  quantity = number of contracts (integer)")
        print("  price = limit price (omit for market order)")
        return
    symbol, qty = args[0], args[1]
    body = {
        "wallet": WALLET, "symbol": symbol,
        "side": "BUY", "quantity": int(qty),
    }
    if len(args) > 2:
        body["type"] = "LIMIT"
        body["price"] = float(args[2])
        body["timeInForce"] = "GTC"
    else:
        body["type"] = "MARKET"

    resp = api_post("/v1/swap/trade/place_order", body)
    code, data = extract(resp)
    if code == 200:
        print(f"  Order placed: {data}")
    elif code == 510:
        print("  Rate limited (510). Trying batch_place_order fallback...")
        batch_body = {
            "wallet": WALLET,
            "orders": [{
                "symbol": symbol, "side": "BUY",
                "type": body["type"], "quantity": str(int(qty)),
                **({"price": str(body["price"]), "timeInForce": "GTC"} if "price" in body else {}),
            }],
        }
        resp2 = api_post("/v1/swap/trade/batch_place_order", batch_body)
        output(resp2, "Batch Fallback")
    else:
        output(resp, "Error")


def cmd_sell(args):
    check_keys()
    if len(args) < 2:
        print("Usage: sell <symbol> <quantity> [price]")
        return
    symbol, qty = args[0], args[1]
    body = {
        "wallet": WALLET, "symbol": symbol,
        "side": "SELL", "quantity": int(qty),
    }
    if len(args) > 2:
        body["type"] = "LIMIT"
        body["price"] = float(args[2])
        body["timeInForce"] = "GTC"
    else:
        body["type"] = "MARKET"

    resp = api_post("/v1/swap/trade/place_order", body)
    code, data = extract(resp)
    if code == 200:
        print(f"  Order placed: {data}")
    elif code == 510:
        print("  Rate limited (510). Trying batch_place_order fallback...")
        batch_body = {
            "wallet": WALLET,
            "orders": [{
                "symbol": symbol, "side": "SELL",
                "type": body["type"], "quantity": str(int(qty)),
                **({"price": str(body["price"]), "timeInForce": "GTC"} if "price" in body else {}),
            }],
        }
        resp2 = api_post("/v1/swap/trade/batch_place_order", batch_body)
        output(resp2, "Batch Fallback")
    else:
        output(resp, "Error")


def cmd_close(args):
    check_keys()
    if len(args) < 2:
        print("Usage: close <symbol> <BUY|SELL> [quantity]")
        print("  Close a position. Side = the OPPOSITE of your position side.")
        print("  e.g. to close a BUY position, use: close BTC-USDT SELL")
        return
    symbol, side = args[0], args[1].upper()
    body = {
        "wallet": WALLET, "symbol": symbol,
        "side": side, "type": "MARKET",
    }
    if len(args) > 2:
        body["quantity"] = int(args[2])
    else:
        # Get position to determine quantity
        params = {"contractType": "FUTURE", "symbol": symbol}
        pos_resp = api_get("/v1/swap/trade/positions", params)
        pos_code, pos_data = extract(pos_resp)
        if pos_code == 200 and isinstance(pos_data, list):
            opp_side = "BUY" if side == "SELL" else "SELL"
            matching = [p for p in pos_data if p.get("symbol") == symbol
                       and p.get("side") == opp_side and float(p.get("volume", 0)) > 0]
            if matching:
                vol = float(matching[0]["volume"])
                cf = get_contract_factor(symbol) or 0.001
                body["quantity"] = int(vol / cf)
            else:
                print(f"  No {opp_side} position found for {symbol}")
                return

    resp = api_post("/v1/swap/trade/place_order", body)
    code, data = extract(resp)
    if code == 200:
        print(f"  Position closed: {data}")
    else:
        output(resp, "Error")


def cmd_cancel(args):
    check_keys()
    if not args:
        print("Usage: cancel <symbol>")
        return
    resp = api_post("/v1/swap/trade/cancel_all_order", {
        "wallet": WALLET, "symbol": args[0],
    })
    output(resp, f"Cancel All {args[0]}")


def cmd_orders(args):
    check_keys()
    if not args:
        print("Usage: orders <symbol>")
        return
    resp = api_get("/v1/swap/trade/open_order", {"wallet": WALLET, "symbol": args[0]})
    code, data = extract(resp)
    output(data, f"Open Orders {args[0]}")


def cmd_history(args):
    check_keys()
    params = {"contractType": "FUTURE"}
    if args:
        params["symbol"] = args[0]
    params["limit"] = int(args[1]) if len(args) > 1 else 10
    resp = api_get("/v1/swap/trade/history_order", params)
    code, data = extract(resp)
    if code == 200 and isinstance(data, list):
        for o in data[:20]:
            s = o.get("symbol", "?")
            side = o.get("side", "?")
            t = o.get("type", "?")
            status = o.get("status", "?")
            qty = o.get("origQty", "?")
            price = o.get("price", o.get("avgPrice", "?"))
            print(f"  {s:15s}  {side:4s}  {t:8s}  {status:10s}  qty={qty}  price={price}")
    else:
        output(resp, "History")


# === Settings ===

def cmd_leverage(args):
    check_keys()
    if not args:
        print("Usage: leverage <symbol> [value]")
        return
    symbol = args[0]
    if len(args) > 1:
        resp = api_post("/v1/swap/trade/leverage", {
            "wallet": WALLET, "symbol": symbol, "leverage": int(args[1]),
        })
    else:
        resp = api_get("/v1/swap/trade/leverage", {"wallet": WALLET, "symbol": symbol})
    code, data = extract(resp)
    output(data, f"Leverage {symbol}")


def cmd_margin_type(args):
    check_keys()
    if len(args) < 2:
        print("Usage: margin_type <symbol> <CROSS|ISOLATED>")
        return
    resp = api_post("/v1/swap/user_data/margin_type", {
        "contractType": "FUTURE", "symbol": args[0],
        "wallet": WALLET, "marginType": args[1].upper(),
    })
    output(resp, f"Margin Type {args[0]}")


def cmd_position_mode(args):
    check_keys()
    if not args:
        print("Usage: position_mode <HEDGE|ONEWAY>")
        return
    resp = api_post("/v1/swap/user_data/position_side/dual", {
        "contractType": "FUTURE", "wallet": WALLET,
        "positionType": args[0].upper(), "settleCoin": "USDT",
    })
    output(resp, "Position Mode")


# === Main ===

COMMANDS = {
    "setup": cmd_setup,
    "price": cmd_price,
    "depth": cmd_depth,
    "ticker": cmd_ticker,
    "klines": cmd_klines,
    "funding": cmd_funding,
    "exchange_info": cmd_exchange_info,
    "balance": cmd_balance,
    "assets": cmd_assets,
    "transfer": cmd_transfer,
    "positions": cmd_positions,
    "buy": cmd_buy,
    "sell": cmd_sell,
    "close": cmd_close,
    "cancel": cmd_cancel,
    "orders": cmd_orders,
    "history": cmd_history,
    "leverage": cmd_leverage,
    "margin_type": cmd_margin_type,
    "position_mode": cmd_position_mode,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(sorted(COMMANDS.keys()))}")
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])
