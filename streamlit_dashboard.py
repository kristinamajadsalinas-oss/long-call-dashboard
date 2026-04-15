"""
Long Call Update Dashboard - Using Streamlit Containers
Proper rendering with visual borders
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib
import time
import plotly.graph_objects as go
import base64

MANILA_TZ = pytz.timezone('Asia/Manila')
SQUAD_LEADS = ["chris", "judith", "josh", "bea"]

st.set_page_config(
    page_title="Long Call Updates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    /* Sidebar as icon nav */
    [data-testid="stSidebar"] {
        width: 70px !important;
        min-width: 70px !important;
        max-width: 70px !important;
        background-color: #FAFBFC !important;
        border-right: 2px solid #E1E4E8 !important;
    }

    [data-testid="stSidebar"] > div {
        width: 70px !important;
        padding: 15px 0 !important;
    }

    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Icon buttons */
    [data-testid="stSidebar"] .stButton button {
        width: 60px !important;
        height: 55px !important;
        font-size: 24px !important;
        background-color: transparent !important;
        border: none !important;
        color: #6C757D !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #E9ECEF !important;
        color: #D71921 !important;
    }

    /* Main area */
    .main {
        background-color: #F0F2F5;
    }

    .block-container {
        padding-top: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Container styling for red borders */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background-color: #FFFFFF;
        border: 3px solid #D71921;
        border-radius: 12px;
        padding: 1.5rem;
    }

    /* Typography */
    h1 {
        color: #D71921 !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
    }

    h2 {
        color: #24292E !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
    }

    h3 {
        color: #6C757D !important;
        font-size: 0.85rem !important;
        font-weight: 400 !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #D71921 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #6C757D !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
    }

    /* Info boxes */
    .stAlert {
        background-color: #E7F5EC;
        border-left: 4px solid #28A745;
        color: #24292E;
        font-size: 0.9rem;
    }

    /* Tables */
    .dataframe thead th {
        background-color: #F6F8FA !important;
        color: #24292E !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F6F8FA !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #E1E4E8;
        color: #24292E !important;
    }

    .streamlit-expanderHeader * {
        color: #24292E !important;
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

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates Dashboard")

        username = st.text_input("Username", placeholder="judith")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if password and hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH:
                if username.strip() and username.lower() in SQUAD_LEADS:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("Access denied")
            else:
                st.error("Incorrect password")

        st.info("Password: admin")
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

def create_donut(data_dict):
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    colors = ['#0F6466', '#6FB86F', '#FFD166', '#4A90E2']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.65,
        marker=dict(colors=colors),
        textinfo='label+percent',
        hovertemplate='%{label}: %{value}m<extra></extra>'
    )])

    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=9)),
        annotations=[dict(
            text=f'<b>{sum(values)}m</b>',
            x=0.5, y=0.5,
            font=dict(size=28, color='#D71921'),
            showarrow=False
        )]
    )

    return fig

def home_view(df):
    st.title("Dashboard Overview")
    st.caption("Good morning, Here's what's going on today")

    if df.empty:
        st.warning("No data")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # Layout
    left_col, right_col = st.columns([2.5, 1.5])

    # LEFT: Real-Time Updates
    with left_col:
        with st.container(border=True):
            st.markdown("### Real-Time Updates")
            st.caption("Live activity feed from all engineers")

            recent = df.head(15)
            if not recent.empty:
                for _, row in recent.iterrows():
                    t = row['timestamp'].strftime('%I:%M %p')
                    eng = row.get('engineer', 'Unknown')
                    tid = row.get('transactionId', 'N/A')
                    action = "started call" if row.get('updateType') == 'initial' else "posted update"

                    st.info(f"🟢 **{t}** - {eng} {action}\n\nTID: {tid}")
            else:
                st.info("No recent updates")

    # RIGHT: Stacked
    with right_col:
        # Longest Call
        with st.container(border=True):
            st.markdown("### Longest Call Running")

            active = df[df['timestamp'] > one_hour_ago] if 'timestamp' in df.columns else pd.DataFrame()

            if not active.empty and 'transactionId' in active.columns:
                longest = 0
                longest_eng = None
                longest_tid = None

                for tid in active['transactionId'].unique():
                    tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                    start = tid_data.iloc[0]['timestamp']
                    dur = (now - start).total_seconds()
                    if dur > longest:
                        longest = dur
                        longest_eng = tid_data.iloc[0].get('engineer')
                        longest_tid = tid

                if longest_eng:
                    h = int(longest / 3600)
                    m = int((longest % 3600) / 60)
                    s = int(longest % 60)
                    timer = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

                    st.markdown(f"<div style='text-align:center;background:linear-gradient(135deg,#FFF5F5,#FFE5E7);border:2px solid #D71921;border-radius:10px;padding:1.5rem;margin:1rem 0;'><div style='font-size:3rem;font-weight:700;color:#D71921;font-family:monospace;'>{timer}</div><div style='font-size:0.75rem;color:#6C757D;margin-top:0.5rem;'>LIVE TIMER</div></div>", unsafe_allow_html=True)

                    st.markdown(f"**Engineer:** {longest_eng}")
                    st.markdown(f"**TID:** {longest_tid}")

                    time.sleep(1)
                    st.rerun()
            else:
                st.info("No active calls")

            st.markdown("---")

            st.markdown("#### Update Activity Comparison")
            if 'engineer' in today_df.columns:
                comp = []
                for eng in today_df['engineer'].unique():
                    eng_data = today_df[today_df['engineer'] == eng]
                    initial = len(eng_data[eng_data['updateType'] == 'initial'])
                    progress = len(eng_data[eng_data['updateType'] == 'progress'])
                    comp.append({'Engineer': eng, 'Initial': initial, 'Progress': progress})

                if comp:
                    st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)

        # Combined Duration
        with st.container(border=True):
            st.markdown("### Total Combined Duration")

            squad_dur = {}
            total = 0

            if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                    if len(tid_data) > 0:
                        mins = int((tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60)
                        total += mins
                        squad = tid_data.iloc[0].get('squad', 'Unknown')
                        squad_dur[squad] = squad_dur.get(squad, 0) + mins

            if squad_dur:
                fig = create_donut(squad_dur)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown(f"<div style='text-align:center;padding:2rem;'><div style='font-size:3.5rem;font-weight:700;color:#D71921;'>{total}m</div><div style='font-size:0.85rem;color:#6C757D;margin-top:0.5rem;'>Sum of all durations today</div></div>", unsafe_allow_html=True)

    # Metrics
    with st.container(border=True):
        st.caption("📊 TODAY'S METRICS")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cases = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
            st.metric("Cases Today", cases)

        with col2:
            active_cnt = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
            st.metric("Active (Live)", active_cnt)

        with col3:
            ended = 0
            if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    last = df[df['transactionId'] == tid]['timestamp'].max()
                    if last < one_hour_ago:
                        ended += 1
            st.metric("Ended Calls", ended)

        with col4:
            over = 0
            if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                    if len(tid_data) > 0 and (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60 >= 60:
                        over += 1
            st.metric(">1hr Calls", over)

def squad_view(df):
    st.title("View by Squad")

    selected = st.selectbox("Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search Engineer")

    if df.empty:
        st.warning("No data")
        return

    filtered = df[df['squad'].str.contains(selected, case=False, na=False)] if 'squad' in df.columns else df

    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    st.markdown(f"### Squad {selected}")

    for eng in sorted(filtered['engineer'].unique()) if 'engineer' in filtered.columns else []:
        eng_data = filtered[filtered['engineer'] == eng]
        with st.expander(f"{eng} - {eng_data['transactionId'].nunique()} calls"):
            for tid in eng_data['transactionId'].unique():
                tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
                st.markdown(f"**TID: {tid}**")
                for _, upd in tid_data.iterrows():
                    st.info(upd.get('issue') if upd.get('updateType')=='initial' else upd.get('updateText'))

def engineer_view(df):
    st.title("View by Engineer")

    if df.empty:
        st.warning("No data")
        return

    engineers = sorted(df['engineer'].unique()) if 'engineer' in df.columns else []
    selected = st.selectbox("Engineer", engineers) if engineers else None

    if selected:
        eng_data = df[df['engineer'] == selected]
        st.markdown(f"### {selected} - {eng_data['transactionId'].nunique()} calls")

        for tid in eng_data['transactionId'].unique():
            tid_data = eng_data[eng_data['transactionId'] == tid]
            with st.expander(f"TID: {tid} - {len(tid_data)} updates"):
                for _, upd in tid_data.iterrows():
                    st.info(upd.get('issue') if upd.get('updateType')=='initial' else upd.get('updateText'))

def history_view(df):
    st.title("History")

    if df.empty:
        st.warning("No data")
        return

    if 'timestamp' in df.columns:
        df['date'] = df['timestamp'].dt.date
        for d in sorted(df['date'].unique(), reverse=True):
            d_data = df[df['date'] == d]
            with st.expander(f"{d.strftime('%B %d, %Y')} - {len(d_data)} updates"):
                for _, upd in d_data.iterrows():
                    st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {upd.get('engineer')} - TID: {upd.get('transactionId')}")

def main():
    if not check_login():
        return

    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    # Sidebar navigation
    with st.sidebar:
        # Try multiple paths for the icon
        icon_loaded = False

        icon_paths = [
            '/home/kristinamajasa/Long Call Update v1.0/icons/icon48.png',
            '/mnt/c/Users/kristinamajas/Documents/Long Call Update Versions/Long Call Update v1.0/icons/icon48.png',
            'icons/icon48.png'
        ]

        for path in icon_paths:
            try:
                with open(path, 'rb') as f:
                    icon_data = f.read()
                    st.image(icon_data, width=50)
                    icon_loaded = True
                    break
            except:
                continue

        if not icon_loaded:
            st.markdown('<div style="width:50px;height:50px;background:#808080;border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:16px;">TL</div>', unsafe_allow_html=True)

        st.markdown("##")

        if st.button("🏠", key="home", help="Home"):
            st.session_state.page = 'home'
            st.rerun()

        if st.button("👥", key="squad", help="Squad"):
            st.session_state.page = 'squad'
            st.rerun()

        if st.button("👤", key="engineer", help="Engineer"):
            st.session_state.page = 'engineer'
            st.rerun()

        if st.button("📅", key="history", help="History"):
            st.session_state.page = 'history'
            st.rerun()

        # Logout at bottom of sidebar
        st.markdown("---")
        if st.button("Logout", key="logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    df = get_updates()

    # Route
    page = st.session_state.page

    if page == 'squad':
        squad_view(df)
    elif page == 'engineer':
        engineer_view(df)
    elif page == 'history':
        history_view(df)
    else:
        home_view(df)

    st.markdown("<div style='text-align:center;padding:2rem;color:#959DA5;border-top:1px solid #E9ECEF;'><b>TrendLife</b> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
