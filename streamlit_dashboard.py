"""
Long Call Update Dashboard - Squad Lead View
Exact layout matching reference design with bordered sections
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib
import time

MANILA_TZ = pytz.timezone('Asia/Manila')
SQUAD_LEADS = ["chris", "judith", "josh", "bea"]

st.set_page_config(
    page_title="Long Call Updates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS - Match reference design with bordered boxes
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}

    .main {
        background-color: #F0F2F5;
        padding-left: 0;
    }

    /* Icon sidebar */
    .icon-nav {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 70px;
        background-color: #FFFFFF;
        border-right: 1px solid #E1E4E8;
        z-index: 999;
        padding: 15px 0;
    }

    .nav-logo {
        width: 70px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 15px;
    }

    .nav-item {
        width: 70px;
        height: 65px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #6C757D;
        text-decoration: none;
        margin: 2px 0;
    }

    .nav-item:hover {
        background-color: #F6F8FA;
        color: #D71921;
    }

    .nav-item.active {
        background-color: #FFF5F5;
        color: #D71921;
        border-left: 3px solid #D71921;
    }

    .nav-icon {
        font-size: 22px;
        margin-bottom: 4px;
    }

    .nav-label {
        font-size: 9px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .block-container {
        padding-left: 90px !important;
        padding-top: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }

    /* Bordered section boxes - like reference */
    .section-box {
        background-color: #FFFFFF;
        border: 2px solid #D71921;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    }

    .section-box-light {
        background-color: #FAFBFC;
        border: 1px solid #E1E4E8;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #24292E;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .section-subtitle {
        font-size: 0.85rem;
        color: #6C757D;
        margin-bottom: 1rem;
    }

    /* Typography */
    h1 {
        color: #D71921 !important;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 0.3rem;
    }

    h2 {
        color: #24292E !important;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background-color: transparent;
        padding: 0.5rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.65rem !important;
        color: #6C757D !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #D71921 !important;
    }

    /* Update feed items */
    .update-item {
        background-color: #E7F5EC;
        border-left: 4px solid #28A745;
        padding: 0.875rem;
        margin-bottom: 0.75rem;
        border-radius: 4px;
    }

    .update-time {
        font-weight: 600;
        color: #24292E;
        font-size: 0.9rem;
    }

    .update-engineer {
        color: #495057;
        font-size: 0.85rem;
    }

    /* Timer display */
    .timer-display {
        background: linear-gradient(135deg, #FFF5F5 0%, #FFE5E7 100%);
        border: 2px solid #D71921;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }

    .timer-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #D71921;
        font-family: 'Courier New', monospace;
    }

    .timer-label {
        font-size: 0.75rem;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }

    /* Tables */
    .dataframe {
        font-size: 0.85rem !important;
        border: none !important;
    }

    .dataframe thead tr th {
        background-color: #F6F8FA !important;
        color: #24292E !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        border-bottom: 2px solid #E1E4E8 !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F6F8FA !important;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 4px;
        border-left-width: 4px;
    }

    /* Buttons */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        border: none;
    }

    .stButton button:hover {
        background-color: #B01419;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #959DA5;
        font-size: 0.8rem;
        margin-top: 2rem;
    }

    #MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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

def check_login():
    PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates Dashboard")

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

def render_nav():
    params = st.query_params
    current = params.get("page", "home")

    logo_svg = '<svg width="30" height="30" viewBox="0 0 100 100"><circle cx="30" cy="50" r="22" fill="#6C757D"/><circle cx="70" cy="50" r="32" fill="none" stroke="#6C757D" stroke-width="7"/></svg>'

    nav_html = f"""
    <div class="icon-nav">
        <div class="nav-logo">{logo_svg}</div>
        <a class="nav-item {'active' if current == 'home' else ''}" href="?page=home" target="_self">
            <div class="nav-icon">🏠</div>
            <div class="nav-label">Home</div>
        </a>
        <a class="nav-item {'active' if current == 'squad' else ''}" href="?page=squad" target="_self">
            <div class="nav-icon">👥</div>
            <div class="nav-label">Squad</div>
        </a>
        <a class="nav-item {'active' if current == 'engineer' else ''}" href="?page=engineer" target="_self">
            <div class="nav-icon">👤</div>
            <div class="nav-label">Engineer</div>
        </a>
        <a class="nav-item {'active' if current == 'history' else ''}" href="?page=history" target="_self">
            <div class="nav-icon">📅</div>
            <div class="nav-label">History</div>
        </a>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)

