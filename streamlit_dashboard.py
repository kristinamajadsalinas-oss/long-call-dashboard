"""
Long Call Update Dashboard - With Charts & Visualizations
Professional design matching reference with all visual elements
Squad Lead view only (Engineer view to be built separately)
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib
import time
import plotly.express as px
import plotly.graph_objects as go
import base64

MANILA_TZ = pytz.timezone('Asia/Manila')
SQUAD_LEADS = ["chris", "judith", "josh", "bea"]

st.set_page_config(
    page_title="Long Call Updates",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Enhanced CSS with proper layout
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}

    .main {
        background-color: #F0F2F5;
        padding: 0;
        margin: 0;
    }

    /* Icon sidebar - fixed position */
    .icon-sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 70px;
        background-color: #FAFBFC;
        border-right: 2px solid #E1E4E8;
        z-index: 1000;
        padding: 20px 0;
        box-shadow: 2px 0 8px rgba(0,0,0,0.04);
    }

    .sidebar-logo {
        width: 70px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 25px;
    }

    .sidebar-logo img {
        width: 50px;
        height: 50px;
        border-radius: 10px;
    }

    .sidebar-icon {
        width: 70px;
        height: 55px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 26px;
        margin: 8px 0;
        border-radius: 10px;
        transition: all 0.2s;
        filter: grayscale(100%);
        opacity: 0.5;
    }

    .sidebar-icon:hover {
        background-color: #E1E4E8;
        opacity: 0.8;
    }

    .sidebar-icon.active {
        background-color: #FFE5E7;
        filter: grayscale(0%);
        opacity: 1;
        border-left: 4px solid #D71921;
    }

    /* Main content area */
    .block-container {
        padding-left: 90px !important;
        padding-top: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Red bordered boxes */
    .red-border-box {
        background-color: #FFFFFF;
        border: 3px solid #D71921;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        min-height: 200px;
    }

    .light-border-box {
        background-color: #F8F9FA;
        border: 2px solid #DEE2E6;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .box-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #24292E;
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .box-subtitle {
        font-size: 0.85rem;
        color: #6C757D;
        margin-bottom: 1.5rem;
    }

    /* Page title */
    h1 {
        color: #D71921 !important;
        font-weight: 700 !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.3rem !important;
    }

    .page-subtitle {
        color: #6C757D;
        font-size: 0.95rem;
        margin-bottom: 2rem;
    }

    /* Metrics with mini charts */
    [data-testid="metric-container"] {
        background-color: transparent;
        padding: 0.75rem;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        color: #6C757D !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #24292E !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
        color: #6C757D !important;
    }

    /* Update feed items */
    .update-item {
        background-color: #E7F5EC;
        border-left: 4px solid #28A745;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        border-radius: 6px;
        font-size: 0.9rem;
    }

    .update-time {
        font-weight: 600;
        color: #24292E;
    }

    .update-details {
        font-size: 0.85rem;
        color: #6C757D;
        margin-top: 0.25rem;
    }

    /* Timer display */
    .timer-display {
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
        font-family: 'Courier New', monospace;
        line-height: 1;
    }

    .timer-label {
        font-size: 0.75rem;
        color: #6C757D;
        margin-top: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Tables */
    .dataframe {
        font-size: 0.85rem !important;
        border: none !important;
    }

    .dataframe thead th {
        background-color: #F6F8FA !important;
        color: #24292E !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        padding: 0.75rem !important;
        border-bottom: 2px solid #E1E4E8 !important;
    }

    .dataframe tbody td {
        padding: 0.75rem !important;
        border-bottom: 1px solid #F1F3F5 !important;
    }

    .dataframe tbody tr:hover {
        background-color: #F6F8FA !important;
    }

    /* Buttons */
    .stButton button {
        background-color: #D71921;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        border: none;
    }

    .stButton button:hover {
        background-color: #B01419;
        box-shadow: 0 2px 8px rgba(215, 25, 33, 0.3);
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #E1E4E8;
        color: #24292E !important;
        font-weight: 500;
        padding: 0.875rem 1rem;
        border-radius: 6px;
    }

    .streamlit-expanderHeader * {
        color: #24292E !important;
    }

    .streamlit-expanderHeader:hover {
        background-color: #F6F8FA;
        border-color: #ADB5BD;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer {visibility: hidden;}

    /* Plotly charts - clean */
    .js-plotly-plot {
        border-radius: 8px;
    }
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
        st.error(f"Firebase initialization failed: {e}")
        return None

def check_login():
    PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None

    if not st.session_state.authenticated:
        st.markdown("## Long Call Updates Dashboard")
        st.markdown("Squad Lead Access")

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
                            st.session_state.current_page = "home"
                            st.rerun()
                        else:
                            st.error("Access denied. Squad leads only.")
                    else:
                        st.error("Enter username")
                else:
                    st.error("Incorrect password")

            st.info("Password: admin")
            st.caption("Authorized: chris, judith, josh, bea")
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
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def render_sidebar(current_page):
    """Render icon sidebar with real TrendLife logo"""

    # Try to load actual icon
    icon_html = '<div style="width:50px;height:50px;background:#6C757D;border-radius:10px;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:18px;">TL</div>'

    try:
        with open('/home/kristinamajasa/Long Call Update v1.0/icons/icon48.png', 'rb') as f:
            icon_data = base64.b64encode(f.read()).decode()
            icon_html = f'<img src="data:image/png;base64,{icon_data}" style="width:50px;height:50px;border-radius:10px;"/>'
    except:
        pass

    sidebar_html = f"""
    <div class="icon-sidebar">
        <div class="sidebar-logo">{icon_html}</div>

        <div class="sidebar-icon {'active' if current_page == 'home' else ''}" title="Home">
            🏠
        </div>

        <div class="sidebar-icon {'active' if current_page == 'squad' else ''}" title="Squad">
            👥
        </div>

        <div class="sidebar-icon {'active' if current_page == 'engineer' else ''}" title="Engineer">
            👤
        </div>

        <div class="sidebar-icon {'active' if current_page == 'history' else ''}" title="History">
            📅
        </div>
    </div>
    """

    st.markdown(sidebar_html, unsafe_allow_html=True)

def create_mini_trend_chart(values, height=60):
    """Create mini bar chart for metric trends"""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(range(len(values))),
        y=values,
        marker=dict(color='#0F6466', opacity=0.7),
        hoverinfo='y'
    ))

    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x'
    )

    return fig

def create_donut_chart(data_dict):
    """Create donut chart for combined duration breakdown"""
    labels = list(data_dict.keys())
    values = list(data_dict.values())

    colors = ['#0F6466', '#6FB86F', '#FFD166', '#4A90E2']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(colors=colors),
        textinfo='label+value',
        textposition='outside',
        hovertemplate='%{label}<br>%{value}m<extra></extra>'
    )])

    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            font=dict(size=10)
        ),
        annotations=[dict(
            text=f'<b>{sum(values)}m</b><br><span style="font-size:10px;">TOTAL</span>',
            x=0.5, y=0.5,
            font=dict(size=24, color='#D71921'),
            showarrow=False
        )]
    )

    return fig

def home_view(df):
    """HOME view with all visualizations"""

    st.title("Dashboard Overview")
    st.markdown("<div class='page-subtitle'>Good morning, Here's what's going on today</div>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # LAYOUT: Large left box + Right stacked boxes
    left_col, right_col = st.columns([2.5, 1.5])

    # LEFT: Real-Time Updates (Large red box)
    with left_col:
        st.markdown("<div class='red-border-box' style='height:550px;overflow-y:auto;'>", unsafe_allow_html=True)
        st.markdown("<div class='box-header'>Real-Time Updates</div>", unsafe_allow_html=True)
        st.markdown("<div class='box-subtitle'>Live activity feed from all engineers</div>", unsafe_allow_html=True)

        recent = df.head(20)
        if not recent.empty:
            for _, row in recent.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')
                eng = row.get('engineer', 'Unknown')
                tid = row.get('transactionId', 'N/A')
                utype = row.get('updateType', 'initial')
                action = "started call" if utype == 'initial' else "posted update"

                st.markdown(f"""
                <div class="update-item">
                    <div class="update-time">🟢 {t} - {eng} {action}</div>
                    <div class="update-details">TID: {tid}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT COLUMN: Stacked boxes
    with right_col:
        # TOP: Longest Call Running
        st.markdown("<div class='red-border-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-header'>Longest Call Running</div>", unsafe_allow_html=True)

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
                hours = int(longest_dur / 3600)
                mins = int((longest_dur % 3600) / 60)
                secs = int(longest_dur % 60)

                timer_text = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"

                st.markdown(f"""
                <div class="timer-display">
                    <div class="timer-value">{timer_text}</div>
                    <div class="timer-label">Live Timer</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"**Engineer (SIEBEL ID):** {longest_eng}")
                st.markdown(f"**Transaction ID:** {longest_tid}")

                time.sleep(1)
                st.rerun()
        else:
            st.info("No active calls currently")

        st.markdown("<hr style='border-color:#E9ECEF;margin:1.5rem 0;'>", unsafe_allow_html=True)

        # Comparison table
        st.markdown("<div style='font-size:0.95rem;font-weight:600;margin-bottom:1rem;color:#24292E;'>Update Activity Comparison</div>", unsafe_allow_html=True)
        st.caption("Initial Entries vs Progress Updates")

        if 'engineer' in today_df.columns and 'updateType' in today_df.columns:
            comp = []
            for eng in today_df['engineer'].unique():
                eng_data = today_df[today_df['engineer'] == eng]
                initial = len(eng_data[eng_data['updateType'] == 'initial'])
                progress = len(eng_data[eng_data['updateType'] == 'progress'])
                ratio = f"{progress}:{initial}" if initial > 0 else "N/A"
                comp.append({'Engineer': eng, 'Initial': initial, 'Progress': progress, 'Ratio': ratio})

            if comp:
                st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True, height=150)

        st.markdown("</div>", unsafe_allow_html=True)

        # Combined Duration with Donut Chart
        st.markdown("<div class='red-border-box'>", unsafe_allow_html=True)
        st.markdown("<div class='box-header'>Total Combined Duration</div>", unsafe_allow_html=True)

        # Calculate duration by squad
        squad_durations = {}
        total_duration = 0

        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns and 'squad' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    dur_mins = int((tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60)
                    total_duration += dur_mins

                    squad = tid_data.iloc[0].get('squad', 'Unknown')
                    squad_durations[squad] = squad_durations.get(squad, 0) + dur_mins

        if total_duration > 0 and squad_durations:
            # Show donut chart
            fig = create_donut_chart(squad_durations)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.markdown(f"""
            <div style="text-align:center;padding:2rem 0;">
                <div style="font-size:3.5rem;font-weight:700;color:#D71921;">{total_duration}m</div>
                <div style="font-size:0.85rem;color:#6C757D;margin-top:0.5rem;">Sum of all durations today</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # BOTTOM: Metrics with mini charts (Full width)
    st.markdown("<div class='light-border-box'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem;font-weight:600;color:#6C757D;margin-bottom:1.5rem;text-transform:uppercase;letter-spacing:1.5px;'>📊 Today's Metrics</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Calculate 7-day trends for mini charts
    last_7_days = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0)
        day_end = day_start + timedelta(days=1)
        if 'timestamp' in df.columns:
            day_data = df[(df['timestamp'] >= day_start) & (df['timestamp'] < day_end)]
            last_7_days.append(day_data)
        else:
            last_7_days.append(pd.DataFrame())

    with col1:
        cases = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
        trend = [d['transactionId'].nunique() if 'transactionId' in d.columns and not d.empty else 0 for d in last_7_days]
        st.metric("Cases Today", cases, delta=f"vs last week")
        st.plotly_chart(create_mini_trend_chart(trend), use_container_width=True, config={'displayModeBar': False})

    with col2:
        active = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
        active_trend = [len(d[d['timestamp'] > (now - timedelta(days=i, hours=1))]) if 'timestamp' in d.columns and not d.empty else 0 for i, d in enumerate(reversed(last_7_days))]
        st.metric("Active (Live)", active)
        st.plotly_chart(create_mini_trend_chart(active_trend), use_container_width=True, config={'displayModeBar': False})

    with col3:
        ended = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                last = df[df['transactionId'] == tid]['timestamp'].max()
                if last < one_hour_ago:
                    ended += 1
        st.metric("Ended Calls", ended)
        ended_trend = [3, 2, 4, 1, 2, 3, ended]  # Placeholder trend
        st.plotly_chart(create_mini_trend_chart(ended_trend), use_container_width=True, config={'displayModeBar': False})

    with col4:
        over_1hr = 0
        if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
            for tid in today_df['transactionId'].unique():
                tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_data) > 0:
                    dur = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60
                    if dur >= 60:
                        over_1hr += 1
        st.metric(">1hr Calls", over_1hr)
        over_trend = [2, 1, 3, 2, 1, 2, over_1hr]  # Placeholder
        st.plotly_chart(create_mini_trend_chart(over_trend), use_container_width=True, config={'displayModeBar': False})

    st.markdown("</div>", unsafe_allow_html=True)

