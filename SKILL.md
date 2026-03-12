---
name: bydfi-swap-trader
description: Use when user wants to trade crypto perpetual contracts on BYDFi - placing orders, checking positions, querying prices, managing leverage, or transferring funds. Triggers on keywords like swap, contract, futures, open position, close position, leverage, buy BTC, sell ETH, check balance.
---

# BYDFi Swap Trader

Crypto perpetual contract trading on BYDFi exchange via CLI tool.

## Setup

### Step 1: Install
Copy the skill folder to `~/.claude/skills/bydfi-swap-trader/` and install dependency:
```bash
pip3 install requests
```

### Step 2: Configure API Keys
Run setup command (one-time, config persists across sessions):
```bash
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py setup <your-api-key> <your-secret-key> [test|prod] [wallet]
```

Config is saved to `~/.bydfi/config.json` (permissions 600, only owner readable).

**Configuration priority:** environment variables > config file > defaults.

### Where to get API Keys
1. Login to [BYDFi](https://www.bydfi.com) (prod) or [BYDTms](https://www.bydtms.com) (test)
2. Go to **Account → API Management → Create API Key**
3. Enable **Transaction** permission for trading operations

### Step 3: Verify
```bash
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py price BTC-USDT
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py balance
```

### Config File Format (`~/.bydfi/config.json`)
```json
{
  "api_key": "your-api-key",
  "secret_key": "your-secret-key",
  "env": "test",
  "wallet": "W001"
}
```

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| api_key | Yes | - | BYDFi API Key |
| secret_key | Yes | - | BYDFi Secret Key |
| env | No | `test` | `test` (testnet) or `prod` (real money) |
| wallet | No | `W001` | Default contract wallet ID |

## How to Use

Execute trading operations by running the script via Bash tool:

```bash
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py <command> [args]
```

## Quick Reference

| Action | Command |
|--------|---------|
| Check price | `price BTC-USDT` |
| Order book | `depth BTC-USDT 10` |
| 24h stats | `ticker BTC-USDT` |
| K-lines | `klines BTC-USDT 1m 20` |
| Funding rate | `funding BTC-USDT` |
| Trading pairs | `exchange_info` |
| Contract balance | `balance` |
| Spot balance | `assets spot USDT` |
| Transfer funds | `transfer SPOT SWAP USDT 100` |
| Current positions | `positions` |
| **Market buy** | `buy BTC-USDT 22` |
| **Limit buy** | `buy BTC-USDT 22 65000` |
| **Market sell** | `sell BTC-USDT 22` |
| **Close position** | `close BTC-USDT SELL` |
| Cancel orders | `cancel BTC-USDT` |
| Open orders | `orders BTC-USDT` |
| Order history | `history BTC-USDT 10` |
| Get/set leverage | `leverage BTC-USDT` / `leverage BTC-USDT 10` |
| Margin type | `margin_type BTC-USDT CROSS` |
| Position mode | `position_mode HEDGE` |

## Critical Rules

### Quantity = Contracts, NOT Coins
`quantity` is **contract count** (integer). Each symbol has a `contractFactor`:
- BTC-USDT: 1 contract = 0.001 BTC → buy 0.01 BTC = `buy BTC-USDT 10`
- ETH-USDT: 1 contract = 0.01 ETH → buy 0.1 ETH = `sell ETH-USDT 10`

Use `exchange_info <symbol>` to check contractFactor.

### Closing Positions
To close, use the **opposite side**: close a BUY position with `close SYMBOL SELL`.
If quantity is omitted, auto-detects from current position.

### Rate Limiting
- `place_order`: 1 req/sec max. Exceeding triggers **15-30 min ban**.
- On 510 error, script auto-falls back to `batch_place_order`.
- Never rapid-fire orders. Wait between trading operations.

### Environment
- `BYDFI_ENV=test` → api.bydtms.com (testnet, safe to experiment)
- `BYDFI_ENV=prod` → api.bydfi.com (real money, use with caution)

## Workflow Examples

### Check market and open a position
```bash
# 1. Check current price
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py price BTC-USDT
# 2. Check balance
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py balance
# 3. Set leverage
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py leverage BTC-USDT 10
# 4. Buy 10 contracts at market
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py buy BTC-USDT 10
# 5. Verify position
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py positions
```

### Close all and withdraw
```bash
# 1. Close position
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py close BTC-USDT SELL
# 2. Transfer from SWAP to SPOT
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py transfer SWAP SPOT USDT 100
```

## Safety

- Always confirm with user before executing trades on prod
- Default environment is `test` (testnet)
- Show price and balance before placing orders
- Never auto-trade without explicit user instruction
