
import { Buffer } from 'buffer'
window.Buffer = Buffer

import React, { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { x402Client } from '@x402/core/client'
import { wrapFetchWithPayment } from '@x402/fetch'
import { ExactAvmScheme } from '@x402/avm/exact/client'
import {
  CheckCircle,
  Eye,
  Lock,
  Shield,
  TrendingUp,
  Wallet,
  Zap,
  XCircle,
} from 'lucide-react'
import { useWallet } from '@txnlab/use-wallet-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true'

// IMPORTANT:
// This must match the network returned by your backend's x402 402 response.
const ALGORAND_NETWORK =  'algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI='

const errText = (e) =>
  e?.response?.data?.detail ||
  e?.response?.data?.error ||
  e?.message ||
  'Something went wrong'

const shortAddress = (a) =>
  a ? `${a.slice(0, 6)}...${a.slice(-6)}` : ''

function WalletPanel({ setError }) {
  const { wallets, activeAddress } = useWallet()
  const [busy, setBusy] = useState(false)

  const activeWallet = wallets?.find((w) => w.isActive)

  if (activeAddress) {
    return (
      <div
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'center',
          flexWrap: 'wrap',
          marginTop: 15,
        }}
      >
        <span
          className="badge"
          style={{ background: '#10b981' }}
        >
          <Wallet size={14} />
          Wallet connected
        </span>

        <span
          style={{
            fontSize: 12,
            color: '#cbd5e1',
            fontFamily: 'monospace',
          }}
        >
          {shortAddress(activeAddress)}
        </span>

        <button
          className="button button-secondary"
          style={{
            padding: '7px 12px',
            fontSize: 12,
          }}
          onClick={async () => {
            try {
              setError('')
              if (activeWallet) {
                await activeWallet.disconnect()
              }
            } catch (e) {
              setError(errText(e))
            }
          }}
        >
          Disconnect
        </button>
      </div>
    )
  }

  return (
    <div style={{ marginTop: 15 }}>
      <div
        style={{
          color: '#cbd5e1',
          fontSize: 13,
          marginBottom: 10,
        }}
      >
        Connect Pera or Defly before making a real payment.
      </div>

      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
        }}
      >
        {(wallets || []).map((wallet) => (
          <button
            key={wallet.id}
            className="button button-primary"
            disabled={busy}
            onClick={async () => {
              try {
                setBusy(true)
                setError('')
                await wallet.connect()
              } catch (e) {
                console.error('Wallet connection failed:', e)
                setError(errText(e))
              } finally {
                setBusy(false)
              }
            }}
          >
            <Wallet size={15} />
            {busy
              ? 'Connecting...'
              : `Connect ${wallet.metadata?.name || wallet.id}`}
          </button>
        ))}
      </div>
    </div>
  )
}

