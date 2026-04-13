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
        app = firebase_admin.get_app()
    except ValueError:
        # Initialize with secrets from Streamlit Cloud
        firebase_config = dict(st.secrets["gcp_service_account"])
        cred = credentials.Certificate(firebase_config)
        app = firebase_admin.initialize_app(cred)

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
        # Group updates by Transaction ID to show timeline
        if 'transactionId' in df.columns:
            grouped = df.groupby('transactionId')

            for tid, group_df in grouped:
                # Sort by timestamp (chronological order)
                group_df = group_df.sort_values('timestamp')

                # Get first (initial) update
                initial = group_df.iloc[0]
                latest = group_df.iloc[-1]

                # Determine if call is still active (latest update within last hour)
                is_active = False
                if 'timestamp' in latest:
                    from datetime import timezone
                    now_utc = datetime.now(timezone.utc)
                    time_diff = now_utc - latest['timestamp']
                    is_active = time_diff.total_seconds() < 3600  # Active if within last hour

                # Format header
                status_icon = "🟢" if is_active else "🔴"
                engineer = initial.get('engineer', 'Unknown')
                # Convert UTC to local time for display
                time_str = latest['timestamp'].tz_convert('Asia/Manila').strftime('%I:%M %p') if 'timestamp' in latest else 'N/A'
                duration = latest.get('callDuration', 'Unknown')

                header = f"{status_icon} {engineer} • TID: {tid} • Duration: {duration} • {len(group_df)} update(s)"

                # Use expander for timeline
                with st.expander(header, expanded=is_active):
                    # Show timeline of all updates
                    for idx, update_row in group_df.iterrows():
                        # Convert UTC to local time
                        update_time = update_row['timestamp'].tz_convert('Asia/Manila').strftime('%I:%M %p') if 'timestamp' in update_row else 'N/A'
                        update_type = update_row.get('updateType', 'initial')

                        # Styling based on update type
                        if update_type == 'initial':
                            st.markdown(f"**⏰ INITIAL UPDATE - {update_time}**")
                            st.write(f"**Issue:** {update_row.get('issue', 'N/A')}")
                            st.write(f"**Reason:** {update_row.get('reason', 'N/A')}")
                        else:
                            st.markdown(f"**⏰ PROGRESS UPDATE - {update_time}**")
                            st.write(f"**Update:** {update_row.get('updateText', 'N/A')}")

                        st.markdown("---")

                    # Show engineer info at bottom
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Squad:** {initial.get('squad', 'Unknown')}")
                    with col2:
                        st.write(f"**Skillset:** {initial.get('skillset', 'N/A')}")
        else:
            st.warning("No transactionId found in data")
    else:
        st.info("No updates found. Waiting for data...")

    st.markdown("---")

    # Full Data Table
    st.subheader("📋 All Updates")

    if not df.empty:
        # Select columns to display
        display_cols = ['timestamp', 'engineer', 'transactionId', 'squad', 'skillset', 'issue']
        available_cols = [col for col in display_cols if col in df.columns]

        # Format timestamp for display (convert to local time)
        display_df = df[available_cols].copy()
        if 'timestamp' in display_df.columns:
            # Convert UTC to local timezone (Asia/Manila = UTC+8)
            display_df['timestamp'] = display_df['timestamp'].dt.tz_convert('Asia/Manila').dt.strftime('%Y-%m-%d %I:%M %p')

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
