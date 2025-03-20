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
BLINK_API_URL = "https://api.staging.blink.sv/graphql"
BLINK_API_KEY = os.getenv(
    "BLINK_API_KEY",
    "blink_OEXpNxtsd1UMLxVH47N2IAZeqlyWPKtjCv4Prx0MC58ebfToa9XybFmZlJ2ZjVtR"
)

# Setup GraphQL client
transport = RequestsHTTPTransport(
    url=BLINK_API_URL,
    headers={'Authorization': f'Bearer {BLINK_API_KEY}'}
)

client = Client(
    transport=transport,
    fetch_schema_from_transport=True
)

# GraphQL query for wallet balance
balance_query = gql("""
    query {
        me {
            wallet {
                balance
            }
        }
    }
""")

def fetch_balance():
    """Fetch wallet balance from Blink API"""
    try:
        result = client.execute(balance_query)
        return result['me']['wallet']['balance']
    except Exception as e:
        st.error(f"Error fetching balance: {str(e)}")
        return None

# Main app layout
st.title("BTC Wallet Balance")

# Create a placeholder for the balance
balance_placeholder = st.empty()

# Main loop for automatic refresh
while True:
    balance = fetch_balance()
    
    if balance is not None:
        balance_placeholder.metric(
            label="Current Balance",
            value=f"{balance} BTC"
        )
    
    # Wait for 2 minutes before next refresh
    time.sleep(120)
    st.rerun()
