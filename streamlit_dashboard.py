"""
Long Call Update Dashboard - Clean Professional Design
Matches extension UI - White/Red/Gray palette only
Two views: Engineer's Personal & Squad Lead's Team Dashboard
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

# Custom CSS - Clean professional design
st.markdown("""
<style>
    /* Clean white background */
    .main {
        background-color: #FFFFFF;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #F8F9FA;
    }

    /* Headers - Trend Micro Red */
    h1 {
        color: #D71921 !important;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }

    h2 {
        color: #212529 !important;
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E9ECEF;
    }

    h3, h4, h5 {
        color: #495057 !important;
        font-weight: 500;
    }

    /* Remove default emoji margins */
    p {
        line-height: 1.6;
    }

    /* Metrics - Clean cards */
    [data-testid="metric-container"] {
        background-color: #FFFFFF;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #DEE2E6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: 700;
        color: #D71921;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        color: #6C757D;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Tabs - Clean professional */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: transparent;
        border-bottom: 1px solid #DEE2E6;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        color: #6C757D;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border-bottom: 2px solid transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background-color: #F8F9FA;
        color: #D71921;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #D71921;
        border-bottom: 2px solid #D71921;
        font-weight: 600;
    }

    /* Tables - Professional */
    .dataframe {
        border: 1px solid #DEE2E6 !important;
        border-radius: 6px;
        overflow: hidden;
    }

    .dataframe thead tr th {
        background-color: #F8F9FA !important;
        color: #495057 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
        padding: 0.75rem !important;
        border-bottom: 2px solid #DEE2E6 !important;
    }

    .dataframe tbody tr td {
        padding: 0.75rem !important;
        border-bottom: 1px solid #F1F3F5 !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F8F9FA !important;
    }

    /* Sidebar - Clean */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E9ECEF;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #212529 !important;
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 1.5rem;
    }

    /* Radio buttons - Clean */
    .stRadio > label {
        font-weight: 500;
        color: #495057;
    }

    [data-baseweb="radio"] {
        background-color: #FFFFFF;
    }

    /* Select boxes - Clean */
    [data-baseweb="select"] {
        background-color: #FFFFFF;
        border-radius: 6px;
    }

    /* Buttons - Trend Micro style */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        padding: 0.625rem 1.5rem;
        width: 100%;
        transition: all 0.2s;
    }

    .stButton button:hover {
        background-color: #B01419;
        box-shadow: 0 2px 8px rgba(215, 25, 33, 0.25);
        transform: translateY(-1px);
    }

    /* Expanders - Clean collapsible */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        border-radius: 6px;
        font-weight: 500;
        color: #212529;
        padding: 0.875rem 1rem;
        font-size: 0.9rem;
    }

    .streamlit-expanderHeader:hover {
        background-color: #F8F9FA;
        border-color: #ADB5BD;
    }

    .streamlit-expanderContent {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 1rem;
    }

    /* Info/Alert boxes - Subtle */
    [data-baseweb="notification"] {
        background-color: #F8F9FA;
        border: 1px solid #DEE2E6;
        border-left: 3px solid #6C757D;
        border-radius: 6px;
        padding: 0.875rem;
    }

    .stSuccess {
        background-color: #D4EDDA !important;
        border-left-color: #28A745 !important;
        color: #155724;
    }

    .stInfo {
        background-color: #D1ECF1 !important;
        border-left-color: #17A2B8 !important;
        color: #0C5460;
    }

    .stWarning {
        background-color: #FFF3CD !important;
        border-left-color: #FFC107 !important;
        color: #856404;
    }

    .stError {
        background-color: #F8D7DA !important;
        border-left-color: #DC3545 !important;
        color: #721C24;
    }

    /* Form elements */
    .stTextInput input,
    .stTextArea textarea {
        background-color: #FFFFFF;
        border: 1px solid #CED4DA;
        border-radius: 6px;
        color: #495057;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: #D71921;
        box-shadow: 0 0 0 0.2rem rgba(215, 25, 33, 0.15);
    }

    /* Dividers */
    hr {
        margin: 2rem 0;
        border-color: #E9ECEF;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #6C757D;
        font-size: 0.875rem;
        border-top: 1px solid #E9ECEF;
        margin-top: 3rem;
    }

    .footer-brand {
        font-weight: 700;
        color: #212529;
        font-size: 1rem;
    }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.7rem;
        font-weight: 600;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 3px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }

    .badge-active {
        background-color: #D4EDDA;
        color: #155724;
    }

    .badge-resolved {
        background-color: #E2E3E5;
        color: #383D41;
    }

    .badge-initial {
        background-color: #FFF3CD;
        color: #856404;
    }

    .badge-update {
        background-color: #D1ECF1;
        color: #0C5460;
    }

    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
        st.error(f"Failed to initialize Firebase: {e}")
        return None

