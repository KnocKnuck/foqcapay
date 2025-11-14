# Live Trading Guide - FOQCAPAY

## 🚨 CRITICAL: Read This Before Enabling Live Trading

Live trading mode executes **REAL orders** on CoinEx with **REAL MONEY**. You can **LOSE MONEY**.

---

## Prerequisites

Before enabling live trading:

### 1. Test Thoroughly in Demo Mode
- ✅ Run strategies in demo mode for at least 1 week
- ✅ Verify win rate is acceptable (>55% recommended)
- ✅ Ensure drawdown stays within limits
- ✅ Test all features (stop-loss, take-profit, emergency stop)

### 2. CoinEx API Key Setup
1. Create CoinEx account: https://www.coinex.com
2. Complete KYC verification
3. Fund your account with USDC
4. Generate API key:
   - Go to Account → API Management
   - Create new API key
   - **Enable**: Spot Trading
   - **Disable**: Withdrawals (for security)
   - Save API Key and Secret
5. Whitelist your IP address (recommended)

### 3. Configure API Keys Securely
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit .env file
nano backend/.env

# Add your API credentials (encrypted automatically)
COINEX_API_KEY=your_actual_api_key_here
COINEX_API_SECRET=your_actual_secret_here
```

**IMPORTANT**: Never commit `.env` to git! It's in `.gitignore`.

---

## Production Safeguards

FOQCAPAY has multiple layers of protection:

### Hard Limits (Cannot be overridden)
| Limit | Value | Description |
|-------|-------|-------------|
| Max Order Size | $5,000 | No single order can exceed this |
| Max Daily Volume | $20,000 | Total trading volume per day |
| Max Orders/Minute | 10 | Rate limiting |
| Max Open Positions | 10 | Simultaneous positions |
| Min Order Interval | 1 second | Time between orders |

### Configurable Risk Controls
| Setting | Default | Description |
|---------|---------|-------------|
| Max Drawdown | 10% | Auto-pause if losses exceed |
| Daily Loss Limit | 5% | Auto-pause if daily loss exceeds |
| Stop Loss | 2% | Default per-trade stop loss |
| Position Size | 20% | Max % of capital per position |

---

## Enabling Live Trading

### Step 1: Verify Configuration
```bash
# Check environment
cat backend/.env | grep TRADING_MODE
# Should show: TRADING_MODE=demo

# Verify API keys are set
cat backend/.env | grep COINEX_API_KEY
# Should show: COINEX_API_KEY=<your key>
```

### Step 2: Enable Live Mode
```bash
# Edit .env
nano backend/.env

# Change:
TRADING_MODE=live
```

### Step 3: Restart Application
```bash
# Restart backend
cd backend
python -m uvicorn main:app --reload