function App() {
  const { activeAddress, signTransactions } = useWallet()

  const [view, setView] = useState('dashboard')
  const [health, setHealth] = useState(null)
  const [resources, setResources] = useState([])
  const [licenses, setLicenses] = useState([])
  const [selectedResource, setSelectedResource] = useState(null)

  const [agentTask, setAgentTask] = useState('')
  const [budget, setBudget] = useState(0.1)
  const [requiredUses, setRequiredUses] = useState(5)
  const [commercialRequired, setCommercialRequired] = useState(false)

  const [agentDecision, setAgentDecision] = useState(null)
  const [decisionLoading, setDecisionLoading] = useState(false)

  const [selectedLicense, setSelectedLicense] = useState(null)
  const [licenseId, setLicenseId] = useState(null)

  const [paymentStatus, setPaymentStatus] = useState(null)
  const [transactionId, setTransactionId] = useState('')
  const [accessMessage, setAccessMessage] = useState('')
  const [usesRemaining, setUsesRemaining] = useState(null)

  const [loading, setLoading] = useState(true)
  const [paymentLoading, setPaymentLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    initializeApp()
  }, [])

  async function initializeApp() {
    try {
      setLoading(true)
      setError('')

      const [h, r] = await Promise.all([
        axios.get(`${API_URL}/health`),
        axios.get(`${API_URL}/resources`),
      ])

      setHealth(h.data)
      setResources(r.data || [])
    } catch (e) {
      console.error('Initialization failed:', e)
      setError(errText(e) || `Cannot connect to ${API_URL}`)
    } finally {
      setLoading(false)
    }
  }

  async function fetchLicenseOptions(resourceId) {
    try {
      setError('')

      const r = await axios.get(
        `${API_URL}/resources/${encodeURIComponent(resourceId)}/licenses`
      )

      setLicenses(r.data || [])
      setSelectedResource(resourceId)
      setSelectedLicense(null)
      setAgentDecision(null)
      setView('marketplace')
    } catch (e) {
      console.error('Failed to fetch licenses:', e)
      setError(errText(e) || 'Failed to fetch license options')
    }
  }

  async function runAgentDecision() {
    if (!selectedResource) {
      setError('Please select a resource first')
      return
    }

    try {
      setDecisionLoading(true)
      setError('')

      const payload = {
        task: agentTask || 'Default task',
        budget: Number(budget),
        required_uses: Number(requiredUses),
        commercial_use_required: Boolean(commercialRequired),
        redistribution_required: false,
        training_required: false,
        duration_days: null,
      }

      console.log(
        'AGENT REQUIREMENTS BEING SENT:',
        JSON.stringify(payload, null, 2)
      )

      const r = await axios.post(
        `${API_URL}/licenses/${encodeURIComponent(selectedResource)}/select`,
        payload
      )

      console.log('AGENT DECISION RESPONSE:', r.data)

      setAgentDecision(r.data)
      setView('decision')
    } catch (e) {
      console.error('AGENT DECISION ERROR:', e)

      const responseData = e.response?.data

      console.log(
        'BACKEND RESPONSE:',
        JSON.stringify(responseData, null, 2)
      )

      if (responseData?.detail) {
        if (typeof responseData.detail === 'string') {
          setError(responseData.detail)
        } else {
          setError(
            responseData.detail.message ||
              JSON.stringify(responseData.detail)
          )
        }
      } else {
        setError(
          e.message || 'Agent decision request failed.'
        )
      }
    } finally {
      setDecisionLoading(false)
    }
  }

  /*
   * ============================================================
   * x402 CLIENT
   * ============================================================
   *
   * The backend returns:
   *
   *   x402Version: 2
   *   scheme: exact
   *   network: algorand:SGO1GKSzyE7IEPIiTxCByw9x8FmnCE
   *
   * ExactAvmScheme handles:
   *
   *   1. Reading payment requirements
   *   2. Building Algorand transactions
   *   3. Asking the connected wallet to sign
   *   4. Returning the signed payment payload
   *
   * wrapFetchWithPayment handles:
   *
   *   1. Initial request
   *   2. HTTP 402
   *   3. Payment creation
   *   4. PAYMENT-SIGNATURE
   *   5. Retrying the original request
   *
   * DO NOT manually construct PAYMENT-SIGNATURE.
   */

  function makeX402Client() {
  if (!activeAddress) {
    throw new Error('Connect Pera or Defly before paying.')
  }

  if (!signTransactions) {
    throw new Error('Connected wallet cannot sign transactions.')
  }

  const signer = {
    address: activeAddress?.address || activeAddress,

    signTransactions: async (txns, indexesToSign) => {
      console.log('======================================');
      console.log('WALLET SIGNING REQUEST');
      console.log('Transaction count:', txns?.length);
      console.log('Indexes:', indexesToSign);
      console.log(
        'Transaction types:',
        txns?.map((x) => ({
          type: x?.constructor?.name,
          isUint8Array: x instanceof Uint8Array,
          length: x?.length,
        }))
      );
      console.log('Calling TxnLab signTransactions...');
      console.log("Active address:", activeAddress);
      console.log("Wallet signTransactions:",
      typeof signTransactions
    );

      try {
        console.log("========== TRANSACTIONS TO SIGN ==========")

        txns.forEach((txn, i) => {
          console.log(`TX ${i}:`, txn)
          console.log(
            `TX ${i} bytes:`,
            txn instanceof Uint8Array
              ? Array.from(txn)
              : txn
          )
        })

        console.log("Indexes to sign:", indexesToSign)
        console.log("==========================================")
        const signed = await signTransactions(txns, indexesToSign);
        console.log('======================================');
        console.log('WALLET SIGNING COMPLETE');
        console.log('Signed transaction count:', signed?.length);
        console.log('======================================');

        return signed;
      } catch (err) {
        console.error('======================================');
        console.error('WALLET SIGNING ERROR');
        console.error(err);
        console.error('======================================');
        throw err;
      }
    },
  };
  console.log(
  'DEBUG CLIENT NETWORK:',
  JSON.stringify(ALGORAND_NETWORK),
  'length:',
  ALGORAND_NETWORK.length
)

  const client = new x402Client(
  (_x402Version, accepts) => {
    console.log(
      '========== X402 ACCEPTS =========='
    )

    console.log(
      'RAW ACCEPTS:',
      JSON.stringify(accepts, null, 2)
    )

    const algorand = accepts.find(
      (x) =>
        x.scheme === 'exact' &&
        String(x.network).trim() ===
          String(ALGORAND_NETWORK).trim()
    )

    console.log(
      'MATCH:',
      algorand
    )

    if (!algorand) {
      throw new Error(
        `No matching Algorand requirement. ` +
        `Expected=${JSON.stringify(ALGORAND_NETWORK)} ` +
        `Received=${JSON.stringify(
          accepts.map(x => x.network)
        )}`
      )
    }

    return algorand
  }
)
    client.register(
      'algorand:*',
      new ExactAvmScheme(signer)
    )

  console.log('x402 client configured:', client)
  console.log('Algorand exact scheme configured:', ExactAvmScheme)

  return wrapFetchWithPayment(fetch, client)
}

  function tierFor(license) {
    if (license.commercial_use) {

      return 'commercial'
    }

    if (Number(license.usage_limit || 0) > 1) {
      return 'multi'
    }

    return 'single'
  }

  async function initiatePayment(licId) {
    if (!licId) {
      setError('No license selected')
      return
    }

    if (!selectedResource) {
      setError('No resource selected')
      return
    }

    const license = licenses.find(
      (x) => x.license_id === licId
    )

    if (!license) {
      setError(
        'Selected license could not be found'
      )
      return
    }

    /*
     * DEMO MODE
     */
    if (DEMO_MODE) {
      const tx =
        `DEMO_${Math.random()
          .toString(16)
          .slice(2, 10)
          .toUpperCase()}`

      setLicenseId(licId)
      setTransactionId(tx)
      setUsesRemaining(
        Number(license.usage_limit || 0)
      )
      setPaymentStatus('complete')
      setAccessMessage(
        'Demo payment completed. No blockchain transaction was submitted.'
      )
      setView('success')

      return
    }

    /*
     * REAL PAYMENT REQUIRES WALLET
     */
    if (!activeAddress) {
      setPaymentStatus('wallet-required')
      setView('payment')
      setError(
        'Connect your Algorand wallet first.'
      )
      return
    }

    if (!signTransactions) {
      setPaymentStatus('error')
      setView('payment')
      setError(
        'Connected wallet cannot sign transactions.'
      )
      return
    }

    try {
      setPaymentLoading(true)
      setPaymentStatus('initiating')
      setError('')
      setLicenseId(null)
      setTransactionId('')
      setUsesRemaining(null)
      setAccessMessage('')
      setView('payment')

      const tier = tierFor(license)

      const url =
        `${API_URL}/x402/purchase/${tier}` +
        `?resource_id=${encodeURIComponent(
          selectedResource
        )}`

      console.log('======================================')
      console.log('STARTING x402 PAYMENT')
      console.log('URL:', url)
      console.log('Resource:', selectedResource)
      console.log('License:', license)
      console.log('Tier:', tier)
      console.log('Wallet:', activeAddress)
      console.log('Network:', ALGORAND_NETWORK)
      console.log('======================================')

      const fetchWithPayment =
        makeX402Client()

      /*
       * DO NOT manually handle HTTP 402 here.
       *
       * wrapFetchWithPayment does:
       *
       *   POST
       *    ↓
       *   402
       *    ↓
       *   parse payment-required
       *    ↓
       *   ExactAvmScheme
       *    ↓
       *   wallet signs
       *    ↓
       *   PAYMENT-SIGNATURE
       *    ↓
       *   retry POST
       *    ↓
       *   backend verifies/settles
       */
      const response =
        await fetchWithPayment(
          url,
          {
            method: 'POST',
            headers: {
              Accept: 'application/json',
            },
          }
        )

      console.log(
        'FINAL x402 RESPONSE:',
        response.status,
        response.statusText
      )

      const text =
        await response.text()

      console.log(
        'FINAL x402 BODY:',
        text
      )

      let data = {}

      try {
        data = text
          ? JSON.parse(text)
          : {}
      } catch {
        data = {
          raw: text,
        }
      }

      if (!response.ok) {
        throw new Error(
          `x402 payment failed (${response.status}): ${
            data?.detail ||
            data?.error ||
            data?.details ||
            response.statusText
          }`
        )
      }

      /*
       * Backend should create the license only after
       * facilitator settlement.
       */
      const realLicenseId =
        data.license_id || licId

      const realTx =
        data.algorand_tx_id ||
        data.transaction_id ||
        data.tx_id ||
        ''

      setLicenseId(realLicenseId)
      setTransactionId(realTx)

      setUsesRemaining(
        data.uses_remaining ?? null
      )

      setPaymentStatus('verified')

      setAccessMessage(
        realTx
          ? 'Payment settled on Algorand and the license was issued.'
          : 'Payment settled and the license was issued.'
      )

      setView('payment')
    } catch (e) {
      console.error(
        '======================================'
      )
      console.error(
        'x402 PAYMENT FAILED'
      )
      console.error(e)
      console.error(
        '======================================'
      )

      setPaymentStatus('error')
      setError(
        errText(e) ||
          'x402 payment failed'
      )
      setView('payment')
    } finally {
      setPaymentLoading(false)
    }
  }

  async function accessResource() {
    if (!licenseId) {
      setError(
        'No license available. Complete payment first.'
      )
      return
    }

    if (!selectedResource) {
      setError('No resource selected.')
      return
    }

    try {
      setError('')

      const r = await axios.get(
        `${API_URL}/resources/${encodeURIComponent(
          selectedResource
        )}/access`,
        {
          headers: {
            'x-license-id': licenseId,
          },
        }
      )

      setAccessMessage(
        `Resource accessed successfully. ${
          r.data.message || ''
        }`
      )

      setUsesRemaining(
        r.data.uses_remaining ?? null
      )

      setPaymentStatus('complete')
      setView('success')
    } catch (e) {
      console.error(e)

      if (e.response?.status === 402) {
        setPaymentStatus(
          'payment-required'
        )
        setView('payment')
        setError(
          'License required. Complete the x402 purchase.'
        )
      } else {
        setError(
          errText(e) ||
            'Failed to access resource'
        )
      }
    }
  }

  const workflow = useMemo(
    () => [
      !!selectedResource,
      !!agentDecision,
      [
        'initiating',
        'wallet-required',
        'verified',
        'complete',
      ].includes(paymentStatus),
      ['verified', 'complete'].includes(
        paymentStatus
      ),
      paymentStatus === 'complete',
    ],
    [
      selectedResource,
      agentDecision,
      paymentStatus,
    ]
  )

  if (loading) {
    return (
      <div
        className="container"
        style={{
          textAlign: 'center',
          paddingTop: 60,
        }}
      >
        <div
          className="loading"
          style={{
            margin: '0 auto 20px',
          }}
        />

        <p>
          Loading AgentLicense...
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="header">
        <div className="header-content">
          <h1>
            ⚡ AgentLicense
          </h1>

          <p>
            Machine-Readable Rights for
            Autonomous Commerce
          </p>

          {health && (
            <div
              style={{
                marginTop: 10,
              }}
            >
              <span
                className={`badge ${
                  health.demo_mode
                    ? 'demo'
                    : 'testnet'
                }`}
              >
                {health.demo_mode
                  ? '🎯 DEMO MODE'
                  : '🧪 TESTNET'}
              </span>

              <span
                className="badge"
                style={{
                  background:
                    health.database
                      ? '#10b981'
                      : '#ef4444',
                }}
              >
                {health.database
                  ? '✓ Database OK'
                  : '✗ Database Error'}
              </span>

              {health.algorand !== null &&
                health.algorand !==
                  undefined && (
                  <span
                    className="badge"
                    style={{
                      background:
                        health.algorand
                          ? '#3b82f6'
                          : '#f59e0b',
                    }}
                  >
                    {health.algorand
                      ? '✓ Algorand Connected'
                      : '⚠ Algorand Demo'}
                  </span>
                )}
            </div>
          )}

          <WalletPanel
            setError={setError}
          />
        </div>
      </div>

      <div className="container">
        {error && (
          <div
            className="alert error"
            style={{
              display: 'flex',
              gap: 8,
              alignItems: 'flex-start',
            }}
          >
            <XCircle size={17} />

            <span>
              <strong>Error:</strong>{' '}
              {error}
            </span>
          </div>
        )}

        <div
          style={{
            marginBottom: 30,
            display: 'flex',
            gap: 10,
            flexWrap: 'wrap',
          }}
        >
          <button
            className={`button ${
              view === 'dashboard'
                ? 'button-primary'
                : 'button-secondary'
            }`}
            onClick={() =>
              setView('dashboard')
            }
          >
            <Eye size={16} />
            Dashboard
          </button>

          <button
            className={`button ${
              view === 'marketplace'
                ? 'button-primary'
                : 'button-secondary'
            }`}
            onClick={() =>
              setView('marketplace')
            }
            disabled={!selectedResource}
          >
            <TrendingUp size={16} />
            Marketplace
          </button>

          <button
            className={`button ${
              view === 'decision'
                ? 'button-primary'
                : 'button-secondary'
            }`}
            onClick={() =>
              setView('decision')
            }
            disabled={!agentDecision}
          >
            <Zap size={16} />
            Agent Decision
          </button>

          <button
            className={`button ${
              view === 'payment'
                ? 'button-primary'
                : 'button-secondary'
            }`}
            onClick={() =>
              setView('payment')
            }
            disabled={!paymentStatus}
          >
            <Wallet size={16} />
            Payment
          </button>
        </div>

        {view === 'dashboard' && (
          <div className="main-grid">
            <div className="card">
              <div className="card-title">
                <Zap size={20} />
                Agent Task Configuration
              </div>

              <div className="form-group">
                <label>
                  Task Description
                </label>

                <textarea
                  value={agentTask}
                  onChange={(e) =>
                    setAgentTask(
                      e.target.value
                    )
                  }
                  placeholder="E.g., Analyze this dataset for commercial research"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>
                  Budget (USDC): $
                  {budget.toFixed(2)}
                </label>

                <input
                  type="range"
                  min="0.01"
                  max="1"
                  step="0.01"
                  value={budget}
                  onChange={(e) =>
                    setBudget(
                      Number(
                        e.target.value
                      )
                    )
                  }
                />
              </div>

              <div className="form-group">
                <label>
                  Required Uses:{' '}
                  {requiredUses}
                </label>

                <input
                  type="range"
                  min="1"
                  max="100"
                  value={requiredUses}
                  onChange={(e) =>
                    setRequiredUses(
                      Number(
                        e.target.value
                      )
                    )
                  }
                />
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={
                      commercialRequired
                    }
                    onChange={(e) =>
                      setCommercialRequired(
                        e.target.checked
                      )
                    }
                  />{' '}
                  Commercial Use Required
                </label>
              </div>
            </div>

            <div className="card">
              <div className="card-title">
                <Lock size={20} />
                Available Resources
              </div>

              {resources.length === 0 ? (
                <div
                  style={{
                    color: '#94a3b8',
                  }}
                >
                  No resources returned by
                  backend.
                </div>
              ) : (
                resources.map((r) => (
                  <div
                    key={r.id}
                    onClick={() =>
                      fetchLicenseOptions(
                        r.id
                      )
                    }
                    style={{
                      padding: 12,
                      border:
                        '1px solid #334155',
                      borderRadius: 6,
                      marginBottom: 10,
                      cursor: 'pointer',
                      background:
                        selectedResource ===
                        r.id
                          ? 'rgba(59,130,246,.1)'
                          : 'transparent',
                      borderColor:
                        selectedResource ===
                        r.id
                          ? '#3b82f6'
                          : '#334155',
                    }}
                  >
                    <div
                      style={{
                        fontWeight: 600,
                        color: '#60a5fa',
                      }}
                    >
                      {r.name}
                    </div>

                    <div
                      style={{
                        fontSize: 12,
                        color: '#94a3b8',
                        marginTop: 5,
                      }}
                    >
                      {r.description}
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="card">
              <div className="card-title">
                <Shield size={20} />
                Payment Workflow
              </div>

              {[
                'Select Resource',
                'Agent Decision',
                'Start x402 Payment',
                'Wallet Signs + Settlement',
                'Access Resource',
              ].map((label, i) => (
                <div
                  className="workflow-step"
                  key={label}
                >
                  <div
                    className={`workflow-step-icon ${
                      workflow[i]
                        ? 'completed'
                        : ''
                    }`}
                  >
                    {i + 1}
                  </div>

                  <span>{label}</span>
                </div>
              ))}

              <button
                className="button button-primary"
                onClick={
                  runAgentDecision
                }
                disabled={
                  decisionLoading ||
                  !selectedResource
                }
                style={{
                  marginTop: 15,
                  width: '100%',
                }}
              >
                {decisionLoading ? (
                  <span className="loading" />
                ) : (
                  <Zap size={16} />
                )}

                {decisionLoading
                  ? 'Analyzing...'
                  : 'Run Agent Decision'}
              </button>
            </div>
          </div>
        )}

        {view === 'marketplace' &&
          selectedResource && (
            <div className="card">
              <div className="card-title">
                <TrendingUp size={20} />
                License Options for{' '}
                {selectedResource}
              </div>

              <div
                className="card-content"
                style={{
                  marginBottom: 20,
                }}
              >
                Choose a license tier that
                matches your requirements.
              </div>

              <div className="license-options">
                {licenses.map((l) => (
                  <div
                    key={l.license_id}
                    className={`license-option ${
                      selectedLicense?.license_id ===
                      l.license_id
                        ? 'selected'
                        : ''
                    }`}
                    onClick={() =>
                      setSelectedLicense(l)
                    }
                  >
                    <div className="license-option-name">
                      {l.name}
                    </div>

                    <div className="license-option-price">
                      $
                      {Number(
                        l.price || 0
                      ).toFixed(2)}
                    </div>

                    <div className="license-option-details">
                      <div>
                        ✓ {l.usage_limit}{' '}
                        uses
                      </div>

                      <div>
                        ✓{' '}
                        {l.duration_days
                          ? `${l.duration_days} days`
                          : 'No expiry'}
                      </div>

                      {l.commercial_use && (
                        <span className="tag">
                          Commercial
                        </span>
                      )}

                      {l.training_allowed && (
                        <span className="tag">
                          Training
                        </span>
                      )}
                    </div>

                    <div
                      style={{
                        fontSize: 12,
                        color: '#94a3b8',
                        marginTop: 10,
                      }}
                    >
                      {l.description}
                    </div>
                  </div>
                ))}
              </div>

              <button
                className="button button-primary"
                onClick={() =>
                  selectedLicense &&
                  initiatePayment(
                    selectedLicense.license_id
                  )
                }
                disabled={
                  !selectedLicense ||
                  paymentLoading
                }
                style={{
                  marginTop: 20,
                  width: '100%',
                }}
              >
                <Wallet size={16} />

                {paymentLoading
                  ? 'Waiting for wallet...'
                  : DEMO_MODE
                  ? 'Purchase (Demo)'
                  : activeAddress
                  ? 'Pay with Connected Wallet'
                  : 'Connect Wallet to Pay'}
              </button>
            </div>
          )}

        {view === 'decision' &&
          agentDecision && (
            <div className="card">
              <div className="alert success">
                <CheckCircle size={16} />
                Agent Decision Made
              </div>

              <div
                className="card-title"
                style={{
                  marginTop: 20,
                }}
              >
                <Zap size={20} />
                Decision:{' '}
                {
                  agentDecision.selected_license_id
                }
              </div>

              <div
                className="card-content"
                style={{
                  marginBottom: 20,
                }}
              >
                <strong>
                  Reason:
                </strong>{' '}
                {agentDecision.reason}
              </div>

              <div
                style={{
                  fontSize: 13,
                  color: '#cbd5e1',
                }}
              >
                <strong>
                  Confidence:
                </strong>{' '}
                {typeof agentDecision.confidence ===
                'number'
                  ? `${(
                      agentDecision.confidence *
                      100
                    ).toFixed(0)}%`
                  : '—'}
              </div>

              <button
                className="button button-primary"
                disabled={paymentLoading}
                onClick={() => {
                  const l =
                    licenses.find(
                      (x) =>
                        x.license_id ===
                        agentDecision.selected_license_id
                    )

                  if (!l) {
                    setError(
                      'Agent-selected license was not found.'
                    )
                    return
                  }

                  setSelectedLicense(l)
                  initiatePayment(
                    l.license_id
                  )
                }}
                style={{
                  marginTop: 20,
                  width: '100%',
                }}
              >
                <Wallet size={16} />

                {paymentLoading
                  ? 'Waiting for wallet...'
                  : 'Proceed to Payment'}
              </button>
            </div>
          )}

        {view === 'payment' &&
          paymentStatus && (
            <div className="main-grid">
              <div className="card">
                <div className="card-title">
                  <Wallet size={20} />
                  x402 Payment Protocol
                </div>

                {paymentStatus ===
                  'wallet-required' && (
                  <div className="alert warning">
                    Connect Pera or Defly above,
                    then press the payment button
                    again.
                  </div>
                )}

                {paymentStatus ===
                  'initiating' && (
                  <>
                    <div className="alert info">
                      x402 returned HTTP 402.
                      Preparing the Algorand
                      payment and opening your
                      wallet for signing...
                    </div>

                    <div
                      style={{
                        marginTop: 15,
                        color: '#94a3b8',
                        fontSize: 13,
                        lineHeight: 1.7,
                      }}
                    >
                      1. Backend returns HTTP
                      402
                      <br />
                      2. x402 reads payment
                      requirements
                      <br />
                      3. Wallet signs the
                      Algorand transaction
                      <br />
                      4. x402 retries with
                      PAYMENT-SIGNATURE
                      <br />
                      5. Backend verifies and
                      settles through the
                      facilitator
                    </div>
                  </>
                )}

                {paymentStatus ===
                  'verified' && (
                  <>
                    <div className="alert success">
                      <CheckCircle size={16} />
                      Payment settled on
                      Algorand. License issued.
                    </div>

                    <button
                      className="button button-primary"
                      onClick={
                        accessResource
                      }
                      style={{
                        marginTop: 15,
                        width: '100%',
                      }}
                    >
                      <Lock size={16} />
                      Access Resource
                    </button>
                  </>
                )}

                {paymentStatus ===
                  'complete' && (
                  <div className="alert success">
                    <CheckCircle size={16} />
                    License issued. Resource
                    unlocked.
                  </div>
                )}

                {paymentStatus ===
                  'error' && (
                  <>
                    <div className="alert error">
                      <XCircle size={16} />
                      x402 payment failed.
                    </div>

                    {selectedLicense && (
                      <button
                        className="button button-primary"
                        onClick={() =>
                          initiatePayment(
                            selectedLicense.license_id
                          )
                        }
                        style={{
                          marginTop: 15,
                          width: '100%',
                        }}
                      >
                        <Wallet size={16} />
                        Try Payment Again
                      </button>
                    )}
                  </>
                )}

                {DEMO_MODE && (
                  <div
                    className="alert warning"
                    style={{
                      marginTop: 15,
                    }}
                  >
                    Demo mode is enabled. Set
                    VITE_DEMO_MODE=false for real
                    x402 payments.
                  </div>
                )}
              </div>

              <div className="card">
                <div className="card-title">
                  <Shield size={20} />
                  License Status
                </div>

                {licenseId ? (
                  <div
                    style={{
                      fontSize: 13,
                      color: '#cbd5e1',
                      lineHeight: 1.8,
                    }}
                  >
                    <div>
                      <strong>
                        License ID:
                      </strong>{' '}
                      {licenseId}
                    </div>

                    <div>
                      <strong>
                        Status:
                      </strong>{' '}
                      {paymentStatus}
                    </div>

                    {transactionId && (
                      <div>
                        <strong>
                          Algorand Tx:
                        </strong>{' '}
                        {transactionId.slice(
                          0,
                          18
                        )}
                        ...
                      </div>
                    )}

                    {usesRemaining !== null && (
                      <div>
                        <strong>
                          Uses Remaining:
                        </strong>{' '}
                        {usesRemaining}
                      </div>
                    )}
                  </div>
                ) : (
                  <div
                    style={{
                      color: '#94a3b8',
                      fontSize: 13,
                    }}
                  >
                    No license has been issued yet.
                  </div>
                )}
              </div>
            </div>
          )}

        {view === 'success' && (
          <div className="card">
            <div
              className="alert success"
              style={{
                marginBottom: 20,
              }}
            >
              <CheckCircle size={20} />
              <strong>Success!</strong>{' '}
              Resource accessed and license
              enforced.
            </div>

            <div
              style={{
                fontSize: 15,
                color: '#cbd5e1',
                lineHeight: 1.8,
              }}
            >
              <p>
                <strong>
                  Message:
                </strong>{' '}
                {accessMessage}
              </p>

              <p>
                <strong>
                  Uses Remaining:
                </strong>{' '}
                {usesRemaining ?? '—'}
              </p>

              <p
                style={{
                  marginTop: 20,
                  color: '#94a3b8',
                }}
              >
                ✓ Agent selected appropriate
                license
                <br />
                ✓ HTTP 402 Payment Required
                triggered
                <br />
                ✓ Wallet signed the x402
                payment
                <br />
                ✓ x402 facilitator settled the
                payment
                <br />
                ✓ License verified and issued
                <br />
                ✓ Usage tracked and enforced
              </p>
            </div>

            {transactionId &&
              !transactionId.startsWith(
                'DEMO_'
              ) && (
                <div
                  style={{
                    marginTop: 15,
                    padding: 12,
                    border:
                      '1px solid #334155',
                    borderRadius: 8,
                    fontFamily:
                      'monospace',
                    fontSize: 12,
                    wordBreak:
                      'break-all',
                    color: '#93c5fd',
                  }}
                >
                  Algorand transaction:{' '}
                  {transactionId}
                </div>
              )}

            <button
              className="button button-primary"
              onClick={
                accessResource
              }
              style={{
                marginTop: 20,
                width: '100%',
              }}
            >
              <Lock size={16} />
              Access Resource Again
            </button>
          </div>
        )}
      </div>

      <div className="footer">
        <p>
          AgentLicense v1.0.0 | Machine-Readable
          Rights for Autonomous Commerce
        </p>

        <p
          style={{
            marginTop: 10,
            color: '#475569',
          }}
        >
          {DEMO_MODE
            ? '🎯 Running in DEMO MODE - transactions are simulated'
            : '🧪 Running in TESTNET MODE - real x402 wallet payments enabled'}
        </p>
      </div>
    </div>
  )
}

export default App