def home_view(df):
    st.title("Dashboard Overview")
    st.caption("Good morning, Here's what's going on today")

    if df.empty:
        st.warning("No data available")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # Top row: Real-time feed (left) + Right cards
    left_col, right_col = st.columns([2, 1])

    # SECTION 2: Real-Time Updates (Large left box with red border)
    with left_col:
        st.markdown("""
        <div class="section-box">
            <div class="section-header">
                <span>Real-Time Updates</span>
            </div>
            <div class="section-subtitle">Live activity feed from all engineers</div>
        """, unsafe_allow_html=True)

        recent = df.head(12)
        if not recent.empty:
            for _, row in recent.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')
                eng = row.get('engineer', 'Unknown')
                tid = row.get('transactionId', 'N/A')
                utype = row.get('updateType', 'initial')

                st.markdown(f"""
                <div class="update-item">
                    <div class="update-time">🟢 {t} - {eng} {'started call' if utype == 'initial' else 'posted update'}</div>
                    <div class="update-engineer">TID: {tid}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent updates")

        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT COLUMN: Two stacked boxes
    with right_col:
        # SECTION 4: Longest Call + Comparison (Top right red box)
        st.markdown("""
        <div class="section-box">
            <div class="section-header">Longest Call Running</div>
        """, unsafe_allow_html=True)

        active_data = df[df['timestamp'] > one_hour_ago] if 'timestamp' in df.columns else pd.DataFrame()

        if not active_data.empty and 'transactionId' in active_data.columns:
            longest_dur = 0
            longest_eng = None
            longest_tid = None

            for tid in active_data['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                start = tid_data.iloc[0]['timestamp']
                dur_sec = (now - start).total_seconds()
                if dur_sec > longest_dur:
                    longest_dur = dur_sec
                    longest_eng = tid_data.iloc[0].get('engineer', 'Unknown')
                    longest_tid = tid

            if longest_eng:
                mins = int(longest_dur / 60)
                secs = int(longest_dur % 60)

                st.markdown(f"""
                <div class="timer-display">
                    <div class="timer-value">{mins}m {secs}s</div>
                    <div class="timer-label">Live Timer</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Engineer:** {longest_eng}")
                st.markdown(f"**TID:** {longest_tid}")

                # Auto-refresh for timer
                time.sleep(1)
                st.rerun()
        else:
            st.info("No active calls")

        st.markdown("<hr style='margin:1.5rem 0;border-color:#E1E4E8;'>", unsafe_allow_html=True)

        # Comparison
        st.markdown("<div class='section-subtitle'>Update Activity Comparison</div>", unsafe_allow_html=True)

        if 'engineer' in today_df.columns and 'updateType' in today_df.columns:
            comp_data = []
            for eng in today_df['engineer'].unique():
                eng_data = today_df[today_df['engineer'] == eng]
                initial = len(eng_data[eng_data['updateType'] == 'initial'])
                progress = len(eng_data[eng_data['updateType'] == 'progress'])
                comp_data.append({'Engineer': eng, 'Initial': initial, 'Progress': progress})

            if comp_data:
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True, height=150)

        st.markdown("</div>", unsafe_allow_html=True)

        # SECTION 3: Combined Duration (Bottom right red box)
        st.markdown("""
        <div class="section-box">
            <div class="section-header">Total Combined Duration</div>
        """, unsafe_allow_html=True)

        total_mins = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    dur = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60
                    total_mins += int(dur)

        st.markdown(f"""
        <div style="text-align:center;padding:2rem 0;">
            <div style="font-size:3rem;font-weight:700;color:#D71921;">{total_mins}m</div>
            <div style="font-size:0.8rem;color:#6C757D;">Sum of all long call durations today</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # SECTION 5: Metrics Bar (Bottom, full width, light box)
    st.markdown("""
    <div class="section-box-light">
        <div style="font-size:0.9rem;font-weight:600;color:#6C757D;margin-bottom:1rem;">TODAY'S METRICS</div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cases = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
        st.metric("Cases Today", cases)

    with col2:
        active = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
        st.metric("Active (Live)", active)

    with col3:
        ended = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                last = df[df['transactionId'] == tid]['timestamp'].max()
                if last < one_hour_ago:
                    ended += 1
        st.metric("Ended Calls", ended)

    with col4:
        over_hour = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    dur = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60
                    if dur >= 60:
                        over_hour += 1
        st.metric(">1hr Calls", over_hour)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='footer'><b>TrendLife</b> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

def squad_view(df):
    st.title("View by Squad")

    selected = st.selectbox("Select Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search Engineer")
    date_range = st.selectbox("Date Range", ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"], index=2)

    if df.empty:
        st.warning("No data")
        return

    filtered = df[df['squad'].str.contains(selected, case=False, na=False)] if 'squad' in df.columns else df

    if search and 'engineer' in filtered.columns:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    # Date filter
    if 'timestamp' in filtered.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Today":
            filtered = filtered[filtered['timestamp'] >= now.replace(hour=0, minute=0, second=0)]
        elif date_range == "Last 7 Days":
            filtered = filtered[filtered['timestamp'] >= now - timedelta(days=7)]

    st.markdown(f"### Squad {selected}")
    st.markdown(f"**Engineers:** {filtered['engineer'].nunique() if 'engineer' in filtered.columns else 0}")

    if 'engineer' in filtered.columns:
        for eng in sorted(filtered['engineer'].unique()):
            eng_data = filtered[filtered['engineer'] == eng]
            with st.expander(f"{eng} - {eng_data['transactionId'].nunique()} calls"):
                for tid in eng_data['transactionId'].unique():
                    tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
                    st.markdown(f"**TID: {tid}** - {len(tid_data)} updates")
                    for _, upd in tid_data.iterrows():
                        t = upd['timestamp'].strftime('%I:%M %p')
                        if upd.get('updateType') == 'initial':
                            st.info(f"{t} - {upd.get('issue')}")
                        else:
                            st.success(f"{t} - {upd.get('updateText')}")

def engineer_view(df):
    st.title("View by Engineer")

    if df.empty:
        st.warning("No data")
        return

    engineers = sorted(df['engineer'].unique().tolist()) if 'engineer' in df.columns else []
    selected = st.selectbox("Select Engineer", engineers) if engineers else None

    if not selected:
        return

    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "All Time"])

    eng_data = df[df['engineer'] == selected]

    st.markdown(f"### {selected}")
    st.markdown(f"**Total Calls:** {eng_data['transactionId'].nunique()}")

    for tid in eng_data['transactionId'].unique():
        tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
        with st.expander(f"TID: {tid} - {tid_data.iloc[0]['timestamp'].strftime('%b %d')} - {len(tid_data)} updates"):
            for _, upd in tid_data.iterrows():
                t = upd['timestamp'].strftime('%I:%M %p')
                if upd.get('updateType') == 'initial':
                    st.info(f"{t} - {upd.get('issue')}")
                else:
                    st.success(f"{t} - {upd.get('updateText')}")

