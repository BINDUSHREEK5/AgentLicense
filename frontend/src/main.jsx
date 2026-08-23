
import React from 'react'
import ReactDOM from 'react-dom/client'
import {
  NetworkId,
  WalletManager,
  WalletProvider,
} from '@txnlab/use-wallet-react'

import { pera } from '@txnlab/use-wallet-pera'
import { defly } from '@txnlab/use-wallet-defly'

import App from './app'
import './index.css'

const walletManager = new WalletManager({
  wallets: [
    pera(),
    defly(),
  ],
  network: NetworkId.TESTNET,
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <WalletProvider manager={walletManager}>
      <App />
    </WalletProvider>
  </React.StrictMode>,
)
