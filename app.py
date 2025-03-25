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

# Initialize session state for API keys
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {}

if 'selected_account' not in st.session_state:
    st.session_state.selected_account = None

# Sidebar for account management
st.sidebar.title("Account Management")

# Add new API key
with st.sidebar.form("add_account_form"):
    new_account_name = st.text_input("Account Name")
    new_api_key = st.text_input("API Key", type="password")
    submit_button = st.form_submit_button("Add Account")
    if submit_button:
        if new_account_name and new_api_key:
            st.session_state.api_keys[new_account_name] = new_api_key
            st.success(f"Added account: {new_account_name}")
        else:
            st.error("Please enter both account name and API key")

# Select account to display
if st.session_state.api_keys:
    selected_account = st.sidebar.selectbox(
        "Select Account",
        options=list(st.session_state.api_keys.keys()),
        key="account_selector"
    )
    st.session_state.selected_account = selected_account
    current_api_key = st.session_state.api_keys[selected_account]

    # Main app layout
    st.title(f"Wallet Balances - {st.session_state.selected_account}")

    # Setup GraphQL client with proper headers
    transport = RequestsHTTPTransport(
        url=BLINK_API_URL,
        headers={
            'X-API-KEY': current_api_key,
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

    def format_usd_balance(cents):
        """Convert cents to USD with proper formatting"""
        usd_value = cents / 100  # Convert cents to dollars
        return f"${usd_value:.2f}"  # Display with 2 decimal places and dollar sign

    def fetch_balance():
        """Fetch wallet balance from Blink API"""
        try:
            st.sidebar.info("Fetching balance from Blink API...")
            result = client.execute(balance_query)
            st.sidebar.success("Successfully fetched balance")

            # Get all wallets from the default account
            wallets = result['me']['defaultAccount']['wallets']

            # Find the BTC and USD wallets
            btc_wallet = next((wallet for wallet in wallets if wallet['walletCurrency'] == 'BTC'), None)
            usd_wallet = next((wallet for wallet in wallets if wallet['walletCurrency'] == 'USD'), None)

            return {
                'btc': btc_wallet['balance'] if btc_wallet else None,
                'usd': usd_wallet['balance'] if usd_wallet else None
            }

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

    # Add API status indicator
    st.sidebar.markdown("### API Status")
    api_status = st.sidebar.empty()

    # Create placeholders for the balances
    btc_balance_placeholder = st.empty()
    usd_balance_placeholder = st.empty()

    # Main loop for automatic refresh
    while True:
        try:
            balances = fetch_balance()

            if balances is not None:
                api_status.success("Connected to Blink API")

                # Display BTC balance
                btc_balance_placeholder.metric(
                    label="BTC Balance",
                    value=f"{format_btc_balance(balances['btc'])} BTC",
                    help="Balance shown in BTC (fetched in satoshis)"
                )

                # Display USD balance
                usd_balance_placeholder.metric(
                    label="USD Balance",
                    value=format_usd_balance(balances['usd']),
                    help="Balance shown in USD (fetched in cents)"
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
else:
    st.title("Wallet Balance Monitor")
    st.info("👈 Please add an account in the sidebar to start monitoring wallet balances.")