def history_view(df):
    st.title("History")

    date_range = st.selectbox("Date Range", ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"], index=2)

    if df.empty:
        st.warning("No data")
        return

    if 'timestamp' in df.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Today":
            filtered = df[df['timestamp'] >= now.replace(hour=0, minute=0, second=0)]
        elif date_range == "Last 7 Days":
            filtered = df[df['timestamp'] >= now - timedelta(days=7)]
        else:
            filtered = df

        st.markdown(f"**Total Cases:** {filtered['transactionId'].nunique()}")

        filtered['date'] = filtered['timestamp'].dt.date
        for d in sorted(filtered['date'].unique(), reverse=True):
            d_data = filtered[filtered['date'] == d]
            with st.expander(f"{d.strftime('%B %d, %Y')} - {len(d_data)} updates"):
                for tid in d_data['transactionId'].unique():
                    tid_data = d_data[d_data['transactionId'] == tid]
                    eng = tid_data.iloc[0].get('engineer', 'Unknown')
                    st.markdown(f"**{eng}** - TID: {tid}")
                    for _, upd in tid_data.iterrows():
                        st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {upd.get('issue') if upd.get('updateType') == 'initial' else upd.get('updateText')}")

def main():
    if not check_login():
        return

    render_nav()

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    df = get_updates()

    page = st.query_params.get("page", "home")

    if page == "squad":
        squad_view(df)
    elif page == "engineer":
        engineer_view(df)
    elif page == "history":
        history_view(df)
    else:
        home_view(df)

    st.markdown("<div class='footer'><b>TrendLife</b> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
