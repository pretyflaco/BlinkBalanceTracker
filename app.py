import streamlit as st
import time
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os

# Configure page
st.set_page_config(
    page_title="BTC Wallet Balance",
    page_icon="💰"
)

# API Configuration
BLINK_API_URL = "https://api.blink.sv/graphql"

# Get API key from environment variable or use the default key
api_key = os.getenv("BLINK_API_KEY")
if not api_key:
    st.error("API key not found. Please set the BLINK_API_KEY environment variable.")
    st.stop()

# Setup GraphQL client with proper headers
transport = RequestsHTTPTransport(
    url=BLINK_API_URL,
    headers={
        'X-API-KEY': api_key,
        'Content-Type': 'application/json',
    },
    verify=True,
    retries=3,
)

client = Client(
    transport=transport,
    fetch_schema_from_transport=True
)

# GraphQL query for wallet balance
balance_query = gql("""
    query Me {
        me {
            defaultAccount {
                wallets {
                    id
                    walletCurrency
                    balance
                }
            }
        }
    }
""")

def format_btc_balance(satoshis):
    """Convert satoshis to BTC with proper formatting"""
    btc_value = satoshis / 100000000  # Convert satoshis to BTC
    return f"{btc_value:.8f}"  # Display with 8 decimal places

def fetch_balance():
    """Fetch wallet balance from Blink API"""
    try:
        st.sidebar.info("Fetching balance from Blink API...")
        result = client.execute(balance_query)
        st.sidebar.success("Successfully fetched balance")

        # Get all wallets from the default account
        wallets = result['me']['defaultAccount']['wallets']

        # Find the BTC wallet
        btc_wallet = next((wallet for wallet in wallets if wallet['walletCurrency'] == 'BTC'), None)

        if btc_wallet:
            return btc_wallet['balance']
        else:
            st.error("BTC wallet not found in the account")
            return None

    except Exception as e:
        error_msg = str(e)
        st.sidebar.error(f"Error details: {error_msg}")
        if "401" in error_msg:
            st.error("Authentication failed. Please check your API key.")
        elif "404" in error_msg:
            st.error("Account not found. Please check your credentials.")
        elif "Network" in error_msg:
            st.error("Network error. Please check your internet connection.")
        else:
            st.error(f"Error fetching balance: {error_msg}")
        return None

# Main app layout
st.title("BTC Wallet Balance")

# Add API status indicator
st.sidebar.markdown("### API Status")
api_status = st.sidebar.empty()

# Create a placeholder for the balance
balance_placeholder = st.empty()

# Main loop for automatic refresh
while True:
    try:
        balance = fetch_balance()

        if balance is not None:
            api_status.success("Connected to Blink API")
            balance_placeholder.metric(
                label="Current Balance",
                value=f"{format_btc_balance(balance)} BTC",
                help="Balance shown in BTC (fetched in satoshis)"
            )
        else:
            api_status.error("Failed to connect to Blink API")

        # Wait for 2 minutes before next refresh
        time.sleep(120)
        st.rerun()
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        time.sleep(120)
        st.rerun()