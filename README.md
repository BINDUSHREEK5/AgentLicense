# AgentLicense

**Machine-Readable Rights for Autonomous Commerce**

AgentLicense is a complete, production-ready system that enables autonomous AI agents to discover, evaluate, purchase, and use digital resources under machine-readable license agreements. The system implements HTTP 402 Payment Required protocol, x402 payment flow, Algorand blockchain integration, and automated license enforcement.

## 🎯 Problem Statement

Autonomous agents need to purchase and use digital resources (datasets, models, APIs) but lack:
- Machine-readable license discovery
- Automated license evaluation based on requirements
- Secure payment mechanisms
- On-chain license verification
- Usage tracking and enforcement

AgentLicense solves this by creating a complete machine-to-machine licensing marketplace.

## ✨ Key Features

### 1. **Agent Decision Engine**
- Autonomous license evaluation based on task requirements
- Budget-aware license selection
- Permission compatibility checking
- Deterministic, explainable decisions

### 2. **HTTP 402 Payment Required**
- Protected resource endpoints return HTTP 402 when no valid license present
- Communicates payment requirement to clients
- x402 payment protocol integration

### 3. **x402 Payment Flow**
- Complete x402 payment protocol implementation
- Payment initiation and verification
- Support for USDC stablecoin on Algorand

### 4. **Algorand Integration**
- License settlement on Algorand blockchain
- Transaction verification and provenance
- Demo mode and testnet support

### 5. **License Enforcement**
- Machine-readable license terms
- Usage limit tracking and enforcement
- Expiry validation
- Permission checking (commercial, training, redistribution)

### 6. **Professional Dashboard**
- Real-time license status monitoring
- Payment workflow visualization
- Agent decision transparency
- Resource marketplace

## 📋 Architecture

```
┌─────────────────────┐
│   AI Agent          │
├─────────────────────┤
│ - Task input        │
│ - Budget            │
│ - Requirements      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ License Discovery   │
│ & Decision Engine   │
├─────────────────────┤
│ - GET /licenses     │
│ - POST /select      │
│ - Evaluate options  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Protected Resource  │
├─────────────────────┤
│ GET /resources/{id} │
│ /access             │
│ → 402 Payment Req   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ x402 Payment Flow   │
├─────────────────────┤
│ POST /payments/     │
│ initiate            │
│ → Payment protocol  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Payment Verify      │
├─────────────────────┤
│ POST /payments/     │
│ verify              │
│ → Confirm xaction   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Algorand Settlement │
├─────────────────────┤
│ - Record on chain   │
│ - License provenance│
│ - TX verification   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ License Issued      │
├─────────────────────┤
│ - Hash verification │
│ - Status active     │
│ - Uses tracked      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Resource Access     │
├─────────────────────┤
│ GET /resources/     │
│ {id}/access         │
│ + license header    │
│ → 200 OK + data     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Usage Enforcement   │
├─────────────────────┤
│ - Decrement uses    │
│ - Verify expiry     │
│ - Check perms       │
│ - Track in DB       │
└─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- git

### Installation (Windows/Mac/Linux)

#### 1. Clone and Navigate
```bash
cd agentlicense
```

#### 2. Set Up Backend

**Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux  
source venv/bin/activate
```

**Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

**Create .env file:**
```bash
cp .env.example .env
```

Edit `.env`:
```
APP_ENV=development
DEBUG=true
DEMO_MODE=true
DATABASE_URL=sqlite:///./agentlicense.db
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Run database initialization:**
```bash
python -c "from app.db.database import init_db; init_db()"
```

**Start backend:**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will be available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

#### 3. Set Up Frontend

**In a new terminal:**
```bash
cd frontend

# Create .env file
copy .env.example .env  # Windows
cp .env.example .env    # Mac/Linux

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## 📚 Complete End-to-End Workflow

### Step 1: Access Dashboard
```
Open http://localhost:3000
→ See system status
→ Verify database and Algorand connection
```

### Step 2: Configure Agent Task
```
✓ Enter task: "Analyze dataset for commercial research"
✓ Set budget: $0.10
✓ Required uses: 5
✓ Commercial use required: ✓
```

### Step 3: Select Resource
```
✓ Choose resource: "Market Research Dataset"
→ View available license options
```

### Step 4: Agent Decision
```
✓ Click "Run Agent Decision"
→ Agent evaluates licenses:
  • Single Use $0.01 → REJECT (no commercial)
  • 10-Use $0.05 → REJECT (no commercial)
  • Commercial $0.20 → REJECT (exceeds budget)
→ Decision: NO COMPATIBLE LICENSES
```

### Step 5: Try with Adjusted Budget
```
✓ Increase budget to $0.25
✓ Run Agent Decision again
→ Agent selects "Commercial License" ($0.20)
→ Reason: "Meets all requirements within budget"
```

