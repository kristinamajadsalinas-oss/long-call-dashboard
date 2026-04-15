"""
Long Call Update Dashboard - Squad Lead View
Icon-based navigation with comprehensive monitoring features
Professional clean design matching extension UI
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib
import time

# Manila timezone
MANILA_TZ = pytz.timezone('Asia/Manila')

# Squad Leads (authorized users)
SQUAD_LEADS = ["chris", "judith", "josh", "bea"]

# Page configuration
st.set_page_config(
    page_title="Long Call Updates - Squad Lead",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Icon sidebar + professional design
st.markdown("""
<style>
    /* Hide default sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Main background */
    .main {
        background-color: #F8F9FA;
        padding-left: 0;
        margin-left: 0;
    }

    /* Custom icon navigation sidebar */
    .icon-nav {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 80px;
        background-color: #FFFFFF;
        border-right: 1px solid #E9ECEF;
        z-index: 999;
        padding: 20px 0;
        box-shadow: 2px 0 4px rgba(0,0,0,0.02);
    }

    .nav-logo {
        width: 80px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
    }

    .nav-logo svg {
        width: 35px;
        height: 35px;
    }

    .nav-item {
        width: 80px;
        height: 70px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        color: #6C757D;
        margin: 4px 0;
    }

    .nav-item:hover {
        background-color: #F8F9FA;
        color: #D71921;
    }

    .nav-item.active {
        background-color: #FFF5F5;
        color: #D71921;
        border-left: 3px solid #D71921;
    }

    .nav-item-icon {
        font-size: 24px;
        margin-bottom: 6px;
    }

    .nav-item-label {
        font-size: 10px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    /* Main content shifted for sidebar */
    .block-container {
        padding-left: 100px !important;
        padding-top: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }

    /* Typography */
    h1 {
        color: #D71921 !important;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    h2 {
        color: #212529 !important;
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E9ECEF;
    }

    h3 {
        color: #495057 !important;
        font-size: 1rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    /* Metrics cards */
    [data-testid="metric-container"] {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #DEE2E6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #D71921 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #6C757D !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }

    /* Live timer special styling */
    .live-timer {
        font-size: 3rem;
        font-weight: 700;
        color: #D71921;
        font-family: 'Courier New', monospace;
        text-align: center;
        padding: 1rem;
        background-color: #FFF5F5;
        border-radius: 8px;
        border: 2px solid #FFE5E7;
    }

    .timer-label {
        font-size: 0.8rem;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* Cards */
    .card {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .card:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border-color: #ADB5BD;
    }

    /* Tables */
    .dataframe {
        font-size: 0.875rem;
        border: 1px solid #DEE2E6 !important;
        border-radius: 6px;
    }

    .dataframe thead tr th {
        background-color: #F8F9FA !important;
        color: #495057 !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        padding: 0.875rem !important;
    }

    .dataframe tbody tr td {
        padding: 0.75rem !important;
        color: #212529 !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F8F9FA !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        color: #495057 !important;
        font-weight: 500;
        padding: 0.875rem 1rem;
    }

    .streamlit-expanderHeader * {
        color: #495057 !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #F8F9FA;
    }

    /* Progress bar */
    .progress-bar {
        height: 8px;
        background-color: #E9ECEF;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }

    .progress-fill {
        height: 100%;
        background-color: #28A745;
        transition: width 0.3s;
    }

    /* Buttons */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 600;
        border-radius: 6px;
    }

    .stButton button:hover {
        background-color: #B01419;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #ADB5BD;
        font-size: 0.8rem;
        border-top: 1px solid #E9ECEF;
        margin-top: 3rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["gcp_service_account"]))
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return None

# Login
def check_login():
    PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates - Squad Lead Dashboard")

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username", placeholder="judith")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):
                if password and hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH:
                    if username.strip():
                        if username.lower() in SQUAD_LEADS:
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Access denied. Squad leads only.")
                    else:
                        st.error("Enter username")
                else:
                    st.error("Incorrect password")

            st.info("Password: admin • Squad Leads: chris, judith, josh, bea")
        return False
    return True

# Get data
@st.cache_data(ttl=5)
def get_updates():
    try:
        db = init_firebase()
        if not db:
            return pd.DataFrame()

        docs = db.collection('updates').stream()
        data = [doc.to_dict() for doc in docs]

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.tz_convert(MANILA_TZ)
            df = df.sort_values('timestamp', ascending=False)

        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# Icon sidebar
def render_nav():
    """Render icon navigation"""

    params = st.query_params
    current = params.get("page", "home")

    # Simple TrendLife logo (two circles)
    logo_svg = """
    <svg width="35" height="35" viewBox="0 0 100 100">
        <circle cx="30" cy="50" r="22" fill="#6C757D"/>
        <circle cx="70" cy="50" r="32" fill="none" stroke="#6C757D" stroke-width="7"/>
    </svg>
    """

    nav_html = f"""
    <div class="icon-nav">
        <div class="nav-logo">{logo_svg}</div>

        <a class="nav-item {'active' if current == 'home' else ''}" href="?page=home" target="_self">
            <div class="nav-item-icon">🏠</div>
            <div class="nav-item-label">Home</div>
        </a>

        <a class="nav-item {'active' if current == 'squad' else ''}" href="?page=squad" target="_self">
            <div class="nav-item-icon">👥</div>
            <div class="nav-item-label">Squad</div>
        </a>

        <a class="nav-item {'active' if current == 'engineer' else ''}" href="?page=engineer" target="_self">
            <div class="nav-item-icon">👤</div>
            <div class="nav-item-label">Engineer</div>
        </a>

        <a class="nav-item {'active' if current == 'history' else ''}" href="?page=history" target="_self">
            <div class="nav-item-icon">📅</div>
            <div class="nav-item-label">History</div>
        </a>
    </div>
    """

    st.markdown(nav_html, unsafe_allow_html=True)

# HOME VIEW
def home_view(df):
    """Overview dashboard with live metrics and monitoring"""

    st.title("Dashboard Overview")
    st.markdown("##### Real-time monitoring for extended customer calls")

    if df.empty:
        st.warning("No data available")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    # Get today's data
    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # METRICS (Section 5)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        # Cases today (unique TIDs)
        cases_today = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
        st.metric("Cases Today", cases_today)

    with col2:
        # Active calls (engineers with updates in last hour)
        active_count = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
        st.metric("Active (Live)", active_count)

    with col3:
        # Ended calls (TIDs from today where last update >1hr ago)
        ended = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_all = df[df['transactionId'] == tid]
                last_update = tid_all['timestamp'].max()
                if last_update < one_hour_ago:
                    ended += 1
        st.metric("Ended Calls", ended)

    with col4:
        # Calls >1 hour (from today)
        long_calls = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    duration = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60
                    if duration >= 60:
                        long_calls += 1
        st.metric(">1hr Calls", long_calls)

    with col5:
        # Combined duration (sum of all call durations today)
        total_minutes = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    duration = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60
                    total_minutes += int(duration)
        st.metric("Combined Duration", f"{total_minutes}m")

    st.markdown("---")

    # Two column layout
    left_col, right_col = st.columns([1, 1])

    # LEFT: Real-time Updates (Section 2)
    with left_col:
        st.markdown("## Real-Time Updates")
        st.caption("Live activity feed from all engineers")

        recent_updates = df.head(15)

        if not recent_updates.empty:
            for _, row in recent_updates.iterrows():
                time_str = row['timestamp'].strftime('%I:%M %p')
                engineer = row.get('engineer', 'Unknown')
                tid = row.get('transactionId', 'N/A')
                utype = row.get('updateType', 'initial')

                if utype == 'initial':
                    st.info(f"🟢 **{time_str}** - {engineer} started call\n\nTID: {tid}")
                else:
                    st.success(f"🟢 **{time_str}** - {engineer} posted update\n\nTID: {tid}")
        else:
            st.info("No recent updates")

    # RIGHT: Longest Call + Comparison (Section 4)
    with right_col:
        # TOP: Longest Running Call
        st.markdown("## Longest Call Running")

        if 'timestamp' in df.columns and 'transactionId' in df.columns:
            active_data = df[df['timestamp'] > one_hour_ago]

            if not active_data.empty:
                # Find longest active call
                longest_duration = 0
                longest_engineer = None
                longest_tid = None
                longest_start = None

                for tid in active_data['transactionId'].unique():
                    tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                    start_time = tid_data.iloc[0]['timestamp']
                    duration_sec = (now - start_time).total_seconds()

                    if duration_sec > longest_duration:
                        longest_duration = duration_sec
                        longest_engineer = tid_data.iloc[0].get('engineer', 'Unknown')
                        longest_tid = tid
                        longest_start = start_time

                if longest_engineer:
                    minutes = int(longest_duration / 60)
                    seconds = int(longest_duration % 60)

                    # Live timer display
                    st.markdown(f"<div class='live-timer'>{minutes}m {seconds}s</div>", unsafe_allow_html=True)
                    st.markdown(f"**Engineer:** {longest_engineer}")
                    st.markdown(f"**TID:** {longest_tid}")
                    st.markdown(f"**Started:** {longest_start.strftime('%I:%M %p')}")

                    # Auto-refresh for live timer
                    time.sleep(1)
                    st.rerun()
            else:
                st.info("No active calls currently")

        st.markdown("---")

        # BOTTOM: Update Comparison Chart
        st.markdown("## Update Activity Comparison")
        st.caption("Initial Entries vs Progress Updates")

        if 'engineer' in today_df.columns and 'updateType' in today_df.columns:
            # Count initial vs progress by engineer
            comparison_data = []

            for eng in today_df['engineer'].unique():
                eng_data = today_df[today_df['engineer'] == eng]
                initial_count = len(eng_data[eng_data['updateType'] == 'initial'])
                progress_count = len(eng_data[eng_data['updateType'] == 'progress'])

                comparison_data.append({
                    'Engineer': eng,
                    'Initial': initial_count,
                    'Progress': progress_count,
                    'Ratio': f"{progress_count}:{initial_count}" if initial_count > 0 else "N/A"
                })

            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
            else:
                st.info("No data for comparison")

# SQUAD VIEW
def squad_view(df):
    """View by squad with search"""

    st.title("View by Squad")

    # Squad selector
    selected_squad = st.selectbox("Select Squad", ["Chris", "Judith", "Josh", "Bea"])

    # Search bar
    search = st.text_input("🔍 Search Engineer", placeholder="Type engineer name...")

    # Date range
    date_range = st.selectbox("Date Range", ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"], index=2)

    if df.empty:
        st.warning("No data")
        return

    # Apply filters
    filtered = df[df['squad'].str.contains(selected_squad, case=False, na=False)] if 'squad' in df.columns else df

    # Date filter
    if 'timestamp' in filtered.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Today":
            filtered = filtered[filtered['timestamp'] >= now.replace(hour=0, minute=0, second=0)]
        elif date_range == "Yesterday":
            yesterday = now - timedelta(days=1)
            filtered = filtered[
                (filtered['timestamp'] >= yesterday.replace(hour=0, minute=0, second=0)) &
                (filtered['timestamp'] < now.replace(hour=0, minute=0, second=0))
            ]
        elif date_range == "Last 7 Days":
            filtered = filtered[filtered['timestamp'] >= now - timedelta(days=7)]
        elif date_range == "Last 30 Days":
            filtered = filtered[filtered['timestamp'] >= now - timedelta(days=30)]

    # Search filter
    if search and 'engineer' in filtered.columns:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    # Display
    st.markdown(f"## Squad {selected_squad}")

    engineers = filtered['engineer'].unique() if 'engineer' in filtered.columns else []
    st.markdown(f"**Engineers with updates:** {len(engineers)}")

    for eng in sorted(engineers):
        eng_data = filtered[filtered['engineer'] == eng]
        calls = eng_data['transactionId'].nunique()

        with st.expander(f"{eng} - {calls} call(s)"):
            for tid in eng_data['transactionId'].unique():
                tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')

                st.markdown(f"**TID: {tid}** • {tid_data.iloc[0]['timestamp'].strftime('%b %d %I:%M %p')} • {len(tid_data)} updates")

                for _, upd in tid_data.iterrows():
                    t = upd['timestamp'].strftime('%I:%M %p')
                    if upd.get('updateType') == 'initial':
                        st.info(f"**{t} - INITIAL**\n\n{upd.get('issue', 'N/A')}")
                    else:
                        st.success(f"**{t} - UPDATE**\n\n{upd.get('updateText', 'N/A')}")

                st.markdown("---")

# ENGINEER VIEW
def engineer_view(df):
    """View specific engineer"""

    st.title("View by Engineer")

    if df.empty:
        st.warning("No data")
        return

    engineers = sorted(df['engineer'].unique().tolist()) if 'engineer' in df.columns else []

    selected = st.selectbox("Select Engineer", engineers) if engineers else None

    if not selected:
        st.info("No engineers found")
        return

    # Date range
    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "All Time"], index=0)

    eng_data = df[df['engineer'] == selected]

    # Date filter
    if 'timestamp' in eng_data.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Last 7 Days":
            eng_data = eng_data[eng_data['timestamp'] >= now - timedelta(days=7)]
        elif date_range == "Last 30 Days":
            eng_data = eng_data[eng_data['timestamp'] >= now - timedelta(days=30)]

    st.markdown(f"## {selected}")
    st.markdown(f"**Total Calls:** {eng_data['transactionId'].nunique()}")

    # Calculate longest call
    if 'transactionId' in eng_data.columns and 'timestamp' in eng_data.columns:
        longest_duration = 0
        longest_tid = None

        for tid in eng_data['transactionId'].unique():
            tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
            if len(tid_data) > 1:
                duration = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60
                if duration > longest_duration:
                    longest_duration = duration
                    longest_tid = tid

        if longest_tid:
            st.markdown(f"**Longest Call:** {int(longest_duration)}m (TID: {longest_tid})")

    # Show all calls
    for tid in eng_data['transactionId'].unique():
        tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
        first = tid_data.iloc[0]

        with st.expander(f"TID: {tid} - {first['timestamp'].strftime('%b %d %I:%M %p')} - {len(tid_data)} updates"):
            for _, upd in tid_data.iterrows():
                t = upd['timestamp'].strftime('%I:%M %p')
                if upd.get('updateType') == 'initial':
                    st.info(f"**{t} - INITIAL**\n\nIssue: {upd.get('issue')}\n\nReason: {upd.get('reason')}")
                else:
                    st.success(f"**{t} - UPDATE**\n\n{upd.get('updateText')}")

# HISTORY VIEW
def history_view(df):
    """Global history with date range"""

    st.title("History")

    # Date range dropdown
    date_range = st.selectbox("Date Range", ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"], index=2)

    if df.empty:
        st.warning("No data")
        return

    # Apply date filter
    if 'timestamp' in df.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Today":
            filtered = df[df['timestamp'] >= now.replace(hour=0, minute=0, second=0)]
        elif date_range == "Yesterday":
            yesterday = now - timedelta(days=1)
            filtered = df[
                (df['timestamp'] >= yesterday.replace(hour=0, minute=0, second=0)) &
                (df['timestamp'] < now.replace(hour=0, minute=0, second=0))
            ]
        elif date_range == "Last 7 Days":
            filtered = df[df['timestamp'] >= now - timedelta(days=7)]
        elif date_range == "Last 30 Days":
            filtered = df[df['timestamp'] >= now - timedelta(days=30)]
        else:
            filtered = df

        st.markdown(f"**Total Cases:** {filtered['transactionId'].nunique()}")

        # Group by date
        filtered['date'] = filtered['timestamp'].dt.date
        dates = sorted(filtered['date'].unique(), reverse=True)

        for d in dates:
            d_data = filtered[filtered['date'] == d]
            d_str = d.strftime('%B %d, %Y')

            with st.expander(f"{d_str} - {len(d_data)} updates - {d_data['transactionId'].nunique()} calls"):
                for tid in d_data['transactionId'].unique():
                    tid_data = d_data[d_data['transactionId'] == tid].sort_values('timestamp')
                    eng = tid_data.iloc[0].get('engineer', 'Unknown')

                    st.markdown(f"**{eng}** - TID: {tid} - {len(tid_data)} updates")

                    for _, upd in tid_data.iterrows():
                        t = upd['timestamp'].strftime('%I:%M %p')
                        if upd.get('updateType') == 'initial':
                            st.info(f"{t} - {upd.get('issue')}")
                        else:
                            st.success(f"{t} - {upd.get('updateText')}")

                    st.markdown("---")

# MAIN
def main():
    if not check_login():
        return

    username = st.session_state.username

    # Render navigation
    render_nav()

    # Get data
    df = get_updates()

    # Logout button (top right)
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # Route to page
    params = st.query_params
    page = params.get("page", "home")

    if page == "squad":
        squad_view(df)
    elif page == "engineer":
        engineer_view(df)
    elif page == "history":
        history_view(df)
    else:
        home_view(df)

    # Footer
    st.markdown("<div class='footer'><span style='font-weight:700;color:#212529;'>TrendLife</span> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
