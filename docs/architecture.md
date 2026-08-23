# AgentLicense Architecture

## System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                      AgentLicense System                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Frontend Layer                                                │
│  ├── React Dashboard (http://localhost:3000)                   │
│  ├── Resource Marketplace View                                 │
│  ├── Agent Configuration UI                                    │
│  ├── Payment Status Tracking                                   │
│  └── License Verification View                                 │
│                                                                │
│  Backend Layer                                                 │
│  ├── FastAPI Application (http://localhost:8000)               │
│  ├── API Endpoints                                             │
│  │   ├── /resources - Resource discovery                       │
│  │   ├── /licenses - License management                        │
│  │   ├── /payments - Payment processing                        │
│  │   └── /health - System status                               │
│  └── Business Logic                                            │
│      ├── Agent Decision Engine                                 │
│      ├── License Service                                       │
│      ├── Payment Facilitator (x402)                            │
│      └── Algorand Integration                                  │
│                                                                │
│  Data Layer                                                    │
│  ├── SQLite Database (dev/demo)                                │
│  ├── PostgreSQL (production)                                   │
│  └── Algorand Blockchain (testnet/mainnet)                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend (React/Vite)

**Structure:**
```
frontend/
├── src/
│   ├── main.jsx           # React entry point
│   ├── App.jsx            # Main application component
│   ├── index.css          # Global styles
│   └── services/          # API clients (if split)
├── index.html             # HTML entry
├── vite.config.js         # Build config
├── package.json           # Dependencies
└── .env.example           # Config template
```

**Key Features:**
- Single-page application (SPA)
- Real-time state management with React hooks
- API communication via axios
- Responsive design with CSS Grid
- Demo mode and testnet indicators

**Views:**
1. **Dashboard** - System status and agent configuration
2. **Marketplace** - License options and selection
3. **Agent Decision** - Autonomous license evaluation
4. **Payment** - x402 payment flow
5. **Success** - Resource access confirmation

### Backend (FastAPI/Python)

**Project Structure:**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── config.py                  # Settings management
│   ├── models.py                  # Pydantic schemas
│   │
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py              # Health check
│   │   ├── resources.py           # Resource endpoints
│   │   ├── licenses.py            # License management
│   │   ├── payments.py            # Payment flow
│   │   └── protected.py           # Protected resource access
│   │
│   ├── agents/                    # Agent decision engine
│   │   ├── __init__.py
│   │   └── decision_engine.py     # License evaluation logic
│   │
│   ├── licensing/                 # License management
│   │   ├── __init__.py
│   │   └── license_service.py     # License CRUD and validation
│   │
│   ├── payments/                  # Payment processing
│   │   ├── __init__.py
│   │   └── x402.py                # x402 protocol implementation
│   │
│   ├── blockchain/                # Blockchain integration
│   │   ├── __init__.py
│   │   └── algorand.py            # Algorand client
│   │
│   ├── db/                        # Database layer
│   │   ├── __init__.py
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── database.py            # Session management
│   │
│   └── resources/                 # Resource management
│       └── resource_service.py
│
├── tests/
│   ├── __init__.py
│   └── test_backend.py            # Test suite
│
├── requirements.txt               # Python dependencies
├── .env.example                   # Configuration template
└── README.md
```

**Core Modules:**

#### 1. **main.py** - FastAPI Application
- Initializes FastAPI app
- Registers middleware (CORS, TrustedHost)
- Sets up startup/shutdown events
- Includes routers
- Global exception handling

#### 2. **config.py** - Settings Management
- Pydantic-based configuration
- Environment variable loading
- Database URL
- Algorand credentials
- x402 settings
- CORS origins

#### 3. **models.py** - Data Schemas
- Pydantic models for request/response validation
- Type safety and documentation
- JSON serialization

#### 4. **db/models.py** - Database Models
- SQLAlchemy ORM models
- Resource, License, Payment, LicenseUsage tables
- Relationships and indexes
- Enum types for status

#### 5. **licensing/license_service.py** - License Logic
- `create_license()` - Create new license
- `get_license()` - Retrieve license
- `validate_license()` - Check validity
- `consume_license_usage()` - Decrement uses
- `generate_license_hash()` - Create SHA-256 hash
- `verify_license_hash()` - Integrity check

#### 6. **agents/decision_engine.py** - Agent Logic
- `evaluate_license_compatibility()` - Check requirements
- `select_best_license()` - Choose optimal license
- `explain_license_selection()` - Provide reasoning
- Deterministic decision making
- Cost optimization strategy

#### 7. **payments/x402.py** - Payment Protocol
- `create_payment_requirement()` - Generate 402 header
- `initiate_payment()` - Start payment flow
- `verify_payment()` - Confirm transaction
- `settle_payment()` - Algorand recording
- x402 protocol compliance

#### 8. **blockchain/algorand.py** - Blockchain
- `record_payment_provenance()` - Record on-chain
- `verify_transaction()` - Check transaction status
- Demo mode simulation
- Testnet support

### Database Design

```sql
-- Resources
CREATE TABLE resources (
  id VARCHAR PRIMARY KEY,
  name VARCHAR NOT NULL,
  description VARCHAR NOT NULL,
  provider VARCHAR NOT NULL,
  data TEXT,                          -- JSON serialized data
  created_at DATETIME
);

-- Licenses (Machine-readable, immutable once created)
CREATE TABLE licenses (
  id VARCHAR PRIMARY KEY,
  resource_id VARCHAR NOT NULL,       -- FK: resources.id
  buyer VARCHAR NOT NULL,             -- Agent address
  seller VARCHAR NOT NULL,            -- Provider
  price FLOAT NOT NULL,
  currency VARCHAR DEFAULT 'USDC',
  usage_limit INTEGER NOT NULL,
  uses_remaining INTEGER NOT NULL,    -- Tracked usage
  commercial_use BOOLEAN,
  redistribution_allowed BOOLEAN,
  training_allowed BOOLEAN,
  expires_at DATETIME,
  status VARCHAR,                     -- active/expired/exhausted/revoked
  payment_reference VARCHAR,          -- FK: payments.id
  algorand_tx_id VARCHAR,            -- Blockchain transaction
  license_hash VARCHAR,              -- SHA-256 integrity
  created_at DATETIME
);
-- Indexes: buyer+status, resource+status, license_hash, algorand_tx_id

-- Payments (x402 flow)
CREATE TABLE payments (
  id VARCHAR PRIMARY KEY,
  license_id VARCHAR NOT NULL,       -- FK: licenses.id
  amount FLOAT NOT NULL,
  currency VARCHAR DEFAULT 'USDC',
  network VARCHAR NOT NULL,         -- algorand, ethereum, etc.
  transaction_id VARCHAR,           -- Blockchain TX
  status VARCHAR,                   -- pending/verified/failed/settled
  payment_method VARCHAR,           -- x402, direct, etc.
  payment_metadata TEXT,            -- JSON metadata
  created_at DATETIME,
  verified_at DATETIME
);
-- Indexes: license_id+status, transaction_id, status

-- License Usage (Audit trail)
CREATE TABLE license_usage (
  id VARCHAR PRIMARY KEY,
  license_id VARCHAR NOT NULL,      -- FK: licenses.id
  accessed_at DATETIME,
  access_method VARCHAR,            -- api, direct, etc.
  client_address VARCHAR,           -- Client IP
  success BOOLEAN
);
-- Indexes: license_id
```

## API Flow Diagrams

### License Discovery Flow
```
Client
  │
  ├─→ GET /resources
  │   └─→ List all resources
  │
  ├─→ GET /resources/{resource_id}
  │   └─→ Resource details
  │
  └─→ GET /resources/{resource_id}/licenses
      └─→ Available license options
```

### Agent Decision Flow
```
Agent
  │
  ├─→ POST /licenses/{resource_id}/select
  │   │
  │   └─→ Decision Engine:
  │       ├─ Evaluate compatibility
  │       ├─ Check budget
  │       ├─ Validate permissions
  │       └─ Select best option
  │
  └─← Agent Decision
      (selected_license_id, reason, confidence)
```

### Payment Flow (x402)
```
Client (with license ID)
  │
  ├─→ GET /resources/{resource_id}/access (no license)
  │   ←─ HTTP 402 Payment Required
  │       (payment method, facilitator URL, amount)
  │
  ├─→ POST /payments/initiate
  │   │
  │   └─→ Payment Facilitator:
  │       ├─ Create payment record
  │       ├─ Generate payment ID
  │       └─ Return payment instructions
  │
  ├─→ Client submits x402 payment with transaction ID
  │   │
  │   └─→ POST /payments/verify?payment_id=X&transaction_id=Y
  │       │
  │       └─→ Verification:
  │           ├─ Query Algorand
  │           ├─ Verify transaction
  │           ├─ Update payment status
  │           └─ Settle on blockchain
  │
  └─→ GET /resources/{resource_id}/access (with license header)
      ├─ Validate license
      ├─ Check permissions
      ├─ Decrement usage
      └─ Return 200 + resource data
```

## License Lifecycle

```
1. CREATE
   └─→ License created after payment verified
       └─ status: ACTIVE
       └─ uses_remaining: usage_limit
       └─ license_hash: SHA-256

2. ACTIVE (Normal Operation)
   ├─→ Each access:
   │   ├─ Validate license
   │   ├─ Check expires_at
   │   ├─ Check uses_remaining > 0
   │   ├─ Verify permissions
   │   ├─ Decrement uses_remaining
   │   └─ Record usage in audit trail
   │
   └─→ While uses_remaining > 0:
       └─ Access granted

3. EXHAUSTED
   └─→ When uses_remaining = 0
       └─ status: EXHAUSTED
       └─ Access denied (new license required)

4. EXPIRED
   └─→ When expires_at < now()
       └─ status: EXPIRED
       └─ Access denied (new license required)

5. REVOKED (Optional)
   └─→ Manual revocation
       └─ status: REVOKED
       └─ Access denied immediately
```

## x402 Payment Protocol Flow

```
Step 1: PAYMENT REQUIRED
┌─────────────────────┐
│ Protected Resource  │
│ GET /access         │
│ (No valid license)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ HTTP 402 Payment Required Response   │
├─────────────────────────────────────┤
│ Headers:                            │
│  x-payment-required: true           │
│  x-payment-method: x402             │
│  x-facilitator-url: URL             │
│                                     │
│ Body:                               │
│  payment_required: true             │
│  payment_method: "x402"             │
│  license_id: "new"                  │
│  amount: 0.01                       │
│  currency: "USDC"                   │
│  facilitator_url: URL               │
└─────────────────────────────────────┘

Step 2: INITIATE PAYMENT
┌────────────────────┐
│ POST /payments/    │
│ initiate           │
│ {                  │
│  license_id: "lic" │
│  amount: 0.01      │
│ }                  │
└─────────┬──────────┘
          │
          ▼
┌──────────────────────────────┐
│ Payment Response             │
│ {                            │
│  payment_id: "pay_xxx"       │
│  status: "initiated"         │
│  facilitator_url: URL        │
│ }                            │
└──────────────────────────────┘

Step 3: SUBMIT PAYMENT
┌────────────────────────────┐
│ x402 Facilitator           │
│ (External or local)        │
│ Submit:                    │
│  amount: 0.01 USDC        │
│  reference: payment_id     │
│  network: algorand-testnet │
└────────┬───────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Algorand Network         │
│ (Testnet or real)        │
│ Transaction submitted    │
│ Transaction ID: 12345... │
└──────────────────────────┘

Step 4: VERIFY PAYMENT
┌──────────────────────────────────────┐
│ POST /payments/verify                │
│ ?payment_id=pay_xxx                  │
│ &transaction_id=ALGO_TX_12345        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Verification Steps:          │
│ 1. Lookup payment record     │
│ 2. Query Algorand/indexer    │
│ 3. Verify transaction exists │
│ 4. Confirm amount matches    │
│ 5. Update payment status     │
│ 6. Update license status     │
│ 7. Record provenance         │
└──────────────────────────────┘

Step 5: ACCESS RESOURCE
┌─────────────────────────────────┐
│ GET /resources/{id}/access      │
│ Headers:                        │
│  x-license-id: lic_xxx          │
└──────────────┬──────────────────┘
               │
               ▼
┌───────────────────────────────────┐
│ Access Control:                   │
│ 1. Verify license exists          │
│ 2. Check status = active          │
│ 3. Validate expiry                │
│ 4. Check uses_remaining > 0       │
│ 5. Verify permissions             │
│ 6. Decrement uses_remaining       │
│ 7. Record usage audit             │
└───────────────────────────────────┘
               │
               ▼
┌──────────────────────┐
│ 200 OK + Resource    │
│ {                    │
│  resource_id: "..."  │
│  data: {...}         │
│  uses_remaining: 9   │
│ }                    │
└──────────────────────┘
```

## Algorand Integration

### Transaction Recording (Demo Mode)

```python
# In demo mode:
transaction_id = "DEMO_" + random_hex(32)

# Simulated record:
{
    "status": "simulated",
    "is_real": False,
    "network": "testnet",
    "transaction_id": "DEMO_xxxxxxxx",
    "license_id": "lic_xxx",
    "amount": 0.01,
    "currency": "USDC",
    "timestamp": "2026-08-19T...",
    "mode": "DEMO_MODE"
}
```

### Transaction Recording (Testnet Mode)

```
1. Construct Algorand transaction
   - Sender: ALGORAND_WALLET_ADDRESS
   - Receiver: License provider
   - Amount: USDC asset transfer
   - Note: Reference to payment_id

2. Sign with private key
   - Use ALGORAND_PRIVATE_KEY
   - Sign transaction bytes

3. Submit to Algorand
   - POST to ALGORAND_NODE_URL
   - Wait for confirmation (typically 5-10 seconds)

4. Record provenance
   - Store transaction ID in licenses.algorand_tx_id
   - Record in payments table
   - Create audit log entry

5. Verification
   - Query ALGORAND_INDEXER_URL
   - Verify transaction confirmed
   - Verify amount and receiver correct
   - Cache result
```

## Security Considerations

### Data Security
- ✅ No secrets in code (environment variables only)
- ✅ Database uses SQLite (file-based) - use PostgreSQL for production
- ✅ Passwords not stored (no auth in MVP)
- ✅ Input validation via Pydantic
- ✅ SQL injection prevention via ORM

### Payment Security
- ✅ Never trust client claims about payments
- ✅ Verify via blockchain query
- ✅ License issued only after verification
- ✅ Payment status persisted in database
- ✅ x402 protocol compliance

### API Security
- ✅ CORS configured (whitelist origins)
- ✅ TrustedHost middleware
- ✅ Request validation
- ✅ Error responses don't leak internals
- ✅ No debugging info in production

### License Security
- ✅ License hash integrity (SHA-256)
- ✅ Immutable license records
- ✅ Audit trail of usage
- ✅ No manual status overrides possible
- ✅ Permissions enforced server-side

## Performance Considerations

### Database Optimization
- Indexes on frequently queried fields
- Foreign key relationships
- Efficient queries with ORM
- Connection pooling (recommended for production)

### API Performance
- FastAPI async endpoints
- Caching of license options
- Minimal payload sizes
- Efficient JSON serialization

### Scaling Considerations
- Stateless API (can run multiple instances)
- Database becomes bottleneck (use PostgreSQL + connection pooling)
- Cache payment verifications (Redis recommended)
- Separate Algorand querying service for high volume

## Testing Strategy

### Unit Tests
- License service functions
- Agent decision logic
- Hash generation/verification
- Payment status transitions

### Integration Tests
- API endpoint responses
- Database operations
- Payment flow completeness
- Usage enforcement

### End-to-End Tests
- Complete workflow from resource discovery to resource access
- Multiple license options
- Payment verification
- Usage tracking

---

**Architecture Document v1.0**
AgentLicense - Machine-Readable Rights for Autonomous Commerce