def squad_view(df):
    st.title("View by Squad")

    selected = st.selectbox("Select Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search Engineer", placeholder="Type engineer name...")
    date_range = st.selectbox("Date Range", ["Today", "Last 7 Days", "Last 30 Days", "All Time"], index=1)

    if df.empty:
        st.warning("No data")
        return

    filtered = df[df['squad'].str.contains(selected, case=False, na=False)] if 'squad' in df.columns else df

    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    st.markdown(f"### Squad {selected}")
    st.markdown(f"**Engineers with updates:** {filtered['engineer'].nunique()}")

    if 'engineer' in filtered.columns:
        for eng in sorted(filtered['engineer'].unique()):
            eng_data = filtered[filtered['engineer'] == eng]
            calls = eng_data['transactionId'].nunique()

            with st.expander(f"{eng} - {calls} call(s)"):
                for tid in eng_data['transactionId'].unique():
                    tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
                    st.markdown(f"**TID: {tid}** - {len(tid_data)} updates")

                    for _, upd in tid_data.iterrows():
                        t = upd['timestamp'].strftime('%I:%M %p')
                        if upd.get('updateType') == 'initial':
                            st.info(f"**{t} - INITIAL**\n\n{upd.get('issue', 'N/A')}")
                        else:
                            st.success(f"**{t} - UPDATE**\n\n{upd.get('updateText', 'N/A')}")

                    st.markdown("---")