### Step 6: Payment Initiation
```
✓ Click "Proceed to Payment"
→ Payment initiated
→ Payment ID received
```

### Step 7: Simulate x402 Payment
```
✓ Click "Simulate Demo Payment"
→ Demo transaction ID generated (DEMO_...)
→ Payment submitted
```

### Step 8: Verify Payment
```
✓ Click "Verify Payment (x402)"
→ Payment verified via x402 protocol
→ Algorand settlement recorded (demo)
→ License issued
```

### Step 9: Access Protected Resource
```
✓ Automatic redirection to resource access
→ HTTP GET /resources/{resource_id}/access
→ License header included: x-license-id: {license_id}
→ 200 OK + Resource data returned
→ Uses remaining: 9
```

### Step 10: Verify Usage Enforcement
```
✓ Try accessing again
→ Uses remaining: 8
→ After 10 accesses: Uses remaining: 0
→ Next access fails with 403 (exhausted)
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/test_backend.py -v

# Or run with coverage
python -m pytest tests/test_backend.py --cov=app
```

### Manual Testing

**Health Check:**
```bash
curl http://localhost:8000/health
```

**List Resources:**
```bash
curl http://localhost:8000/resources
```

**Get License Options:**
```bash
curl http://localhost:8000/resources/market-dataset-001/licenses
```

**Agent Decision:**
```bash
curl -X POST http://localhost:8000/licenses/market-dataset-001/select \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze dataset",
    "budget": 0.20,
    "required_uses": 5,
    "commercial_use_required": true
  }'
```

**Request Protected Resource (no license - returns 402):**
```bash
curl http://localhost:8000/resources/market-dataset-001/access
# Returns: HTTP 402 Payment Required
```

## 🔐 API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /` - API info

### Resources
- `GET /resources` - List all resources
- `GET /resources/{id}` - Get resource details
- `GET /resources/{id}/licenses` - List license options
- `GET /resources/{id}/preview` - Preview resource (no license required)
- `GET /resources/{id}/access` - Access protected resource (requires license)

### Licenses
- `GET /licenses` - List licenses (filter by buyer, resource, status)
- `GET /licenses/{id}` - Get license details
- `POST /licenses/{resource_id}/select` - Agent selects license
- `GET /licenses/{id}/verify` - Verify license validity
- `POST /licenses/{id}/consume` - Consume one usage

### Payments (x402)
- `POST /payments/initiate` - Initiate x402 payment
- `POST /payments/verify` - Verify payment transaction
- `GET /payments/status/{payment_id}` - Get payment status
- `POST /payments/create-license` - Create license after payment

## 💾 Database Schema

### Resources Table
```sql
CREATE TABLE resources (
  id VARCHAR PRIMARY KEY,
  name VARCHAR,
  description VARCHAR,
  provider VARCHAR,
  data TEXT,
  created_at DATETIME
);
```

### Licenses Table
```sql
CREATE TABLE licenses (
  id VARCHAR PRIMARY KEY,
  resource_id VARCHAR,
  buyer VARCHAR,
  seller VARCHAR,
  price FLOAT,
  currency VARCHAR,
  usage_limit INTEGER,
  uses_remaining INTEGER,
  commercial_use BOOLEAN,
  redistribution_allowed BOOLEAN,
  training_allowed BOOLEAN,
  expires_at DATETIME,
  status VARCHAR,
  payment_reference VARCHAR,
  algorand_tx_id VARCHAR,
  license_hash VARCHAR,
  created_at DATETIME
);
```

### Payments Table
```sql
CREATE TABLE payments (
  id VARCHAR PRIMARY KEY,
  license_id VARCHAR,
  amount FLOAT,
  currency VARCHAR,
  network VARCHAR,
  transaction_id VARCHAR,
  status VARCHAR,
  payment_method VARCHAR,
  created_at DATETIME,
  verified_at DATETIME
);
```

### License Usage Table
```sql
CREATE TABLE license_usage (
  id VARCHAR PRIMARY KEY,
  license_id VARCHAR,
  accessed_at DATETIME,
  access_method VARCHAR,
  client_address VARCHAR,
  success BOOLEAN
);
```

## 🔑 Environment Variables

### Backend (.env)
```
# Application
APP_ENV=development
DEBUG=true
DEMO_MODE=true

# Database
DATABASE_URL=sqlite:///./agentlicense.db

# Algorand
ALGORAND_NETWORK=testnet
ALGORAND_NODE_URL=https://testnet-algorand.api.purestake.io/ps2
ALGORAND_INDEXER_URL=https://testnet-algorand.api.purestake.io/idx2
ALGORAND_WALLET_ADDRESS=  # Optional for testnet
ALGORAND_PRIVATE_KEY=     # Optional for testnet
ALGORAND_ASSET_ID=0

# x402 Payment
X402_ENABLED=true
X402_FACILITATOR_URL=http://localhost:9090
X402_NETWORK=algorand-testnet
X402_ASSET_ID=

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_DEMO_MODE=true
```

