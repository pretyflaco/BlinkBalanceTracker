# Bitcoin Wallet Balance Monitor

A Streamlit-powered dashboard that leverages the Blink API to track Bitcoin and USD wallet balances, along with comprehensive transaction history.

## Features

- 💰 Real-time wallet balance tracking for BTC and USD
- 📊 Complete transaction history with monthly grouping
- 🔄 Automatic refresh every 2 minutes
- 👥 Multi-account support
- 📱 Responsive design
- 🔒 Secure API key management

## Prerequisites

- Python 3.x
- Streamlit
- GQL (GraphQL client)
- Pandas
- Blink API key(s)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bitcoin-wallet-monitor
```

2. Install the required packages:
```bash
pip install streamlit gql requests-toolbelt pandas
```

## Configuration

1. Create a `.streamlit` directory and add `config.toml` with the following content:
```toml
[server]
headless = true
address = "0.0.0.0"
port = 5000
```

## Usage

1. Start the Streamlit application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Add your wallet account:
   - Click "Add Account" in the sidebar
   - Enter an account name
   - Enter your Blink API key
   - Click "Add Account"

4. View your wallet information:
   - Select an account from the dropdown menu
   - View real-time BTC and USD balances
   - Explore transaction history grouped by month

## Features Overview

### Balance Monitoring
- Real-time BTC balance in satoshis (converted to BTC)
- Real-time USD balance in cents (converted to USD)
- Automatic refresh every 2 minutes

### Transaction History
- Complete transaction history grouped by month
- Expandable monthly views
- Transaction details including:
  - Date and time
  - Transaction type (Send/Receive)
  - Amount with currency
  - Status
  - Memo/Description

### Account Management
- Add multiple accounts
- Switch between accounts
- Secure API key storage
- Easy account removal

## Development

The application is built with Streamlit and uses:
- GraphQL for API communication
- Pandas for data handling
- Streamlit's built-in components for UI

## Security Note

API keys are stored in session state and are not persisted between sessions. Always keep your API keys secure and never share them.
