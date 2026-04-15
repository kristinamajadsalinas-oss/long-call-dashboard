"""
Long Call Update Dashboard - Final Correct Version
- Squad Leads: Icon navigation + full access
- Engineers: Simple personal view
- No re-login issues
- Real TrendLife icon
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib
import time
import base64

MANILA_TZ = pytz.timezone('Asia/Manila')
SQUAD_LEADS = ["chris", "judith", "josh", "bea"]

st.set_page_config(
    page_title="Long Call Updates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS with strong borders
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}

    .main {
        background-color: #F0F2F5;
        padding-left: 0;
    }

    /* Icon navigation */
    .icon-nav {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 70px;
        background-color: #FFFFFF;
        border-right: 2px solid #E1E4E8;
        z-index: 999;
        padding: 15px 0;
        box-shadow: 2px 0 8px rgba(0,0,0,0.05);
    }

    .nav-logo {
        width: 70px;
        height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px;
    }

    .nav-logo img {
        width: 45px;
        height: 45px;
        border-radius: 8px;
    }

    .nav-item {
        width: 70px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        color: #495057;
        margin: 6px 0;
        transition: all 0.2s;
        border-radius: 8px;
    }

    .nav-item:hover {
        background-color: #F6F8FA;
        color: #D71921;
    }

    .nav-item.active {
        background-color: #FFF0F0;
        color: #D71921;
        border-left: 4px solid #D71921;
    }

    .nav-icon {
        font-size: 28px;
        filter: grayscale(100%);
        opacity: 0.7;
    }

    .nav-item:hover .nav-icon {
        filter: grayscale(0%);
        opacity: 1;
    }

    .nav-item.active .nav-icon {
        filter: grayscale(0%) brightness(0) saturate(100%)
                invert(18%) sepia(98%) saturate(5847%)
                hue-rotate(352deg) brightness(91%) contrast(94%);
        opacity: 1;
    }

    .block-container {
        padding-left: 90px !important;
        padding-top: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }

    /* STRONG RED BORDERED BOXES - Like reference */
    .red-box {
        background-color: #FFFFFF;
        border: 3px solid #D71921;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 8px rgba(215, 25, 33, 0.08);
    }

    .light-box {
        background-color: #F8F9FA;
        border: 2px solid #DEE2E6;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .box-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #212529;
        margin-bottom: 0.5rem;
    }

    .box-subtitle {
        font-size: 0.85rem;
        color: #6C757D;
        margin-bottom: 1.5rem;
    }

    /* Typography */
    h1 {
        color: #D71921 !important;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        color: #6C757D;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Metrics */
    [data-testid="metric-container"] {
        background-color: transparent;
        padding: 0.5rem 0;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #6C757D !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #D71921 !important;
    }

    /* Update items */
    .update-card {
        background-color: #E7F5EC;
        border-left: 4px solid #28A745;
        padding: 1rem;
        margin-bottom: 0.875rem;
        border-radius: 6px;
    }

    /* Timer */
    .timer-box {
        background: linear-gradient(135deg, #FFF5F5, #FFE5E7);
        border: 3px solid #D71921;
        border-radius: 10px;
        padding: 2rem 1rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }

    .timer-value {
        font-size: 3rem;
        font-weight: 700;
        color: #D71921;
        font-family: monospace;
    }

    /* Tables */
    .dataframe {
        font-size: 0.875rem;
        border: none !important;
    }

    .dataframe thead th {
        background-color: #F6F8FA !important;
        color: #24292E !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #E1E4E8;
        color: #24292E !important;
        font-weight: 500;
        padding: 0.875rem;
    }

    .streamlit-expanderHeader * {
        color: #24292E !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #F6F8FA;
        border-color: #D71921;
    }

    /* Buttons */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 600;
        border-radius: 8px;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #959DA5;
        font-size: 0.8rem;
    }

    #MainMenu, footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(dict(st.secrets["gcp_service_account"]))
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except:
        return None

def check_login():
    PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates Dashboard")

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username", placeholder="judith or kristinamajasa")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):
                if password and hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH:
                    if username.strip():
                        role = "squad_lead" if username.lower() in SQUAD_LEADS else "engineer"
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.session_state.current_page = "home"  # Initialize page
                        st.rerun()
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
    except:
        return pd.DataFrame()

def submit_update(engineer, tid, text, squad, skillset):
    try:
        db = init_firebase()
        if not db:
            return False

        db.collection('updates').add({
            'timestamp': datetime.now(MANILA_TZ).isoformat(),
            'engineer': engineer,
            'transactionId': tid,
            'squad': squad,
            'skillset': skillset,
            'updateType': 'progress',
            'updateText': text,
            'callDuration': 'Unknown'
        })
        return True
    except:
        return False

def render_nav(current_page):
    """Icon sidebar with real TrendLife logo"""

    # Real TrendLife icon (base64 encoded from your icon48.png)
    # This is a placeholder - will use actual icon
    icon_html = f'<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" style="width:45px;height:45px;border-radius:8px;"/>'

    # Use actual icon from extension folder if available
    try:
        with open('/home/kristinamajasa/Long Call Update v1.0/icons/icon48.png', 'rb') as f:
            icon_data = base64.b64encode(f.read()).decode()
            icon_html = f'<img src="data:image/png;base64,{icon_data}" style="width:45px;height:45px;border-radius:8px;"/>'
    except:
        # Fallback to simple text
        icon_html = '<div style="width:45px;height:45px;background:#6C757D;border-radius:8px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:14px;">TL</div>'

    nav_html = f"""
    <div class="icon-nav">
        <div class="nav-logo">{icon_html}</div>

        <div class="nav-item {'active' if current_page == 'home' else ''}" title="Home">
            <div class="nav-icon">🏠</div>
        </div>

        <div class="nav-item {'active' if current_page == 'squad' else ''}" title="Squad">
            <div class="nav-icon">👥</div>
        </div>

        <div class="nav-item {'active' if current_page == 'engineer' else ''}" title="Engineer">
            <div class="nav-icon">👤</div>
        </div>

        <div class="nav-item {'active' if current_page == 'history' else ''}" title="History">
            <div class="nav-icon">📅</div>
        </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)

