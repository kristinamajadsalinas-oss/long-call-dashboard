"""
Long Call Update Dashboard - Streamlit Version
Displays long call updates from Firebase Firestore in real-time
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import time
import hashlib

# Page configuration
st.set_page_config(
    page_title="Long Call Updates Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Password protection
def check_password():
    """Simple password protection for free deployment"""

    # Store password as SHA256 hash (change "trendmicro2026" to your desired password)
    # To generate: hashlib.sha256("your_password".encode()).hexdigest()
    CORRECT_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # "admin"

    # Initialize session state
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If already authenticated, skip
    if st.session_state["password_correct"]:
        return True

    # Show login form
    st.markdown('<div class="main-header">🔐 Long Call Updates Dashboard</div>', unsafe_allow_html=True)
    st.markdown("### Please enter password to access")

    password = st.text_input("Password", type="password", key="password_input")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Login", use_container_width=True):
            # Hash the entered password
            entered_hash = hashlib.sha256(password.encode()).hexdigest()

            if entered_hash == CORRECT_PASSWORD_HASH:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")
                return False

    st.markdown("---")
    st.info("💡 Default password: **admin** (change this in streamlit_dashboard.py)")

    return False

# Custom CSS for TrendLife branding
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #D71921;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #F8F9FA;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #D71921;
    }
    .active-call {
        background: #FFF5F5;
        border: 2px solid #D71921;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .stButton>button {
        background-color: #D71921;
        color: white;
    }
    .footer {
        text-align: center;
        color: #6C757D;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #E9ECEF;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
@st.cache_resource
def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize with secrets from Streamlit Cloud
        if "gcp_service_account" in st.secrets:
            # Use Streamlit secrets
            cred = credentials.Certificate(dict(st.secrets["gcp_service_account"]))
        else:
            # Fallback to application default (for local testing)
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred, {
            'projectId': 'long-call-update-dashboa-233b5',
        })

    return firestore.client()

# Get data from Firestore
def get_updates(db, squad_filter=None, date_filter=None):
    """Fetch long call updates from Firestore"""
    try:
        # Query Firestore
        updates_ref = db.collection('updates')
        query = updates_ref.order_by('timestamp', direction=firestore.Query.DESCENDING)

        # Get documents
        docs = query.stream()

        # Convert to list of dictionaries
        updates = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            updates.append(data)

        # Convert to DataFrame
        if updates:
            df = pd.DataFrame(updates)

            # Convert timestamp to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)

                      # Apply filters
            if squad_filter and squad_filter != "All":
                df = df[df['squad'] == squad_filter]

            if date_filter and date_filter != "All Time":
                # Make datetime timezone-aware to match pandas datetime64
                from datetime import timezone
                today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

                if date_filter == "Today":
                    df = df[df['timestamp'] >= today]
                elif date_filter == "Yesterday":
                    yesterday = today - timedelta(days=1)
                    df = df[(df['timestamp'] >= yesterday) & (df['timestamp'] < today)]
                elif date_filter == "Last 7 Days":
                    week_ago = today - timedelta(days=7)
                    df = df[df['timestamp'] >= week_ago]
                elif date_filter == "Last 30 Days":
                    month_ago = today - timedelta(days=30)
                    df = df[df['timestamp'] >= month_ago]

            return df

        return pd.DataFrame()

    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

# Main app
def main():
    # Check password first
    if not check_password():
        return  # Stop here if not authenticated

    # Initialize Firebase
    db = init_firebase()

    # Header
    st.markdown('<div class="main-header">📊 Long Call Updates Dashboard</div>', unsafe_allow_html=True)
    st.markdown("Real-time monitoring for extended customer calls")

    # Sidebar filters
    st.sidebar.title("🔍 Filters")

    squad_filter = st.sidebar.selectbox(
        "Squad",
        ["All", "Judith", "Maria", "Tech Support", "Premium Support"]
    )

    date_filter = st.sidebar.selectbox(
        "Date Range",
        ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"]
    )

    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 5 seconds)", value=True)

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

    # Get data
    df = get_updates(db, squad_filter, date_filter)

    # Display metrics
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Updates", len(df))

        with col2:
            unique_engineers = df['engineer'].nunique() if 'engineer' in df.columns else 0
            st.metric("Engineers", unique_engineers)

        with col3:
            # Count how many calls might still be active (within last hour)
            from datetime import timezone
now_utc = datetime.now(timezone.utc)
one_hour_ago = now_utc - timedelta(hours=1)
recent = df[df['timestamp'] > one_hour_ago] if 'timestamp' in df.columns else df
st.metric("Recent (1hr)", len(recent))

        with col4:
            # Average call duration (if available)
            st.metric("Entries", len(df))

    st.markdown("---")

    # Active/Recent Calls Section
    st.subheader("🟢 Recent Updates")

    if not df.empty:
        # Display recent updates as cards
        for idx, row in df.head(10).iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    # Format timestamp
                    time_str = row['timestamp'].strftime('%I:%M %p') if 'timestamp' in row else 'N/A'

                    st.markdown(f"""
                    <div class="active-call">
                        <strong>🔴 {row.get('engineer', 'Unknown')}</strong> •
                        {time_str} •
                        TID: <code>{row.get('transactionId', 'N/A')}</code> •
                        {row.get('skillset', 'N/A')}
                        <br>
                        <strong>Issue:</strong> {row.get('issue', 'N/A')}
                        <br>
                        <strong>Reason:</strong> {row.get('reason', 'N/A')}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.text(f"Squad: {row.get('squad', 'Unknown')}")
                    if 'callDuration' in row:
                        st.text(f"Duration: {row.get('callDuration', 'N/A')}")
    else:
        st.info("No updates found. Waiting for data...")

    st.markdown("---")

    # Full Data Table
    st.subheader("📋 All Updates")

    if not df.empty:
        # Select columns to display
        display_cols = ['timestamp', 'engineer', 'transactionId', 'squad', 'skillset', 'issue']
        available_cols = [col for col in display_cols if col in df.columns]

        # Format timestamp for display
        display_df = df[available_cols].copy()
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %I:%M %p')

        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"long_call_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to display")

    # Footer
    st.markdown("""
    <div class="footer">
        <strong>TrendLife</strong> | Where intelligence meets care
        <br>
        <small>Long Call Update Dashboard v1.0</small>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
