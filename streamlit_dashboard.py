"""
Long Call Update Dashboard - Fixed Icon Sidebar
Using Streamlit's native sidebar styled as icon navigation
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

# CSS for icon-style sidebar
st.markdown("""
<style>
    /* Style sidebar as icon navigation */
    [data-testid="stSidebar"] {
        width: 70px !important;
        min-width: 70px !important;
        max-width: 70px !important;
        background-color: #FAFBFC !important;
        border-right: 2px solid #E1E4E8 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 70px !important;
        padding: 15px 0 !important;
    }

    /* Hide sidebar collapse button */
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    /* Sidebar content */
    [data-testid="stSidebar"] .element-container {
        display: flex;
        justify-content: center;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Logo area */
    .sidebar-logo {
        width: 50px;
        height: 50px;
        margin: 0 auto 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .sidebar-logo img {
        width: 50px;
        height: 50px;
        border-radius: 10px;
    }

    /* Icon buttons */
    [data-testid="stSidebar"] .stButton {
        width: 100%;
        margin: 4px 0 !important;
    }

    [data-testid="stSidebar"] .stButton button {
        width: 60px !important;
        height: 55px !important;
        font-size: 24px !important;
        background-color: transparent !important;
        border: none !important;
        color: #6C757D !important;
        border-radius: 10px !important;
        padding: 0 !important;
        margin: 0 auto !important;
        transition: all 0.2s !important;
    }

    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #E9ECEF !important;
        color: #D71921 !important;
    }

    /* Active state - handled by key checking */
    button[data-baseweb="button"].active-nav {
        background-color: #FFE5E7 !important;
        color: #D71921 !important;
        border-left: 4px solid #D71921 !important;
    }

    /* Main content */
    .main {
        background-color: #F0F2F5;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Red bordered sections */
    .red-box {
        background-color: #FFFFFF;
        border: 3px solid #D71921;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
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
        color: #24292E;
        margin-bottom: 0.5rem;
    }

    .box-subtitle {
        font-size: 0.85rem;
        color: #6C757D;
        margin-bottom: 1.25rem;
    }

    /* Typography */
    h1 {
        color: #D71921 !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.3rem !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: #24292E !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #6C757D !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.7rem !important;
    }

    /* Update items */
    .update-item {
        background-color: #E7F5EC;
        border-left: 4px solid #28A745;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        border-radius: 6px;
    }

    /* Timer */
    .timer-box {
        background: linear-gradient(135deg, #FFF5F5, #FFE5E7);
        border: 2px solid #D71921;
        border-radius: 12px;
        padding: 2rem 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }

    .timer-value {
        font-size: 3.5rem;
        font-weight: 700;
        color: #D71921;
        font-family: monospace;
    }

    /* Tables */
    .dataframe {
        font-size: 0.85rem !important;
    }

    .dataframe thead th {
        background-color: #F6F8FA !important;
        color: #24292E !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F6F8FA !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #E1E4E8;
        color: #24292E !important;
        font-weight: 500;
    }

    .streamlit-expanderHeader * {
        color: #24292E !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #F6F8FA;
    }

    /* Logout button */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 600;
        border-radius: 8px;
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

        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username", placeholder="judith")
            password = st.text_input("Password", type="password")

            if st.button("Login", use_container_width=True):
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

def create_mini_chart(values):
    """Mini trend bar chart"""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(range(len(values))),
        y=values,
        marker=dict(color='#0F6466', opacity=0.6),
        hoverinfo='skip'
    ))

    fig.update_layout(
        height=50,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def create_donut(data_dict):
    """Donut chart for duration breakdown"""
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    colors = ['#0F6466', '#6FB86F', '#FFD166', '#4A90E2']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.65,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside'
    )])

    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(size=9)),
        annotations=[dict(
            text=f'<b>{sum(values)}m</b><br><span style="font-size:10px;">TOTAL</span>',
            x=0.5, y=0.5,
            font=dict(size=20, color='#D71921'),
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

    # Two column layout
    left_col, right_col = st.columns([2.5, 1.5])

    # LEFT: Real-Time Updates
    with left_col:
        st.markdown("<div class='red-box' style='height:550px;overflow-y:auto;'>", unsafe_allow_html=True)
        st.markdown("<div class='box-title'>Real-Time Updates</div>", unsafe_allow_html=True)
        st.markdown("<div class='box-subtitle'>Live activity feed from all engineers</div>", unsafe_allow_html=True)

        recent = df.head(20)
        for _, row in recent.iterrows():
            t = row['timestamp'].strftime('%I:%M %p')
            eng = row.get('engineer', 'Unknown')
            tid = row.get('transactionId', 'N/A')
            action = "started call" if row.get('updateType') == 'initial' else "posted update"

            st.markdown(f"""
            <div class="update-item">
                <div style="font-weight:600;">🟢 {t} - {eng} {action}</div>
                <div style="font-size:0.85rem;color:#6C757D;margin-top:0.25rem;">TID: {tid}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT: Stacked boxes
    with right_col:
        # Longest Call
        st.markdown("<div class='red-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-title'>Longest Call Running</div>", unsafe_allow_html=True)

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
                    longest_eng = tid_data.iloc[0].get('engineer', 'Unknown')
                    longest_tid = tid

            if longest_eng:
                h = int(longest / 3600)
                m = int((longest % 3600) / 60)
                s = int(longest % 60)
                timer = f"{h}h {m}m {s}s" if h > 0 else f"{m}m {s}s"

                st.markdown(f"""
                <div class="timer-box">
                    <div class="timer-value">{timer}</div>
                    <div style="font-size:0.75rem;color:#6C757D;margin-top:0.75rem;">LIVE TIMER</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Engineer:** {longest_eng}")
                st.markdown(f"**TID:** {longest_tid}")

                time.sleep(1)
                st.rerun()
        else:
            st.info("No active calls")

        st.markdown("<hr style='margin:1.5rem 0;border-color:#E9ECEF;'>", unsafe_allow_html=True)

        # Comparison
        st.markdown("<div style='font-size:0.95rem;font-weight:600;margin-bottom:0.75rem;'>Update Activity Comparison</div>", unsafe_allow_html=True)

        if 'engineer' in today_df.columns and 'updateType' in today_df.columns:
            comp = []
            for eng in today_df['engineer'].unique():
                eng_data = today_df[today_df['engineer'] == eng]
                initial = len(eng_data[eng_data['updateType'] == 'initial'])
                progress = len(eng_data[eng_data['updateType'] == 'progress'])
                comp.append({'Engineer': eng, 'Initial': initial, 'Progress': progress})

            if comp:
                st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True, height=120)

        st.markdown("</div>", unsafe_allow_html=True)

        # Combined Duration with Donut
        st.markdown("<div class='red-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-title'>Total Combined Duration</div>", unsafe_allow_html=True)

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
            st.markdown(f"<div style='text-align:center;padding:2rem;'><div style='font-size:3.5rem;font-weight:700;color:#D71921;'>{total}m</div></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Metrics with mini charts
    st.markdown("<div class='light-box'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem;font-weight:600;color:#6C757D;margin-bottom:1.5rem;'>📊 TODAY'S METRICS</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Get 7-day data for trends
    trends = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0)
        day_end = day + timedelta(days=1)
        if 'timestamp' in df.columns:
            day_df = df[(df['timestamp'] >= day) & (df['timestamp'] < day_end)]
            trends.append(day_df)
        else:
            trends.append(pd.DataFrame())

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

    st.markdown("</div>", unsafe_allow_html=True)

def squad_view(df):
    st.title("View by Squad")

    selected = st.selectbox("Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search Engineer")

    if df.empty:
        return

    filtered = df[df['squad'].str.contains(selected, case=False, na=False)] if 'squad' in df.columns else df

    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    st.markdown(f"### Squad {selected}")

    for eng in sorted(filtered['engineer'].unique()):
        with st.expander(f"{eng} - {filtered[filtered['engineer']==eng]['transactionId'].nunique()} calls"):
            eng_data = filtered[filtered['engineer'] == eng]
            for tid in eng_data['transactionId'].unique():
                st.markdown(f"**TID: {tid}**")
                tid_data = eng_data[eng_data['transactionId'] == tid]
                for _, upd in tid_data.iterrows():
                    st.info(upd.get('issue') if upd.get('updateType')=='initial' else upd.get('updateText'))

def engineer_view(df):
    st.title("View by Engineer")

    if df.empty:
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
        return

    if 'timestamp' in df.columns:
        df['date'] = df['timestamp'].dt.date
        for d in sorted(df['date'].unique(), reverse=True):
            d_data = df[df['date'] == d]
            with st.expander(f"{d.strftime('%B %d, %Y')} - {len(d_data)} updates"):
                for _, upd in d_data.iterrows():
                    st.info(f"{upd['timestamp'].strftime('%I:%M %p')} - {upd.get('engineer')} - {upd.get('issue') if upd.get('updateType')=='initial' else upd.get('updateText')}")

def main():
    if not check_login():
        return

    # Initialize page
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    # SIDEBAR: Icon navigation
    with st.sidebar:
        # Logo
        try:
            with open('/home/kristinamajasa/Long Call Update v1.0/icons/icon48.png', 'rb') as f:
                icon_b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<div class="sidebar-logo"><img src="data:image/png;base64,{icon_b64}"/></div>', unsafe_allow_html=True)
        except:
            st.markdown('<div class="sidebar-logo"><div style="width:50px;height:50px;background:#6C757D;border-radius:10px;color:white;display:flex;align-items:center;justify-content:center;font-weight:700;">TL</div></div>', unsafe_allow_html=True)

        # Navigation icons
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

    # Logout in main area
    col1, col2 = st.columns([7, 1])
    with col2:
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # Get data
    df = get_updates()

    # Route to page
    page = st.session_state.page

    if page == 'squad':
        squad_view(df)
    elif page == 'engineer':
        engineer_view(df)
    elif page == 'history':
        history_view(df)
    else:
        home_view(df)

    st.markdown("<div style='text-align:center;padding:2rem;color:#959DA5;font-size:0.8rem;border-top:1px solid #E9ECEF;margin-top:2rem;'><b style='color:#24292E;'>TrendLife</b> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
