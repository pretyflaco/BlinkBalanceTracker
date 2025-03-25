import streamlit as st
import time
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os
from datetime import datetime
import pandas as pd # Added pandas import

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
            # Reset form by triggering a rerun
            st.rerun()
        else:
            st.error("Please enter both account name and API key")

# Select account to display
if st.session_state.api_keys:
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        selected_account = st.selectbox(
            "Select Account",
            options=list(st.session_state.api_keys.keys()),
            key="account_selector"
        )
    with col2:
        if st.button("🗑️", key=f"remove_{selected_account}"):
            if selected_account in st.session_state.api_keys:
                del st.session_state.api_keys[selected_account]
                # Move success message outside the button column
                st.sidebar.success(f"Removed account: {selected_account}")
                st.rerun()

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

    # GraphQL query for recent transactions
    transactions_query = gql("""
        query Me {
            me {
                defaultAccount {
                    transactions(first: 50) {
                        edges {
                            node {
                                id
                                status
                                direction
                                memo
                                settlementAmount
                                settlementFee
                                settlementCurrency
                                createdAt
                            }
                        }
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

    def format_date(date_str):
        """Format date string to a readable format"""
        try:
            # Try parsing as ISO format string
            if isinstance(date_str, str):
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Handle timestamp
                date = datetime.fromtimestamp(date_str)

            return date.strftime("%b %d, %Y %I:%M %p")
        except Exception as e:
            # If date parsing fails, return original value
            return str(date_str)

    def format_amount(amount, currency):
        """Format amount based on currency"""
        if currency == 'BTC':
            value = amount / 100000000  # Convert satoshis to BTC
            return f"{value:.8f} BTC"
        elif currency == 'USD':
            value = amount / 100  # Convert cents to USD
            return f"${value:.2f}"
        return str(amount)

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

    def fetch_transactions():
        """Fetch recent transactions from Blink API"""
        try:
            result = client.execute(transactions_query)
            transactions = result['me']['defaultAccount']['transactions']['edges']
            return transactions
        except Exception as e:
            st.error(f"Error fetching transactions: {str(e)}")
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

                # Fetch and display transactions
                st.markdown("### Recent Transactions")
                transactions = fetch_transactions()

                if transactions and len(transactions) > 0:
                    # Create a list for all transactions
                    transactions_data = []
                    for tx in transactions:
                        transaction = tx['node']
                        direction = transaction['direction'].capitalize()
                        sign = '+' if direction == 'RECEIVE' else '-'
                        formatted_amount = format_amount(
                            transaction['settlementAmount'],
                            transaction['settlementCurrency']
                        )

                        # Parse the date correctly from createdAt
                        try:
                            if isinstance(transaction['createdAt'], int):
                                # Handle timestamp (seconds since epoch)
                                date = datetime.fromtimestamp(transaction['createdAt'])
                            else:
                                # Handle ISO format string
                                date = datetime.fromisoformat(transaction['createdAt'].replace('Z', '+00:00'))

                            month_year = date.strftime("%B %Y")  # e.g., "March 2024"
                            formatted_date = date.strftime("%b %d, %Y %I:%M %p")
                        except Exception as e:
                            # Fallback for any date parsing issues
                            st.error(f"Error parsing date: {str(e)}")
                            month_year = "Unknown Date"
                            formatted_date = str(transaction['createdAt'])

                        transactions_data.append({
                            "Month": month_year,
                            "Date": formatted_date,
                            "Type": direction,
                            "Amount": f"{sign}{formatted_amount}",
                            "Status": transaction['status'].capitalize(),
                            "Memo": transaction['memo'] or '-'
                        })

                    # Convert to DataFrame and sort by date
                    df = pd.DataFrame(transactions_data)

                    # Group transactions by month
                    months = df['Month'].unique()

                    for month in sorted(months, key=lambda x: datetime.strptime(x, "%B %Y") if x != "Unknown Date" else datetime.min, reverse=True):
                        # Create an expander for each month
                        with st.expander(f"📅 {month}"):
                            # Filter transactions for this month
                            month_df = df[df['Month'] == month].copy()
                            # Drop the Month column for display
                            month_df = month_df.drop('Month', axis=1)

                            # Display transactions for this month
                            st.dataframe(
                                month_df,
                                hide_index=True,
                                column_config={
                                    "Date": st.column_config.TextColumn("Date", width="medium"),
                                    "Type": st.column_config.TextColumn("Type", width="small"),
                                    "Amount": st.column_config.TextColumn("Amount", width="medium"),
                                    "Status": st.column_config.TextColumn("Status", width="small"),
                                    "Memo": st.column_config.TextColumn("Memo", width="large"),
                                }
                            )
                else:
                    st.info("No recent transactions found")

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