# Password protection
def check_password():
    """Simple password protection"""
    CORRECT_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # "admin"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates Dashboard")
        st.markdown("Please enter password to access")

        password = st.text_input("Password", type="password", key="password_input")

        if st.button("Login"):
            if hashlib.sha256(password.encode()).hexdigest() == CORRECT_PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")

        st.info("Default password: admin")
        return False

    return True

# Fetch updates from Firebase
@st.cache_data(ttl=10)
def get_updates():
    """Fetch all updates from Firestore"""
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

        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(MANILA_TZ)

        # Sort by newest first
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)

        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Submit update from dashboard
def submit_update(engineer, tid, update_text, squad, skillset):
    """Submit progress update"""
    try:
        db = init_firebase()
        if not db:
            return False

        data = {
            'timestamp': datetime.now(MANILA_TZ).isoformat(),
            'engineer': engineer,
            'transactionId': tid,
            'squad': squad,
            'skillset': skillset,
            'updateType': 'progress',
            'updateText': update_text,
            'callDuration': 'Unknown'
        }

        db.collection('updates').add(data)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# ============================================
# ENGINEER'S VIEW
# ============================================
def engineer_view():
    """Engineer's personal dashboard"""

    st.title("Long Call Updates")
    st.markdown("Your Personal Call History")

    params = st.query_params
    engineer_siebel = params.get("engineer", None)

    if not engineer_siebel:
        st.info("Enter your Siebel ID to access your dashboard")
        engineer_siebel = st.text_input("Siebel ID", placeholder="e.g., kristinamajasa")

        if st.button("Access Dashboard", use_container_width=True):
            if engineer_siebel:
                st.query_params["engineer"] = engineer_siebel
                st.rerun()
        return

    st.success(f"Logged in as: {engineer_siebel}")

    df = get_updates()

    if df.empty:
        st.warning("No data found")
        return

    my_data = df[df['engineer'] == engineer_siebel].copy()

    if my_data.empty:
        st.info("No updates yet. Send from extension to see them here.")
        return

    # Tabs
    tab1, tab2 = st.tabs(["Active Calls", "History"])

    # ACTIVE CALLS TAB
    with tab1:
        one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)

        active = {}
        for tid in my_data['transactionId'].unique():
            tid_data = my_data[my_data['transactionId'] == tid].sort_values('timestamp')
            if tid_data.iloc[-1]['timestamp'] > one_hour_ago:
                active[tid] = tid_data

        if active:
            for tid, data in active.items():
                first = data.iloc[0]
                latest = data.iloc[-1]

                start_time = first['timestamp'].strftime('%I:%M %p')
                duration = int((latest['timestamp'] - first['timestamp']).total_seconds() / 60)

                st.markdown(f"### Transaction ID: {tid}")
                st.markdown(f"**Started:** {start_time} • **Duration:** {duration}m • **Updates:** {len(data)}")
                st.markdown('<span class="badge badge-active">ACTIVE</span>', unsafe_allow_html=True)

                st.markdown("**Timeline:**")

                for _, upd in data.iterrows():
                    t = upd['timestamp'].strftime('%I:%M %p')
                    utype = upd.get('updateType', 'initial')

                    if utype == 'initial':
                        with st.container():
                            st.markdown(f"**{t} - INITIAL UPDATE**")
                            st.info(f"**Issue:** {upd.get('issue', 'N/A')}\n\n**Reason:** {upd.get('reason', 'N/A')}")
                    else:
                        with st.container():
                            st.markdown(f"**{t} - PROGRESS UPDATE**")
                            st.success(upd.get('updateText', 'N/A'))

                # Add update form
                st.markdown("**Add Progress Update:**")
                with st.form(key=f"form_{tid}"):
                    new_text = st.text_area("Update", placeholder="Enter progress update...", height=80, label_visibility="collapsed")
                    if st.form_submit_button("Submit Update", use_container_width=True):
                        if new_text.strip():
                            if submit_update(engineer_siebel, tid, new_text, first.get('squad'), first.get('skillset')):
                                st.success("Update submitted")
                                time.sleep(1)
                                st.rerun()

                st.markdown("---")
        else:
            st.info("No active calls")

    # HISTORY TAB
    with tab2:
        seven_days = datetime.now(MANILA_TZ) - timedelta(days=7)
        history = my_data[my_data['timestamp'] > seven_days]

        if not history.empty:
            for tid in history['transactionId'].unique():
                if tid in active:
                    continue

                tid_data = history[history['transactionId'] == tid].sort_values('timestamp')
                first = tid_data.iloc[0]

                date = first['timestamp'].strftime('%b %d, %Y %I:%M %p')
                duration = "Unknown"
                if len(tid_data) > 1:
                    duration = f"{int((tid_data.iloc[-1]['timestamp'] - first['timestamp']).total_seconds() / 60)}m"

                with st.expander(f"TID: {tid} • {date} • {duration} • {len(tid_data)} updates"):
                    for _, upd in tid_data.iterrows():
                        t = upd['timestamp'].strftime('%I:%M %p')
                        utype = upd.get('updateType', 'initial')

                        if utype == 'initial':
                            st.info(f"**{t} - INITIAL**\n\nIssue: {upd.get('issue')}\n\nReason: {upd.get('reason')}")
                        else:
                            st.success(f"**{t} - UPDATE**\n\n{upd.get('updateText')}")
        else:
            st.info("No history in last 7 days")

    st.markdown("<div class='footer'><span class='footer-brand'>TrendLife</span> | Where intelligence meets care<br>v1.0</div>", unsafe_allow_html=True)