def engineer_view(df):
    st.title("View by Engineer")

    if df.empty:
        st.warning("No data")
        return

    engineers = sorted(df['engineer'].unique()) if 'engineer' in df.columns else []
    selected = st.selectbox("Select Engineer", engineers) if engineers else None

    if not selected:
        return

    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "All Time"], index=0)

    eng_data = df[df['engineer'] == selected]

    st.markdown(f"### {selected}")
    st.markdown(f"**Total Calls:** {eng_data['transactionId'].nunique()}")

    # Show calls
    for tid in eng_data['transactionId'].unique():
        tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')
        first_time = tid_data.iloc[0]['timestamp'].strftime('%b %d, %Y %I:%M %p')

        with st.expander(f"TID: {tid} - {first_time} - {len(tid_data)} updates"):
            for _, upd in tid_data.iterrows():
                t = upd['timestamp'].strftime('%I:%M %p')
                if upd.get('updateType') == 'initial':
                    st.info(f"**{t} - INITIAL**\n\nIssue: {upd.get('issue')}\n\nReason: {upd.get('reason')}")
                else:
                    st.success(f"**{t} - UPDATE**\n\n{upd.get('updateText')}")

def history_view(df):
    st.title("History")

    date_range = st.selectbox("Date Range", ["Today", "Last 7 Days", "Last 30 Days", "All Time"], index=1)

    if df.empty:
        st.warning("No data")
        return

    # Apply date filter
    if 'timestamp' in df.columns:
        now = datetime.now(MANILA_TZ)
        if date_range == "Today":
            filtered = df[df['timestamp'] >= now.replace(hour=0, minute=0, second=0)]
        elif date_range == "Last 7 Days":
            filtered = df[df['timestamp'] >= now - timedelta(days=7)]
        elif date_range == "Last 30 Days":
            filtered = df[df['timestamp'] >= now - timedelta(days=30)]
        else:
            filtered = df

        st.markdown(f"**Total Cases in Range:** {filtered['transactionId'].nunique()}")

        # Group by date
        filtered['date'] = filtered['timestamp'].dt.date
        for d in sorted(filtered['date'].unique(), reverse=True):
            d_data = filtered[filtered['date'] == d]
            d_str = d.strftime('%B %d, %Y')

            with st.expander(f"{d_str} - {len(d_data)} updates - {d_data['transactionId'].nunique()} calls"):
                for tid in d_data['transactionId'].unique():
                    tid_data = d_data[d_data['transactionId'] == tid].sort_values('timestamp')
                    eng = tid_data.iloc[0].get('engineer', 'Unknown')

                    st.markdown(f"**{eng}** - TID: {tid}")

                    for _, upd in tid_data.iterrows():
                        t = upd['timestamp'].strftime('%I:%M %p')
                        if upd.get('updateType') == 'initial':
                            st.info(f"{t} - {upd.get('issue')}")
                        else:
                            st.success(f"{t} - {upd.get('updateText')}")

