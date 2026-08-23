# AgentLicense Live Demo Script

**Duration:** 3-4 minutes

This script demonstrates the complete Agent → License → Payment → Resource → Usage workflow.

## Setup (Pre-Demo)

```bash
# Terminal 1: Start Backend
cd backend
. venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start Frontend  
cd frontend
npm run dev

# Open browser: http://localhost:3000
```

## Demo Sequence

### 1. **System Status Check** (30 seconds)
"Let's verify the system is operational..."

- Show dashboard loading
- Point out status badges:
  - ✓ Database OK (green)
  - 🎭 DEMO MODE (orange) - "Safe testing mode"
  - ⚠ Algorand Demo (no testnet configured)

```
Dashboard loaded successfully.
All systems operational in demo mode.
```

### 2. **Resource Discovery** (45 seconds)
"AgentLicense provides access to digital resources..."

- Scroll down to "Available Resources" card
- Point out three demo resources:
  - Market Research Dataset
  - Fine-tuned NLP Model
  - Real-time Market API

```
Say: "These are example resources. Agents can discover
available resources and their license options here."
```

- Click "Market Research Dataset"
  - Shows three license options:
    - Single Use: $0.01 (1 use, no commercial)
    - 10-Use License: $0.05 (10 uses, training allowed)
    - Commercial License: $0.20 (100 uses, commercial allowed)

### 3. **Configure Agent Task** (60 seconds)
"Now, let's configure an autonomous agent with specific requirements..."

Back on Dashboard:

```
Task: "Analyze this dataset for commercial research"
Budget: Set slider to $0.10
Required Uses: 5
Commercial Use Required: ✓ (checkbox)
```

Say:
```
"The agent has a budget of $0.10,
needs at least 5 uses,
and requires commercial rights.

Now let's see which license the agent selects."
```

### 4. **Agent Decision** (45 seconds)
"This is where the agent decision engine kicks in..."

Click "Run Agent Decision"

Show loading spinner for 2 seconds, then decision appears:

```
DECISION REJECTED - No Compatible Licenses
(Agent explains why each license was rejected)
```

Say:
```
"The agent evaluated each license and found none
meet all requirements:
- Single Use: No commercial rights
- 10-Use: No commercial rights
- Commercial: $0.20 exceeds budget of $0.10

This is the agent being responsible with budget constraints."
```

### 5. **Adjust Requirements** (60 seconds)
"Let's adjust the budget and try again..."

Back to Dashboard:
- Adjust budget slider to $0.25

Click "Run Agent Decision" again

Now shows:
```
✓ DECISION ACCEPTED
Selected License: Commercial 10-Use License
Reason: "Meets all requirements within budget"
Confidence: 100%
```

Say:
```
"Excellent! The agent found a compatible license.
With the increased budget of $0.25,
the Commercial License at $0.20 now satisfies:
✓ 100 uses (exceeds required 5)
✓ Commercial use permitted
✓ Within budget
✓ Training allowed

Now let's execute the payment flow."
```

### 6. **Payment Initiation** (45 seconds)
Click "Proceed to Payment"

Navigate to Payment view:

```
x402 PAYMENT PROTOCOL
Payment Status: Initiated
Payment ID: pay_xxxxxxxxxxxxx
```

Say:
```
"The payment initiation triggered the x402 protocol.
This is an HTTP 402 Payment Required flow.

The agent now needs to submit payment
through the x402 facilitator."
```

### 7. **x402 Payment Submission** (60 seconds)
Click "Simulate Demo Payment"

Shows:
```
⚠️ Demo Transaction Generated (not real blockchain)
Transaction ID: DEMO_xxxxxxxx
```

Say:
```
"In demo mode, we simulate the payment.
The transaction ID starts with 'DEMO_'
showing this is simulated, not a real blockchain transaction.

In production with ALGORAND_WALLET_ADDRESS configured,
this would be a real Algorand transaction."
```

### 8. **Payment Verification** (45 seconds)
Click "Verify Payment (x402)"

Shows:
```
✓ Payment verified on Algorand
License issued
```

Say:
```
"The x402 payment was verified.
Even in demo mode, we follow the complete protocol:

1. Payment Request → HTTP 402
2. Payment Submission → x402 protocol
3. Payment Verification → Check transaction
4. Algorand Settlement → Record provenance
5. License Issuance → Create license record
6. Resource Unlock → Access granted"
```

### 9. **Resource Access** (45 seconds)
Automatically transitions to Success view

Shows:
```
✓ SUCCESS
Resource accessed and license enforced

Message: ✓ Resource accessed! Usage consumed. 9 uses remaining
Uses Remaining: 9
```

