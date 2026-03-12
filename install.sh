#!/bin/bash
# BYDFi Swap Trader - One-line installer for Claude Code skill
# Usage: bash <(curl -s https://raw.githubusercontent.com/betterlee/bydfi-swap-trader/main/install.sh)

set -e

SKILL_DIR="$HOME/.claude/skills/bydfi-swap-trader"
REPO_BASE="https://raw.githubusercontent.com/kater2026/bydfi-swap-trader/main"

echo "========================================"
echo "  BYDFi Swap Trader - Installer"
echo "========================================"
echo

# 1. Create skill directory
mkdir -p "$SKILL_DIR"
echo "[1/4] Created $SKILL_DIR"

# 2. Download files
curl -sL "$REPO_BASE/SKILL.md" -o "$SKILL_DIR/SKILL.md"
curl -sL "$REPO_BASE/bydfi_swap.py" -o "$SKILL_DIR/bydfi_swap.py"
chmod +x "$SKILL_DIR/bydfi_swap.py"
echo "[2/4] Downloaded SKILL.md + bydfi_swap.py"

# 3. Install dependency
if python3 -c "import requests" 2>/dev/null; then
    echo "[3/4] requests already installed"
else
    pip3 install requests -q
    echo "[3/4] Installed requests"
fi

# 4. Setup API keys
echo "[4/4] Configure API keys"
echo
echo "  Get your API key from:"
echo "    Test: https://www.bydtms.com (Account > API Management)"
echo "    Prod: https://www.bydfi.com  (Account > API Management)"
echo
read -p "  API Key: " api_key
read -p "  Secret Key: " secret_key
read -p "  Environment (test/prod) [test]: " env
env=${env:-test}

if [ -n "$api_key" ] && [ -n "$secret_key" ]; then
    python3 "$SKILL_DIR/bydfi_swap.py" setup "$api_key" "$secret_key" "$env"
else
    echo
    echo "  Skipped. Run later:"
    echo "    python3 $SKILL_DIR/bydfi_swap.py setup <api_key> <secret_key>"
fi

echo
echo "========================================"
echo "  Installation complete!"
echo "========================================"
echo
echo "  Verify: python3 $SKILL_DIR/bydfi_swap.py price BTC-USDT"
echo
echo "  In Claude Code, just say:"
echo "    '帮我买10张BTC合约'"
echo "    'check my BTC position'"
echo "    'what is the BTC price'"
echo