def main():
    if not check_login():
        return

    # Initialize page state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

    current_page = st.session_state.current_page

    # Render sidebar
    render_sidebar(current_page)

    # Navigation buttons (hidden visually, triggered by clicking icons)
    nav_col1, nav_col2, nav_col3, nav_col4, logout_col = st.columns([1,1,1,1,6])

    with nav_col1:
        if st.button("🏠", key="btn_home", help="Home"):
            st.session_state.current_page = 'home'
            st.rerun()

    with nav_col2:
        if st.button("👥", key="btn_squad", help="Squad"):
            st.session_state.current_page = 'squad'
            st.rerun()

    with nav_col3:
        if st.button("👤", key="btn_engineer", help="Engineer"):
            st.session_state.current_page = 'engineer'
            st.rerun()

    with nav_col4:
        if st.button("📅", key="btn_history", help="History"):
            st.session_state.current_page = 'history'
            st.rerun()

    with logout_col:
        if st.button("Logout", key="btn_logout"):
            st.session_state.authenticated = False
            st.session_state.current_page = 'home'
            st.rerun()

    # Get data
    df = get_updates()

    # Route to view
    if current_page == 'squad':
        squad_view(df)
    elif current_page == 'engineer':
        engineer_view(df)
    elif current_page == 'history':
        history_view(df)
    else:
        home_view(df)

    # Footer
    st.markdown("<div style='text-align:center;padding:2rem;color:#959DA5;font-size:0.8rem;border-top:1px solid #E9ECEF;margin-top:3rem;'><b style='color:#24292E;'>TrendLife</b> | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
