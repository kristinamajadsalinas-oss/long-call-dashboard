"""
Long Call Update Dashboard - 2-View Version
Engineer's View & Squad Lead's View
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib

# Page configuration
st.set_page_config(
    page_title="Long Call Updates Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Manila timezone
MANILA_TZ = pytz.timezone('Asia/Manila')

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #D71921;
        margin-bottom: 1rem;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .update-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .update-card-progress {
        border-left-color: #007bff;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6C757D;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Password protection
def check_password():
    """Simple password protection"""
    CORRECT_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # "admin"

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.markdown('<div class="main-header">🔐 Long Call Updates Dashboard</div>', unsafe_allow_html=True)
    st.markdown("### Please enter password to access")

    password = st.text_input("Password", type="password", key="password_input")

    if st.button("Login"):
        entered_hash = hashlib.sha256(password.encode()).hexdigest()
        if entered_hash == CORRECT_PASSWORD_HASH:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.info("💡 Default password: admin")
    return False

# Initialize Firebase
@st.cache_resource
def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["gcp_service_account"]))
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")
        return None

# Get updates from Firestore
@st.cache_data(ttl=5)
def get_updates():
    """Fetch all updates from Firebase"""
    try:
        db = init_firebase()
        if not db:
            return pd.DataFrame()

        updates_ref = db.collection('updates')
        docs = updates_ref.stream()

        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            data.append(doc_data)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Convert timestamps to Manila timezone
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['timestamp'] = df['timestamp'].dt.tz_convert(MANILA_TZ)

        # Sort by timestamp descending
        df = df.sort_values('timestamp', ascending=False)

        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Engineer's View
def engineer_view(df, engineer_name):
    """Dashboard view for engineers"""
    st.markdown('<div class="main-header">📱 My Long Call Updates</div>', unsafe_allow_html=True)
    st.markdown(f"**Engineer:** {engineer_name}")

    # Filter to this engineer's data only
    engineer_df = df[df['engineer'] == engineer_name] if 'engineer' in df.columns and not df.empty else pd.DataFrame()

    if engineer_df.empty:
        st.info("📋 No updates found. Your long call updates will appear here once submitted.")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_calls = engineer_df['transactionId'].nunique() if 'transactionId' in engineer_df.columns else 0
        st.metric("Total Calls", total_calls)

    with col2:
        today = datetime.now(MANILA_TZ).date()
        today_calls = len(engineer_df[engineer_df['timestamp'].dt.date == today]) if 'timestamp' in engineer_df.columns else 0
        st.metric("Today", today_calls)

    with col3:
        this_week = datetime.now(MANILA_TZ) - timedelta(days=7)
        week_calls = engineer_df[engineer_df['timestamp'] >= this_week]['transactionId'].nunique() if 'timestamp' in engineer_df.columns else 0
        st.metric("This Week", week_calls)

    st.markdown("---")

    # Active Calls
    st.subheader("🟢 Active Calls")
    active_tids = engineer_df.groupby('transactionId').filter(lambda x: True).groupby('transactionId').first()

    if not active_tids.empty:
        for tid, row in active_tids.iterrows():
            tid_updates = engineer_df[engineer_df['transactionId'] == tid].sort_values('timestamp')
            update_count = len(tid_updates)
            latest = tid_updates.iloc[-1]

            with st.expander(f"📞 TID: {tid} - {update_count} update(s)", expanded=False):
                for idx, update in tid_updates.iterrows():
                    update_type = update.get('updateType', 'initial')
                    time_str = update['timestamp'].strftime('%I:%M %p') if 'timestamp' in update else 'N/A'

                    if update_type == 'initial':
                        st.markdown(f"**⏰ {time_str} - INITIAL UPDATE**")
                        st.markdown(f"**Issue:** {update.get('issue', 'N/A')}")
                        st.markdown(f"**Reason:** {update.get('reason', 'N/A')}")
                    else:
                        st.markdown(f"**⏰ {time_str} - PROGRESS UPDATE**")
                        st.markdown(f"**Update:** {update.get('updateText', 'N/A')}")

                    st.markdown("---")
    else:
        st.info("No active calls currently")

    st.markdown("---")

    # History by Date
    st.subheader("📅 My History")

    if 'timestamp' in engineer_df.columns:
        dates = engineer_df['timestamp'].dt.date.unique()
        dates = sorted(dates, reverse=True)

        for date in dates[:7]:  # Last 7 days
            date_updates = engineer_df[engineer_df['timestamp'].dt.date == date]
            date_str = date.strftime('%B %d, %Y')

            with st.expander(f"📆 {date_str} - {len(date_updates)} update(s)"):
                for tid in date_updates['transactionId'].unique():
                    tid_updates = date_updates[date_updates['transactionId'] == tid]
                    st.markdown(f"**TID: {tid}** - {len(tid_updates)} update(s)")

                    for idx, update in tid_updates.iterrows():
                        time_str = update['timestamp'].strftime('%I:%M %p')
                        update_type = update.get('updateType', 'initial')

                        if update_type == 'initial':
                            st.caption(f"⏰ {time_str} - {update.get('issue', 'N/A')[:50]}...")
                        else:
                            st.caption(f"⏰ {time_str} - {update.get('updateText', 'N/A')[:50]}...")

# Squad Lead's View
def squad_lead_view(df):
    """Dashboard view for squad leads"""
    st.markdown('<div class="main-header">📊 Long Call Updates Dashboard</div>', unsafe_allow_html=True)

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")

    # Squad filter
    squad_options = ["All", "Chris", "Judith", "Josh", "Bea"]
    squad_filter = st.sidebar.selectbox("Squad", squad_options)

    # Engineer filter
    engineer_list = df['engineer'].unique().tolist() if 'engineer' in df.columns and not df.empty else []
    engineer_filter = st.sidebar.selectbox("Engineer", ["All"] + engineer_list)

    # Date range filter
    date_options = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"]
    date_filter = st.sidebar.selectbox("Date Range", date_options)

    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (every 5 seconds)", value=True)
    if st.sidebar.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

    # Apply filters
    filtered_df = df.copy()

    # Filter by squad
    if squad_filter != "All" and 'squad' in filtered_df.columns:
        # Handle both "Squad Judith" and "Judith" formats
        filtered_df = filtered_df[
            (filtered_df['squad'] == squad_filter) |
            (filtered_df['squad'] == f"Squad {squad_filter}")
        ]

    # Filter by engineer
    if engineer_filter != "All" and 'engineer' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['engineer'] == engineer_filter]

    # Filter by date
    if 'timestamp' in filtered_df.columns and not filtered_df.empty:
        now = datetime.now(MANILA_TZ)

        if date_filter == "Today":
            filtered_df = filtered_df[filtered_df['timestamp'].dt.date == now.date()]
        elif date_filter == "Yesterday":
            yesterday = (now - timedelta(days=1)).date()
            filtered_df = filtered_df[filtered_df['timestamp'].dt.date == yesterday]
        elif date_filter == "Last 7 Days":
            week_ago = now - timedelta(days=7)
            filtered_df = filtered_df[filtered_df['timestamp'] >= week_ago]
        elif date_filter == "Last 30 Days":
            month_ago = now - timedelta(days=30)
            filtered_df = filtered_df[filtered_df['timestamp'] >= month_ago]

    # METRICS
    col1, col2, col3 = st.columns(3)

    with col1:
        total = len(filtered_df)
        st.metric("📊 TOTAL", total)

    with col2:
        # Active = calls with updates in last hour
        if 'timestamp' in filtered_df.columns and not filtered_df.empty:
            one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)
            active = len(filtered_df[filtered_df['timestamp'] >= one_hour_ago])
        else:
            active = 0
        st.metric("🟢 ACTIVE", active)

    with col3:
        # Recent = unique calls in last hour
        if 'timestamp' in filtered_df.columns and not filtered_df.empty:
            one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)
            recent = filtered_df[filtered_df['timestamp'] >= one_hour_ago]['transactionId'].nunique() if 'transactionId' in filtered_df.columns else 0
        else:
            recent = 0
        st.metric("⏰ RECENT", recent)

    st.markdown("---")

    # RECENT ACTIVITIES
    st.subheader("📢 Recent Activities (Last Hour)")

    if 'timestamp' in filtered_df.columns and not filtered_df.empty:
        one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)
        recent_df = filtered_df[filtered_df['timestamp'] >= one_hour_ago].head(10)

        if not recent_df.empty:
            for idx, row in recent_df.iterrows():
                time_str = row['timestamp'].strftime('%I:%M %p')
                engineer = row.get('engineer', 'Unknown')
                tid = row.get('transactionId', 'N/A')
                squad = row.get('squad', 'Unknown')
                update_type = row.get('updateType', 'initial')

                if update_type == 'initial':
                    issue = row.get('issue', 'N/A')
                    st.markdown(f"""
                    <div class="update-card">
                        🟢 <strong>{time_str}</strong> - {engineer} ({squad})<br>
                        TID: {tid} - INITIAL: "{issue[:60]}..."
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    update_text = row.get('updateText', 'N/A')
                    st.markdown(f"""
                    <div class="update-card update-card-progress">
                        🔵 <strong>{time_str}</strong> - {engineer} ({squad})<br>
                        TID: {tid} - UPDATE: "{update_text[:60]}..."
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No recent activities in the last hour")
    else:
        st.info("No recent activities in the last hour")

    st.markdown("---")

    # BY ENGINEER
    st.subheader("👨‍💻 By Engineer")

    if 'engineer' in filtered_df.columns and not filtered_df.empty:
        engineers = filtered_df['engineer'].unique()

        for engineer in engineers:
            engineer_data = filtered_df[filtered_df['engineer'] == engineer]
            engineer_squad = engineer_data.iloc[0].get('squad', 'Unknown') if not engineer_data.empty else 'Unknown'

            # Count unique calls
            unique_calls = engineer_data['transactionId'].nunique() if 'transactionId' in engineer_data.columns else 0

            with st.expander(f"👤 {engineer} ({engineer_squad}) - {unique_calls} call(s)", expanded=False):
                # Group by Transaction ID
                if 'transactionId' in engineer_data.columns:
                    for tid in engineer_data['transactionId'].unique():
                        tid_updates = engineer_data[engineer_data['transactionId'] == tid].sort_values('timestamp')
                        update_count = len(tid_updates)

                        st.markdown(f"**📞 TID: {tid}** - {update_count} update(s)")

                        # Show timeline
                        for idx, update in tid_updates.iterrows():
                            time_str = update['timestamp'].strftime('%I:%M %p')
                            update_type = update.get('updateType', 'initial')

                            if update_type == 'initial':
                                st.markdown(f"⏰ **{time_str} - INITIAL**")
                                st.markdown(f"  Issue: {update.get('issue', 'N/A')}")
                                st.markdown(f"  Reason: {update.get('reason', 'N/A')}")
                            else:
                                st.markdown(f"⏰ **{time_str} - UPDATE**")
                                st.markdown(f"  {update.get('updateText', 'N/A')}")

                        st.markdown("---")
    else:
        st.info("No engineer data available")

    st.markdown("---")

    # BY DATE
    st.subheader("📅 By Date")

    if 'timestamp' in filtered_df.columns and not filtered_df.empty:
        dates = filtered_df['timestamp'].dt.date.unique()
        dates = sorted(dates, reverse=True)

        for date in dates[:14]:  # Last 14 days
            date_updates = filtered_df[filtered_df['timestamp'].dt.date == date]
            date_str = date.strftime('%B %d, %Y')
            unique_calls = date_updates['transactionId'].nunique() if 'transactionId' in date_updates.columns else 0

            with st.expander(f"📆 {date_str} - {len(date_updates)} update(s) ({unique_calls} call(s))", expanded=False):
                # Group by Transaction ID
                if 'transactionId' in date_updates.columns:
                    for tid in date_updates['transactionId'].unique():
                        tid_updates = date_updates[date_updates['transactionId'] == tid].sort_values('timestamp')
                        engineer = tid_updates.iloc[0].get('engineer', 'Unknown')

                        st.markdown(f"**TID: {tid}** - {engineer} - {len(tid_updates)} update(s)")

                        for idx, update in tid_updates.iterrows():
                            time_str = update['timestamp'].strftime('%I:%M %p')
                            update_type = update.get('updateType', 'initial')

                            if update_type == 'initial':
                                st.caption(f"⏰ {time_str} - INITIAL: {update.get('issue', 'N/A')[:50]}...")
                            else:
                                st.caption(f"⏰ {time_str} - UPDATE: {update.get('updateText', 'N/A')[:50]}...")

                        st.markdown("---")
    else:
        st.info("No date history available")

    # All Updates Table
    st.markdown("---")
    st.subheader("📋 All My Updates")

    if not engineer_df.empty:
        display_df = engineer_df[['timestamp', 'transactionId', 'squad', 'skillset', 'updateType']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %I:%M %p')
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No updates to display")

# Main app
def main():
    """Main application"""

    # Password check
    if not check_password():
        return

    # Get data
    df = get_updates()

    # View selection
    st.sidebar.markdown("---")
    st.sidebar.header("👁️ View")
    view_type = st.sidebar.radio("Select View", ["Squad Lead View", "Engineer View"])

    if view_type == "Engineer View":
        st.sidebar.markdown("---")
        st.sidebar.subheader("👤 Select Engineer")

        # Get list of engineers
        if 'engineer' in df.columns and not df.empty:
            engineers = sorted(df['engineer'].unique().tolist())
            selected_engineer = st.sidebar.selectbox("Engineer", engineers)
            engineer_view(df, selected_engineer)
        else:
            st.info("No engineer data available yet")

    else:  # Squad Lead View
        squad_lead_view(df)

    # Footer
    st.markdown("---")
    st.markdown('<div class="footer">TrendLife | Where intelligence meets care<br>Long Call Update Dashboard v1.0</div>', unsafe_allow_html=True)

    # Auto-refresh
    if view_type == "Squad Lead View":
        if st.session_state.get("auto_refresh", True):
            time.sleep(5)
            st.rerun()

if __name__ == "__main__":
    main()
