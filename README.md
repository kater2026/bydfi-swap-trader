# BYDFi Swap Trader - Claude Code Skill

A Claude Code skill for trading crypto perpetual contracts on BYDFi exchange. Configure your API key once, then trade by talking to Claude.

## Quick Install

```bash
bash <(curl -s https://raw.githubusercontent.com/kater2026/bydfi-swap-trader/feat/initial-release/install.sh)
```

## Manual Install

```bash
# 1. Copy files
mkdir -p ~/.claude/skills/bydfi-swap-trader
cp SKILL.md bydfi_swap.py ~/.claude/skills/bydfi-swap-trader/

# 2. Install dependency
pip3 install requests

# 3. Configure API keys
python3 ~/.claude/skills/bydfi-swap-trader/bydfi_swap.py setup <your-api-key> <your-secret-key> [test|prod]
```

## Get API Keys

| Environment | URL | Note |
|-------------|-----|------|
| Test (testnet) | https://www.bydtms.com | Safe to experiment |
| Prod (real) | https://www.bydfi.com | Real money |

Go to **Account > API Management > Create API Key**, enable **Transaction** permission.

## Usage

Just talk to Claude:

```
"帮我买10张BTC合约"
"查看我的持仓"
"BTC现在什么价格"
"设置BTC杠杆为20倍"
"平掉BTC多单"
```

Or use the CLI directly:

```bash
S=~/.claude/skills/bydfi-swap-trader/bydfi_swap.py

python3 $S price BTC-USDT          # Check price
python3 $S balance                  # Check balance
python3 $S positions                # View positions
python3 $S buy BTC-USDT 10         # Buy 10 contracts (market)
python3 $S buy BTC-USDT 10 65000   # Buy 10 contracts (limit @ 65000)
python3 $S sell BTC-USDT 10        # Sell 10 contracts
python3 $S close BTC-USDT SELL     # Close BUY position
python3 $S leverage BTC-USDT 10    # Set leverage
python3 $S history BTC-USDT        # Order history
python3 $S help                    # All commands
```

## Configuration

Config saved at `~/.bydfi/config.json` (permissions 600):

```json
{
  "api_key": "your-api-key",
  "secret_key": "your-secret-key",
  "env": "test",
  "wallet": "W001"
}
```

Environment variables override config file if set:
```bash
export BYDFI_API_KEY="..."
export BYDFI_SECRET_KEY="..."
export BYDFI_ENV="prod"
```

## Important Notes

- **Quantity = contracts, not coins.** BTC: 1 contract = 0.001 BTC. Buy 0.01 BTC = 10 contracts.
- **Rate limit:** max 1 order/sec. Exceeding triggers 15-30 min ban.
- **Default env is `test`** (testnet). Set `env` to `prod` for real trading.

## Files

```
bydfi-swap-trader/
├── SKILL.md          # Claude Code skill definition
├── bydfi_swap.py     # Trading CLI (20 commands)
├── install.sh        # One-line installer
└── README.md         # This file
```

## License

MIT