# ============================================
# SQUAD LEAD'S VIEW
# ============================================
def squad_lead_view():
    """Squad Lead's dashboard - clean professional monitoring"""

    st.title("Long Call Updates Dashboard")
    st.markdown("Real-time monitoring for extended customer calls")

    # Sidebar
    with st.sidebar:
        st.markdown("### Filters")

        squad_opts = ["All", "Chris", "Judith", "Josh", "Bea"]
        squad_filter = st.selectbox("Squad", squad_opts)

        df_all = get_updates()
        eng_opts = ["All"]
        if not df_all.empty and 'engineer' in df_all.columns:
            eng_opts += sorted(df_all['engineer'].unique().tolist())

        eng_filter = st.selectbox("Engineer", eng_opts)

        date_opts = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"]
        date_filter = st.selectbox("Date Range", date_opts, index=2)

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

    if squad_filter != "All" and 'squad' in filtered.columns:
        filtered = filtered[filtered['squad'].str.contains(squad_filter, case=False, na=False)]

    if eng_filter != "All" and 'engineer' in filtered.columns:
        filtered = filtered[filtered['engineer'] == eng_filter]

    if 'timestamp' in filtered.columns:
        now = datetime.now(MANILA_TZ)
        if date_filter == "Today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered = filtered[filtered['timestamp'] >= start]
        elif date_filter == "Yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered = filtered[(filtered['timestamp'] >= start) & (filtered['timestamp'] < end)]
        elif date_filter == "Last 7 Days":
            week_ago = now - timedelta(days=7)
            filtered = filtered[filtered['timestamp'] >= week_ago]
        elif date_filter == "Last 30 Days":
            month_ago = now - timedelta(days=30)
            filtered = filtered[filtered['timestamp'] >= month_ago]

    # METRICS
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Updates", len(filtered))

    with col2:
        one_hr = datetime.now(MANILA_TZ) - timedelta(hours=1)
        active_count = len(filtered[filtered['timestamp'] > one_hr]) if 'timestamp' in filtered.columns else 0
        st.metric("Active (1hr)", active_count)

    with col3:
        recent_calls = filtered[filtered['timestamp'] > one_hr]['transactionId'].nunique() if 'timestamp' in filtered.columns else 0
        st.metric("Recent Calls", recent_calls)

    # TABS
    tab1, tab2, tab3 = st.tabs(["Overview", "By Engineer", "By Date"])

    # OVERVIEW TAB
    with tab1:
        st.markdown("### Recent Activities (Last Hour)")

        if 'timestamp' in filtered.columns:
            one_hr = datetime.now(MANILA_TZ) - timedelta(hours=1)
            recent = filtered[filtered['timestamp'] > one_hr]

            if not recent.empty:
                # Create display dataframe
                display_data = []
                for _, row in recent.head(20).iterrows():
                    display_data.append({
                        'Time': row['timestamp'].strftime('%I:%M %p'),
                        'Engineer': row.get('engineer', 'Unknown'),
                        'Squad': row.get('squad', 'Unknown'),
                        'TID': row.get('transactionId', 'N/A'),
                        'Type': row.get('updateType', 'initial').upper(),
                        'Details': row.get('updateText' if row.get('updateType') == 'progress' else 'issue', 'N/A')[:50] + '...'
                    })

                if display_data:
                    st.dataframe(
                        pd.DataFrame(display_data),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info("No recent activities in the last hour")

    # BY ENGINEER TAB
    with tab2:
        st.markdown("### Engineers")

        if 'engineer' in filtered.columns:
            for eng in sorted(filtered['engineer'].unique()):
                eng_data = filtered[filtered['engineer'] == eng]
                squad = eng_data.iloc[0].get('squad', 'Unknown')
                num_calls = eng_data['transactionId'].nunique()

                with st.expander(f"{eng} (Squad {squad}) - {num_calls} call(s)"):
                    # Group by TID
                    for tid in eng_data['transactionId'].unique():
                        tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')

                        first_time = tid_data.iloc[0]['timestamp'].strftime('%b %d %I:%M %p')
                        st.markdown(f"**TID: {tid}** • {first_time} • {len(tid_data)} updates")

                        for _, upd in tid_data.iterrows():
                            t = upd['timestamp'].strftime('%I:%M %p')
                            utype = upd.get('updateType', 'initial')

                            if utype == 'initial':
                                st.info(f"**{t} - INITIAL**\n\nIssue: {upd.get('issue', 'N/A')}\n\nReason: {upd.get('reason', 'N/A')}")
                            else:
                                st.success(f"**{t} - UPDATE**\n\n{upd.get('updateText', 'N/A')}")

                        st.markdown("---")

    # BY DATE TAB
    with tab3:
        st.markdown("### Date History")

        if 'timestamp' in filtered.columns:
            filtered['date'] = filtered['timestamp'].dt.date
            dates = sorted(filtered['date'].unique(), reverse=True)

            for date in dates:
                date_data = filtered[filtered['date'] == date]
                date_str = date.strftime('%B %d, %Y')

                with st.expander(f"{date_str} - {len(date_data)} updates", expanded=(date == dates[0])):
                    # Show updates for this date
                    for tid in date_data['transactionId'].unique():
                        tid_data = date_data[date_data['transactionId'] == tid].sort_values('timestamp')
                        eng = tid_data.iloc[0].get('engineer', 'Unknown')

                        st.markdown(f"**{eng}** - TID: {tid} - {len(tid_data)} updates")

                        for _, upd in tid_data.iterrows():
                            t = upd['timestamp'].strftime('%I:%M %p')
                            utype = upd.get('updateType', 'initial')

                            if utype == 'initial':
                                st.info(f"{t} - INITIAL: {upd.get('issue', 'N/A')}")
                            else:
                                st.success(f"{t} - UPDATE: {upd.get('updateText', 'N/A')}")

                        st.markdown("---")

    st.markdown("<div class='footer'><span class='footer-brand'>TrendLife</span> | Where intelligence meets care<br>v1.0</div>", unsafe_allow_html=True)

    if auto:
        time.sleep(5)
        st.rerun()

# ============================================
# MAIN
# ============================================
def main():
    if not check_password():
        return

    with st.sidebar:
        st.markdown("### View")

        view = st.radio(
            "Select",
            ["Squad Lead View", "Engineer View"],
            label_visibility="collapsed"
        )

        params = st.query_params
        current = params.get("view", "squad")
        new = "engineer" if "Engineer" in view else "squad"

        if new != current:
            st.query_params["view"] = new
            st.rerun()

    params = st.query_params
    v = params.get("view", "squad")

    if v == "engineer":
        engineer_view()
    else:
        squad_lead_view()

if __name__ == "__main__":
    main()