## 🎭 Demo Mode vs Testnet Mode

### Demo Mode (Default)
- Algorand transactions are simulated
- No wallet or testnet funds required
- Transaction IDs start with `DEMO_`
- Perfect for development and demos
- Dashboard shows "DEMO MODE" badge

### Testnet Mode
- Real Algorand testnet connections (if configured)
- Requires `ALGORAND_WALLET_ADDRESS` and `ALGORAND_PRIVATE_KEY`
- Requires testnet USDC balance
- Dashboard shows "TESTNET" badge
- Real blockchain transactions recorded

**To enable testnet:**
1. Set `DEMO_MODE=false` in `.env`
2. Configure Algorand credentials
3. Restart backend
4. Dashboard will show testnet status

## 📊 Hackathon Requirements Coverage

✅ **HTTP 402 Payment Required** - Fully implemented at `GET /resources/{resource_id}/access`
✅ **x402 Payment Protocol** - Complete payment flow with verification
✅ **Algorand Integration** - Transaction recording and provenance
✅ **Machine Readable Licenses** - Pydantic models with JSON serialization
✅ **License Discovery** - `GET /resources/{id}/licenses` with multiple options
✅ **Agent Decision Engine** - Autonomous license selection with evaluation
✅ **License Verification** - Hash-based integrity checking
✅ **Usage Enforcement** - Tracked and enforced per-license
✅ **Resource Access** - Protected endpoint with license validation
✅ **Payment Verification** - Before license issuance
✅ **Professional Dashboard** - React frontend with complete workflow
✅ **Automated Tests** - pytest suite for backend
✅ **API Documentation** - FastAPI Swagger/OpenAPI at `/docs`
✅ **Security** - No hardcoded secrets, environment-based config
✅ **Demo Mode** - Safe testing without real credentials
✅ **README & Docs** - Complete documentation

## 🐛 Troubleshooting

### Backend fails to start
```
Error: Address already in use
Solution: Change port in .env or kill process on 8000
```

### Frontend can't connect to backend
```
Error: Failed to connect to http://localhost:8000
Solution: Ensure backend is running, check VITE_API_URL in frontend/.env
```

### Database errors
```
Error: Database is locked
Solution: Delete agentlicense.db and restart backend (reinitializes DB)
```

### License verification fails
```
Error: License not found
Solution: Ensure license was created after payment verification
```

## 📝 License Model Details

Every license includes:
- **license_id**: Unique identifier
- **resource_id**: Which resource it grants access to
- **buyer**: Agent/entity that purchased the license
- **seller**: Provider of the resource
- **price**: Cost in USDC
- **usage_limit**: Maximum uses allowed
- **uses_remaining**: Tracked and decremented
- **commercial_use**: Permission flag
- **redistribution_allowed**: Permission flag
- **training_allowed**: Permission flag
- **expires_at**: Expiration timestamp (optional)
- **status**: active/expired/exhausted/revoked
- **payment_reference**: Links to payment record
- **algorand_tx_id**: Blockchain transaction ID
- **license_hash**: SHA-256 hash for integrity

## 🔗 Agent Decision Logic

The agent evaluates licenses by:
1. **Checking usage limit** - Must meet required uses
2. **Verifying budget** - Price must be within budget
3. **Validating permissions** - Commercial/training/redistribution requirements
4. **Confirming duration** - Expiry window must be sufficient

**Selection strategy:** Choose cheapest compatible license (cost optimization)

**Rejection:** If no compatible license exists, decision fails with clear reasoning.

## 🚀 Production Deployment

For production use:

1. **Use PostgreSQL** - Change `DATABASE_URL` to PostgreSQL connection string
2. **Configure Algorand testnet** - Set `ALGORAND_WALLET_ADDRESS` and `ALGORAND_PRIVATE_KEY`
3. **Enable HTTPS** - Use reverse proxy (nginx/Apache)
4. **Set DEBUG=false** - Disable debug mode
5. **Configure proper CORS_ORIGINS** - Restrict to your domain
6. **Add authentication** - Implement agent authentication (JWT recommended)
7. **Set up monitoring** - Log payment failures, track license usage
8. **Database backups** - Regular backup strategy
9. **Rate limiting** - Add rate limiting for payment endpoints

## 📄 License

This project is provided as a hackathon MVP demonstrating machine-readable licensing, autonomous commerce, and blockchain integration.

## 🤝 Support

For issues or questions:
1. Check the docs/ folder for detailed guides
2. Review API documentation at `/docs`
3. Check logs for detailed error information
4. Test endpoints with curl or Postman

---

**AgentLicense v1.0.0** - Built for autonomous commerce