Say:
```
"The license was issued and the resource was accessed.

The agent now has a valid license with:
✓ Uses Remaining: 9
✓ Commercial rights: Permitted
✓ Expiration: 90 days
✓ Payment verified on blockchain

Notice the usage tracking:
- License created with 10 uses
- One access consumed
- 9 uses remaining"
```

### 10. **Verify Usage Enforcement** (60 seconds)
Open browser dev console or show the API response:

```bash
curl http://localhost:8000/licenses/<license_id> -s | python -m json.tool
```

Point out:
```json
{
  "uses_remaining": 9,
  "status": "active",
  "algorand_tx_id": "DEMO_xxxxxxxx"
}
```

Say:
```
"This demonstrates the complete workflow:

1. ✓ Agent discovered available licenses
2. ✓ Agent evaluated options autonomously
3. ✓ Agent selected appropriate license
4. ✓ HTTP 402 triggered (payment required)
5. ✓ x402 payment flow executed
6. ✓ Payment verified
7. ✓ Algorand provenance recorded
8. ✓ License issued and activated
9. ✓ Resource accessed
10. ✓ Usage tracked and enforced

This is autonomous commerce with
machine-readable licensing."
```

## Key Points to Emphasize

### Machine-Readable Licensing
```
- Licenses are JSON with explicit terms
- Agents can parse and evaluate automatically
- No ambiguity in permissions
```

### Agent Autonomy
```
- Agent made decisions without human intervention
- Evaluated multiple options
- Applied constraints (budget, permissions)
- Selected optimal choice
```

### HTTP 402 Payment Required
```
- Protected resource endpoint
- Returns 402 without valid license
- Communicates payment requirement
- Triggers x402 flow
```

### x402 Payment Protocol
```
- Modern HTTP payment protocol
- Supports USDC stablecoin
- Integrates with facilitator
- Verifiable and auditable
```

### Blockchain Integration
```
- Algorand settlement for provenance
- Transaction recording
- Demo mode shows transaction ID clearly
- Real Algorand testnet when configured
```

### Usage Enforcement
```
- Licenses have usage limits
- Each access decrements counter
- Access denied when exhausted
- Tracked in database
```

## Common Questions

**Q: Is this a real blockchain transaction?**
A: In demo mode, no - it's simulated for testing. In production mode with configured Algorand credentials, yes - it's a real testnet transaction.

**Q: Can I see the actual blockchain transaction?**
A: In testnet mode, yes. Transaction IDs are real and can be verified on the Algorand testnet explorer.

**Q: How does the agent decide?**
A: The agent uses deterministic rules - it evaluates each license against requirements and selects the cheapest compatible option.

**Q: Is the payment actually processed?**
A: In demo mode, no - it's simulated safely. In production, the x402 protocol would handle real payments.

**Q: What happens when uses are exhausted?**
A: The license is marked as exhausted and access is denied. A new license must be purchased.

## Failure Scenarios (Optional)

If time permits, demonstrate error handling:

### Scenario 1: Budget Too Low
```
Set Budget: $0.01
Required Uses: 10
→ No compatible licenses (all too expensive)
→ Agent rejects decision with reason
```

### Scenario 2: Insufficient Uses
```
License with 2 uses
Required Uses: 5
→ Rejected (usage_limit too low)
```

### Scenario 3: Missing Permissions
```
License without commercial rights
Commercial Required: ✓
→ Rejected (permission not allowed)
```

## Timeline

- **Introduction**: 30 seconds
- **Resource Discovery**: 1 minute
- **Agent Configuration**: 1 minute
- **Agent Decision**: 1 minute (30 seconds × 2 tries)
- **Payment Flow**: 2 minutes (initiate + verify + access)
- **Verification**: 1 minute
- **Total**: 6-7 minutes (fits in 10 minute slot with buffer)

## Technical Notes

- Backend: FastAPI on `localhost:8000`
- Frontend: React/Vite on `localhost:3000`
- Database: SQLite (auto-initialized)
- API Docs: `http://localhost:8000/docs`
- Demo Database: Auto-populated with demo resources and license options
- All transactions in demo mode use DEMO_* prefix for clarity

## Troubleshooting During Demo

| Issue | Fix |
|-------|-----|
| Backend not running | Start: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Frontend not loading | Start: `npm run dev` in frontend dir |
| Database error | Delete `agentlicense.db` and restart backend |
| CORS error | Check CORS_ORIGINS in .env |
| Port in use | Change port in vite.config.js or .env |

---

**Demo Checklist:**
- [ ] Backend running on :8000
- [ ] Frontend running on :3000
- [ ] Browser at http://localhost:3000
- [ ] All demo resources loaded
- [ ] Database initialized
- [ ] First agent decision ready (budget $0.10)

**Go time! You're ready to impress.** ⚡