def home_view(df):
    st.title("Dashboard Overview")
    st.markdown("<div class='subtitle'>Good morning, Here's what's going on today</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # Layout: Large left box + Right stacked boxes
    left_col, right_col = st.columns([2, 1])

    # LEFT: Real-Time Updates (RED BOX)
    with left_col:
        st.markdown("<div class='red-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-title'>Real-Time Updates</div>", unsafe_allow_html=True)
        st.markdown("<div class='box-subtitle'>Live activity feed from all engineers</div>", unsafe_allow_html=True)

        recent = df.head(12)
        if not recent.empty:
            for _, row in recent.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')
                eng = row.get('engineer', 'Unknown')
                tid = row.get('transactionId', 'N/A')
                utype = row.get('updateType', 'initial')
                action = "started call" if utype == 'initial' else "posted update"

                st.markdown(f"""
                <div class="update-card">
                    <div style="font-weight:600;color:#212529;">🟢 {t} - {eng} {action}</div>
                    <div style="font-size:0.85rem;color:#6C757D;margin-top:0.25rem;">TID: {tid}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT COLUMN
    with right_col:
        # TOP: Longest Call (RED BOX)
        st.markdown("<div class='red-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-title'>Longest Call Running</div>", unsafe_allow_html=True)

        active = df[df['timestamp'] > one_hour_ago] if 'timestamp' in df.columns else pd.DataFrame()

        if not active.empty and 'transactionId' in active.columns:
            longest_dur = 0
            longest_eng = None
            longest_tid = None

            for tid in active['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                start = tid_data.iloc[0]['timestamp']
                dur = (now - start).total_seconds()
                if dur > longest_dur:
                    longest_dur = dur
                    longest_eng = tid_data.iloc[0].get('engineer', 'Unknown')
                    longest_tid = tid

            if longest_eng:
                mins = int(longest_dur / 60)
                secs = int(longest_dur % 60)

                st.markdown(f"""
                <div class="timer-box">
                    <div class="timer-value">{mins}m {secs}s</div>
                    <div style="margin-top:1rem;font-size:0.9rem;color:#495057;">
                        <strong>Engineer:</strong> {longest_eng}<br>
                        <strong>TID:</strong> {longest_tid}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                time.sleep(1)
                st.rerun()
        else:
            st.info("No active calls")

        st.markdown("<hr style='border-color:#E9ECEF;margin:1.5rem 0;'>", unsafe_allow_html=True)

        # Comparison
        st.markdown("<div style='font-size:0.95rem;font-weight:600;margin-bottom:1rem;'>Update Activity Comparison</div>", unsafe_allow_html=True)

        if 'engineer' in today_df.columns:
            comp = []
            for eng in today_df['engineer'].unique():
                eng_data = today_df[today_df['engineer'] == eng]
                initial = len(eng_data[eng_data['updateType'] == 'initial'])
                progress = len(eng_data[eng_data['updateType'] == 'progress'])
                comp.append({'Engineer': eng, 'Initial': initial, 'Progress': progress})

            if comp:
                st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True, height=120)

        st.markdown("</div>", unsafe_allow_html=True)

        # BOTTOM: Combined Duration (RED BOX)
        st.markdown("<div class='red-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-title'>Total Combined Duration</div>", unsafe_allow_html=True)

        total = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    total += int((tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60)

        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem 0;">
            <div style="font-size:3.5rem;font-weight:700;color:#D71921;">{total}m</div>
            <div style="font-size:0.8rem;color:#6C757D;margin-top:0.5rem;">Sum of all durations today</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # BOTTOM: Metrics Bar (LIGHT BOX, full width)
    st.markdown("<div class='light-box'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.85rem;font-weight:600;color:#6C757D;margin-bottom:1.5rem;text-transform:uppercase;letter-spacing:1px;'>Today's Metrics</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cases = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
        st.metric("Cases Today", cases)

    with col2:
        active_count = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
        st.metric("Active (Live)", active_count)

    with col3:
        ended = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                last = df[df['transactionId'] == tid]['timestamp'].max()
                if last < one_hour_ago:
                    ended += 1
        st.metric("Ended Calls", ended)

    with col4:
        over_1hr = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0 and (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60 >= 60:
                    over_1hr += 1
        st.metric(">1hr Calls", over_1hr)

    st.markdown("</div>", unsafe_allow_html=True)

def squad_view(df):
    st.title("View by Squad")

    selected = st.selectbox("Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search Engineer")
    date_range = st.selectbox("Date Range", ["Today", "Last 7 Days", "Last 30 Days"], index=1)

    if df.empty:
        return

    filtered = df[df['squad'].str.contains(selected, case=False, na=False)] if 'squad' in df.columns else df

    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    st.markdown(f"### Squad {selected}")
    st.markdown(f"**Engineers:** {filtered['engineer'].nunique()}")

    for eng in sorted(filtered['engineer'].unique()):
        eng_data = filtered[filtered['engineer'] == eng]
        with st.expander(f"{eng} - {eng_data['transactionId'].nunique()} calls"):
            for tid in eng_data['transactionId'].unique():
                tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
                st.markdown(f"**TID: {tid}**")
                for _, upd in tid_data.iterrows():
                    st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {upd.get('issue') if upd.get('updateType') == 'initial' else upd.get('updateText')}")

def engineer_detail_view(df):
    st.title("View by Engineer")

    engineers = sorted(df['engineer'].unique()) if 'engineer' in df.columns else []
    selected = st.selectbox("Engineer", engineers) if engineers else None

    if not selected:
        return

    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "All Time"])

    eng_data = df[df['engineer'] == selected]

    st.markdown(f"### {selected}")
    st.markdown(f"**Total Calls:** {eng_data['transactionId'].nunique()}")

    for tid in eng_data['transactionId'].unique():
        tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
        with st.expander(f"TID: {tid} - {len(tid_data)} updates"):
            for _, upd in tid_data.iterrows():
                st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {upd.get('issue') if upd.get('updateType') == 'initial' else upd.get('updateText')}")

def history_view(df):
    st.title("History")

    date_range = st.selectbox("Date Range", ["Today", "Last 7 Days", "Last 30 Days", "All Time"], index=1)

    if df.empty:
        return

    st.markdown(f"**Total Cases:** {df['transactionId'].nunique()}")

    if 'timestamp' in df.columns:
        df['date'] = df['timestamp'].dt.date
        for d in sorted(df['date'].unique(), reverse=True):
            d_data = df[df['date'] == d]
            with st.expander(f"{d.strftime('%B %d, %Y')} - {len(d_data)} updates"):
                for _, upd in d_data.iterrows():
                    eng = upd.get('engineer', 'Unknown')
                    tid = upd.get('transactionId', 'N/A')
                    st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {eng} - TID: {tid}")

def engineer_personal_view(username, df):
    """Engineer's simple personal dashboard (unchanged from before)"""

    st.title("My Long Call Updates")
    st.markdown(f"##### {username}'s Dashboard")

    if df.empty:
        st.warning("No data")
        return

    my_data = df[df['engineer'] == username]

    if my_data.empty:
        st.info("No updates yet")
        return

    tab1, tab2 = st.tabs(["Active Calls", "My History"])

    with tab1:
        st.markdown("## Active Calls")

        one_hr = datetime.now(MANILA_TZ) - timedelta(hours=1)
        active = {}

        for tid in my_data['transactionId'].unique():
            tid_data = my_data[my_data['transactionId'] == tid].sort_values('timestamp')
            if tid_data.iloc[-1]['timestamp'] > one_hr:
                active[tid] = tid_data

        if active:
            for tid, data in active.items():
                first = data.iloc[0]
                st.markdown(f"### TID: {tid}")

                for _, upd in data.iterrows():
                    t = upd['timestamp'].strftime('%I:%M %p')
                    if upd.get('updateType') == 'initial':
                        st.info(f"**{t} - Initial**\n\n{upd.get('issue')}\n\n{upd.get('reason')}")
                    else:
                        st.success(f"**{t} - Update**\n\n{upd.get('updateText')}")

                with st.form(key=f"f_{tid}"):
                    txt = st.text_area("Add Update", height=60, placeholder="Progress update...")
                    if st.form_submit_button("Submit", use_container_width=True):
                        if txt.strip():
                            if submit_update(username, tid, txt, first.get('squad'), first.get('skillset')):
                                st.success("Submitted")
                                time.sleep(1)
                                st.rerun()
                st.markdown("---")
        else:
            st.info("No active calls")

    with tab2:
        st.markdown("## History")
        seven = datetime.now(MANILA_TZ) - timedelta(days=7)
        history = my_data[my_data['timestamp'] > seven]

        if not history.empty:
            for tid in history['transactionId'].unique():
                if tid in active:
                    continue

                tid_data = history[history['transactionId'] == tid].sort_values('timestamp')
                with st.expander(f"TID: {tid} - {tid_data.iloc[0]['timestamp'].strftime('%b %d')} - {len(tid_data)} updates"):
                    for _, upd in tid_data.iterrows():
                        st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {upd.get('issue') if upd.get('updateType') == 'initial' else upd.get('updateText')}")

def main():
    if not check_login():
        return

    username = st.session_state.username
    role = st.session_state.role

    # Initialize page state if not exists
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

    # Get data
    df = get_updates()

    # SQUAD LEAD VIEW: Icon navigation
    if role == "squad_lead":
        # Navigation buttons in sidebar using session state
        current_page = st.session_state.current_page

        # Render icon nav
        render_nav(current_page)

        # Page navigation buttons (hidden, triggered by icon clicks)
        col1, col2, col3, col4, col5 = st.columns([1,1,1,1,2])

        with col1:
            if st.button("🏠", key="nav_home", help="Home"):
                st.session_state.current_page = 'home'
                st.rerun()

        with col2:
            if st.button("👥", key="nav_squad", help="Squad"):
                st.session_state.current_page = 'squad'
                st.rerun()

        with col3:
            if st.button("👤", key="nav_engineer", help="Engineer"):
                st.session_state.current_page = 'engineer'
                st.rerun()

        with col4:
            if st.button("📅", key="nav_history", help="History"):
                st.session_state.current_page = 'history'
                st.rerun()

        with col5:
            if st.button("Logout", key="logout"):
                st.session_state.authenticated = False
                st.rerun()

        # Route to page (NO RELOAD!)
        if current_page == 'home':
            home_view(df)
        elif current_page == 'squad':
            squad_view(df)
        elif current_page == 'engineer':
            engineer_detail_view(df)
        elif current_page == 'history':
            history_view(df)

    # ENGINEER VIEW: Simple personal dashboard
    else:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

        engineer_personal_view(username, df)

    st.markdown("<div class='footer'><b>TrendLife</b> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