# Backend will log:
# "Live Trading Service initialized (live_enabled=True)"
```

### Step 4: Confirm in UI
1. Open dashboard at http://localhost:3000
2. You'll see a **BIG RED WARNING**: "LIVE MODE ENABLED"
3. Confirm you understand the risks
4. Type "ENABLE LIVE TRADING" to confirm

---

## Safety Checklist Before First Live Trade

- [ ] Tested strategies in demo mode for ≥7 days
- [ ] Win rate ≥55% in demo mode
- [ ] Max drawdown <10% in demo testing
- [ ] CoinEx API key configured with:
  - [ ] Spot trading enabled
  - [ ] Withdrawals disabled
  - [ ] IP whitelist configured
- [ ] Starting with small capital ($500-1000 max)
- [ ] Risk limits configured appropriately
- [ ] Stop-loss and take-profit set
- [ ] Emergency stop button tested
- [ ] Monitoring plan in place (check daily minimum)

---

## Starting Small

**Recommendation**: Start with minimal capital to test live trading.

```bash
# In .env, use conservative limits
DEFAULT_STOP_LOSS_PCT=1.5  # Tighter stops
MAX_DAILY_LOSS_PCT=3.0     # Lower daily limit
```

**Example First Week**:
- Days 1-3: $500 capital, max 1 position
- Days 4-7: $1,000 capital, max 2 positions
- Week 2+: Gradually increase if profitable

---

## Monitoring Your Bot

### Daily Monitoring (Required)
1. Check dashboard daily
2. Review open positions
3. Check P&L and drawdown
4. Verify no alerts

### Weekly Review
1. Calculate weekly ROI
2. Analyze winning vs losing trades
3. Review strategy performance
4. Adjust risk limits if needed

### When to Stop
Stop trading immediately if:
- Daily loss limit hit (auto-pauses)
- Max drawdown hit (auto-pauses)
- Win rate drops below 45%
- Unusual behavior or errors
- Market conditions change dramatically

---

## Emergency Procedures

### Emergency Stop Button
1. Click **"Emergency Stop"** button in dashboard
2. Confirm action
3. All positions close immediately at market price
4. Trading paused until manually resumed

### Manual Intervention
If bot is unresponsive:
1. Log into CoinEx directly
2. Manually close positions
3. Cancel open orders
4. Disable API key if necessary

---

## Common Issues

### "Insufficient Balance" Error
- **Cause**: Not enough USDC in account
- **Fix**: Fund account or reduce position sizes

### "API Key Invalid" Error
- **Cause**: Wrong credentials or key disabled
- **Fix**: Verify API key in CoinEx dashboard

### "Daily Volume Limit Reached"
- **Cause**: Traded $20,000 in one day
- **Fix**: Wait until midnight UTC for reset

### "Order Rejected - Price Too Far From Market"
- **Cause**: Limit order price too far from current
- **Fix**: Use market orders or adjust limits

---

## Security Best Practices

### API Key Security
✅ **DO**:
- Create API key with minimal permissions
- Disable withdrawal permissions
- Use IP whitelist
- Rotate keys periodically
- Keep secrets in .env (never commit)

❌ **DON'T**:
- Share API keys
- Enable withdrawal permissions
- Commit secrets to git
- Use same key for multiple bots
- Ignore security warnings

### Account Security
- Enable 2FA on CoinEx account
- Use strong unique password
- Monitor account activity
- Set up email alerts
- Withdraw profits regularly (manually)

---

## Performance Expectations

### Realistic Expectations
- **Good**: 5-15% monthly return
- **Excellent**: 15-25% monthly return
- **Warning**: >30% monthly = high risk

### Risk Assessment
- **Low Risk**: <5% drawdown, 50-60% win rate
- **Medium Risk**: 5-10% drawdown, 55-65% win rate
- **High Risk**: >10% drawdown, 60%+ win rate

---

## Support and Troubleshooting

### Logs
Check logs for errors:
```bash
# Backend logs
tail -f backend/logs/app.log

# Look for errors
grep "ERROR" backend/logs/app.log
```

### Bug Reporting
If you encounter bugs:
1. Stop live trading immediately
2. Switch to demo mode
3. Note error messages
4. Report issue with full details

---

## Legal Disclaimer

⚠️ **IMPORTANT LEGAL NOTICE**:

- Automated trading carries significant risk
- You can lose all capital invested
- Past performance does not guarantee future results
- No guarantee of profitability
- FOQCAPAY developers are not responsible for trading losses
- Use at your own risk
- Only trade what you can afford to lose
- Consult a financial advisor before trading

By enabling live trading, you acknowledge:
- You understand the risks
- You accept full responsibility for losses
- You have tested thoroughly in demo mode
- You will monitor the bot regularly
- You agree to the terms above

---

## Need Help?

- 📖 Documentation: Check DOCUMENTATION_GUIDELINES.md
- 🐛 Bugs: Report in GitHub issues
- 💬 Questions: Check project README

**Remember**: When in doubt, use demo mode! There's no rush to go live.
