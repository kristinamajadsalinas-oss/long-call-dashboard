"""
Long Call Update Dashboard - Final Clean Design
Matches Streamlit docs style - Minimal, organized, professional
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

# Page configuration
st.set_page_config(
    page_title="Long Call Updates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal professional CSS
st.markdown("""
<style>
    /* Clean white background */
    .main {
        background-color: #FFFFFF;
        padding: 2rem;
    }

    /* Typography */
    h1 {
        color: #D71921 !important;
        font-weight: 600;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    h2 {
        color: #495057 !important;
        font-size: 1.5rem;
        font-weight: 500;
        margin-top: 2.5rem;
        margin-bottom: 1.5rem;
    }

    h3 {
        color: #6C757D !important;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }

    /* Subtitle */
    .subtitle {
        color: #6C757D;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    /* Metrics - Simple clean cards */
    [data-testid="metric-container"] {
        background-color: #FFFFFF;
        padding: 1.25rem;
        border: 1px solid #E9ECEF;
        border-radius: 4px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem;
        color: #6C757D !important;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    [data-testid="stMetricValue"] {
        font-size: 2.25rem !important;
        font-weight: 600 !important;
        color: #D71921 !important;
    }

    /* Tabs - Like docs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: transparent;
        border-bottom: 1px solid #E9ECEF;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #6C757D;
        font-weight: 400;
        padding: 0.75rem 1.5rem;
        font-size: 0.95rem;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #D71921;
    }

    .stTabs [aria-selected="true"] {
        color: #D71921;
        font-weight: 500;
        border-bottom: 2px solid #D71921;
    }

    /* Tables - Clean professional */
    .dataframe {
        font-size: 0.875rem;
    }

    .dataframe thead tr th {
        background-color: #F8F9FA !important;
        color: #495057 !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.875rem 0.75rem !important;
        border-bottom: 1px solid #DEE2E6 !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F8F9FA !important;
    }

    .dataframe tbody tr td {
        padding: 0.75rem !important;
        color: #212529 !important;
        border-bottom: 1px solid #F1F3F5 !important;
    }

    /* Sidebar - Clean minimal */
    [data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #E9ECEF;
        padding-top: 2rem;
    }

    [data-testid="stSidebar"] h3 {
        color: #212529 !important;
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
        margin-top: 2rem;
    }

    /* Radio buttons - Clean */
    .stRadio > label {
        font-size: 0.875rem;
        color: #495057;
        font-weight: 400;
    }

    /* Select boxes */
    .stSelectbox > label {
        font-size: 0.8rem;
        color: #6C757D;
        font-weight: 500;
    }

    /* Buttons */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 500;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        width: 100%;
    }

    .stButton button:hover {
        background-color: #B01419;
    }

    /* Expanders - Minimal */
    .streamlit-expanderHeader {
        background-color: #F8F9FA;
        border: 1px solid #DEE2E6;
        color: #495057 !important;
        font-weight: 400;
        font-size: 0.9rem;
        padding: 0.75rem 1rem;
    }

    .streamlit-expanderHeader:hover {
        background-color: #E9ECEF;
    }

    /* Force all text in expander to be dark */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader *  {
        color: #495057 !important;
    }

    .streamlit-expanderContent {
        border: 1px solid #DEE2E6;
        border-top: none;
        background-color: #FFFFFF;
        padding: 1rem;
    }

    /* Info boxes - Subtle */
    .element-container .stAlert {
        background-color: #F8F9FA;
        border-left: 3px solid #6C757D;
        color: #495057;
        font-size: 0.875rem;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }

    div[data-baseweb="notification"] {
        background-color: #E7F3FF;
        border-left: 3px solid #0066CC;
    }

    /* Success */
    .stSuccess {
        background-color: #D4EDDA !important;
        border-left-color: #28A745 !important;
        color: #155724 !important;
    }

    /* Forms */
    .stTextArea textarea {
        background-color: #FFFFFF;
        border: 1px solid #CED4DA;
        color: #495057;
        font-size: 0.875rem;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2.5rem 0 1.5rem 0;
        color: #ADB5BD;
        font-size: 0.8rem;
        margin-top: 4rem;
        border-top: 1px solid #E9ECEF;
    }

    .footer-brand {
        color: #495057;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Section headers */
    .section-header {
        color: #212529;
        font-weight: 500;
        font-size: 0.95rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E9ECEF;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["gcp_service_account"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")
        return None

# Password
def check_password():
    CORRECT_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates Dashboard")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if hashlib.sha256(password.encode()).hexdigest() == CORRECT_PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.info("Default password: admin")
        return False
    return True

# Fetch data
@st.cache_data(ttl=10)
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

# Submit update
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

# ENGINEER VIEW
def engineer_view():
    st.title("Long Call Updates")
    st.markdown("<p class='subtitle'>Your Personal Call History</p>", unsafe_allow_html=True)

    params = st.query_params
    engineer = params.get("engineer", None)

    if not engineer:
        st.info("Enter your Siebel ID")
        engineer = st.text_input("Siebel ID", placeholder="kristinamajasa")
        if st.button("Access Dashboard", use_container_width=True):
            if engineer:
                st.query_params["engineer"] = engineer
                st.rerun()
        return

    st.success(f"Logged in as: {engineer}")

    df = get_updates()
    if df.empty:
        st.warning("No data found")
        return

    my_data = df[df['engineer'] == engineer]
    if my_data.empty:
        st.info("No updates yet")
        return

    tab1, tab2 = st.tabs(["Active Calls", "History"])

    with tab1:
        st.markdown("<div class='section-header'>Active Calls</div>", unsafe_allow_html=True)

        one_hr = datetime.now(MANILA_TZ) - timedelta(hours=1)
        active = {}

        for tid in my_data['transactionId'].unique():
            tid_data = my_data[my_data['transactionId'] == tid].sort_values('timestamp')
            if tid_data.iloc[-1]['timestamp'] > one_hr:
                active[tid] = tid_data

        if active:
            for tid, data in active.items():
                first = data.iloc[0]

                st.markdown(f"**Transaction ID:** {tid}")
                st.markdown(f"**Duration:** {int((data.iloc[-1]['timestamp'] - first['timestamp']).total_seconds() / 60)}m • **Updates:** {len(data)}")

                st.markdown("**Timeline:**")
                for _, upd in data.iterrows():
                    t = upd['timestamp'].strftime('%I:%M %p')
                    if upd.get('updateType') == 'initial':
                        st.info(f"**{t} - Initial Update**\n\nIssue: {upd.get('issue')}\n\nReason: {upd.get('reason')}")
                    else:
                        st.success(f"**{t} - Progress Update**\n\n{upd.get('updateText')}")

                st.markdown("**Add Update:**")
                with st.form(key=f"f_{tid}"):
                    txt = st.text_area("Update", height=60, label_visibility="collapsed", placeholder="Enter progress update...")
                    if st.form_submit_button("Submit", use_container_width=True):
                        if txt.strip():
                            if submit_update(engineer, tid, txt, first.get('squad'), first.get('skillset')):
                                st.success("Submitted")
                                time.sleep(1)
                                st.rerun()
                st.markdown("---")
        else:
            st.info("No active calls")

    with tab2:
        st.markdown("<div class='section-header'>Call History (Last 7 Days)</div>", unsafe_allow_html=True)

        seven = datetime.now(MANILA_TZ) - timedelta(days=7)
        history = my_data[my_data['timestamp'] > seven]

        if not history.empty:
            for tid in history['transactionId'].unique():
                if tid in active:
                    continue

                tid_data = history[history['transactionId'] == tid].sort_values('timestamp')
                first = tid_data.iloc[0]
                date = first['timestamp'].strftime('%b %d, %Y')

                with st.expander(f"TID: {tid} • {date} • {len(tid_data)} updates"):
                    for _, upd in tid_data.iterrows():
                        t = upd['timestamp'].strftime('%I:%M %p')
                        if upd.get('updateType') == 'initial':
                            st.info(f"**{t}** - {upd.get('issue')}")
                        else:
                            st.success(f"**{t}** - {upd.get('updateText')}")
        else:
            st.info("No history")

    st.markdown("<div class='footer'><span class='footer-brand'>TrendLife</span> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

# SQUAD LEAD VIEW
def squad_lead_view():
    st.title("Long Call Updates Dashboard")
    st.markdown("<p class='subtitle'>Real-time monitoring for extended customer calls</p>", unsafe_allow_html=True)

    # Sidebar filters
    with st.sidebar:
        st.markdown("### FILTERS")

        squad = st.selectbox("Squad", ["All", "Chris", "Judith", "Josh", "Bea"])

        df_all = get_updates()
        engs = ["All"]
        if not df_all.empty and 'engineer' in df_all.columns:
            engs += sorted(df_all['engineer'].unique().tolist())
        eng = st.selectbox("Engineer", engs)

        dates = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"]
        date_range = st.selectbox("Date Range", dates, index=2)

        st.markdown("---")

        auto = st.checkbox("Auto-refresh (5s)", value=True)
        if st.button("Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    df = get_updates()

    if df.empty:
        st.warning("No data available")
        return

    # Apply filters
    filtered = df.copy()

    if squad != "All" and 'squad' in filtered.columns:
        filtered = filtered[filtered['squad'].str.contains(squad, case=False, na=False)]

    if eng != "All" and 'engineer' in filtered.columns:
        filtered = filtered[filtered['engineer'] == eng]

    if 'timestamp' in filtered.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered = filtered[filtered['timestamp'] >= start]
        elif date_range == "Yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered = filtered[(filtered['timestamp'] >= start) & (filtered['timestamp'] < end)]
        elif date_range == "Last 7 Days":
            filtered = filtered[filtered['timestamp'] >= now - timedelta(days=7)]
        elif date_range == "Last 30 Days":
            filtered = filtered[filtered['timestamp'] >= now - timedelta(days=30)]

    # METRICS
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Updates", len(filtered))

    with col2:
        one_hr = datetime.now(MANILA_TZ) - timedelta(hours=1)
        active_count = len(filtered[filtered['timestamp'] > one_hr]) if 'timestamp' in filtered.columns else 0
        st.metric("Active (1hr)", active_count)

    with col3:
        recent = filtered[filtered['timestamp'] > one_hr]['transactionId'].nunique() if 'timestamp' in filtered.columns else 0
        st.metric("Recent Calls", recent)

    # TABS
    tab1, tab2, tab3 = st.tabs(["Overview", "By Engineer", "By Date"])

    with tab1:
        st.markdown("<div class='section-header'>Recent Activities (Last Hour)</div>", unsafe_allow_html=True)

        if 'timestamp' in filtered.columns:
            one_hr = datetime.now(MANILA_TZ) - timedelta(hours=1)
            recent_df = filtered[filtered['timestamp'] > one_hr].head(20)

            if not recent_df.empty:
                table_data = []
                for _, row in recent_df.iterrows():
                    table_data.append({
                        'Time': row['timestamp'].strftime('%I:%M %p'),
                        'Engineer': row.get('engineer', 'Unknown'),
                        'Squad': row.get('squad', 'Unknown'),
                        'TID': row.get('transactionId', 'N/A'),
                        'Type': row.get('updateType', 'initial').upper(),
                        'Details': row.get('updateText' if row.get('updateType') == 'progress' else 'issue', 'N/A')
                    })

                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
            else:
                st.info("No recent activities")

    with tab2:
        st.markdown("<div class='section-header'>Engineers</div>", unsafe_allow_html=True)

        if 'engineer' in filtered.columns:
            for e in sorted(filtered['engineer'].unique()):
                e_data = filtered[filtered['engineer'] == e]
                sq = e_data.iloc[0].get('squad', 'Unknown')
                calls = e_data['transactionId'].nunique()

                with st.expander(f"{e} (Squad {sq}) - {calls} calls"):
                    for tid in e_data['transactionId'].unique():
                        tid_data = e_data[e_data['transactionId'] == tid].sort_values('timestamp')

                        st.markdown(f"**TID: {tid}** • {tid_data.iloc[0]['timestamp'].strftime('%b %d %I:%M %p')} • {len(tid_data)} updates")

                        for _, u in tid_data.iterrows():
                            t = u['timestamp'].strftime('%I:%M %p')
                            if u.get('updateType') == 'initial':
                                st.info(f"**{t}** - {u.get('issue', 'N/A')}")
                            else:
                                st.success(f"**{t}** - {u.get('updateText', 'N/A')}")

                        st.markdown("---")

    with tab3:
        st.markdown("<div class='section-header'>Date History</div>", unsafe_allow_html=True)

        if 'timestamp' in filtered.columns:
            filtered['date'] = filtered['timestamp'].dt.date
            dates = sorted(filtered['date'].unique(), reverse=True)

            for d in dates:
                d_data = filtered[filtered['date'] == d]
                d_str = d.strftime('%B %d, %Y')

                with st.expander(f"{d_str} - {len(d_data)} updates", expanded=(d == dates[0])):
                    for tid in d_data['transactionId'].unique():
                        tid_data = d_data[d_data['transactionId'] == tid].sort_values('timestamp')
                        e = tid_data.iloc[0].get('engineer', 'Unknown')

                        st.markdown(f"**{e}** - TID: {tid}")

                        for _, u in tid_data.iterrows():
                            t = u['timestamp'].strftime('%I:%M %p')
                            if u.get('updateType') == 'initial':
                                st.info(f"{t} - {u.get('issue')}")
                            else:
                                st.success(f"{t} - {u.get('updateText')}")

    st.markdown("<div class='footer'><span class='footer-brand'>TrendLife</span> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

    if auto:
        time.sleep(5)
        st.rerun()

# MAIN
def main():
    if not check_password():
        return

    with st.sidebar:
        st.markdown("### VIEW")

        view = st.radio("Select", ["Squad Lead View", "Engineer View"], label_visibility="collapsed")

        params = st.query_params
        curr = params.get("view", "squad")
        new = "engineer" if "Engineer" in view else "squad"

        if new != curr:
            st.query_params["view"] = new
            st.rerun()

    v = st.query_params.get("view", "squad")

    if v == "engineer":
        engineer_view()
    else:
        squad_lead_view()

if __name__ == "__main__":
    main()
