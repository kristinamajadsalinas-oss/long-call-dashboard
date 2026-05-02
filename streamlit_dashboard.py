"""
Long Call Updates Dashboard - Squad Lead View with Table Format
Clean, professional design with icon navigation
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

# Manila timezone
MANILA_TZ = pytz.timezone('Asia/Manila')

# Squad leads list
SQUAD_LEADS = ["chris", "judith", "josh", "bea", "kristinamajasa"]  # Added for testing

# Page configuration
st.set_page_config(
    page_title="Long Call Updates Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean professional design
st.markdown("""
<style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Keep sidebar toggle visible */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
    }

    /* Main content styling */
    .main {
        background-color: #FFFFFF;
        padding: 1.5rem;
    }

    /* Headers */
    h1, h2, h3 {
        color: #212529;
        font-weight: 600;
    }

    h1 {
        color: #D71921 !important;
        font-size: 2.25rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Containers with borders */
    [data-testid="stVerticalBlock"] > div:has(> div.element-container) {
        background-color: #FFFFFF;
    }

    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        color: #D71921;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #6C757D;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Tables */
    .stDataFrame {
        border: 1px solid #DEE2E6;
        border-radius: 6px;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 6px;
    }

    /* Buttons */
    .stButton button {
        border-radius: 6px;
        background-color: #D71921;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        border: none;
    }

    .stButton button:hover {
        background-color: #B01419;
    }

    /* Sidebar icon navigation - icon only, no colors */
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: none !important;
        font-size: 2rem !important;
        filter: grayscale(100%) !important;
        opacity: 0.6 !important;
        padding: 1rem !important;
    }

    [data-testid="stSidebar"] button:hover {
        filter: grayscale(0%) brightness(0) saturate(100%) invert(16%) sepia(97%) saturate(4982%) hue-rotate(350deg) brightness(91%) contrast(95%) !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] button:active,
    [data-testid="stSidebar"] button:focus {
        filter: grayscale(0%) brightness(0) saturate(100%) invert(16%) sepia(97%) saturate(4982%) hue-rotate(350deg) brightness(91%) contrast(95%) !important;
        opacity: 1 !important;
    }

    /* Icon sidebar navigation */
    .icon-nav {
        position: fixed;
        left: 0;
        top: 0;
        width: 80px;
        height: 100vh;
        background: #F8F9FA;
        border-right: 1px solid #DEE2E6;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 1rem;
        z-index: 1000;
    }

    .icon-nav-item {
        width: 50px;
        height: 50px;
        margin: 0.5rem 0;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        cursor: pointer;
        color: #6C757D;
        transition: all 0.2s;
    }

    .icon-nav-item:hover {
        background: #E9ECEF;
        color: #D71921;
    }

    .icon-nav-item.active {
        background: #D71921;
        color: white;
    }

    /* Table styling */
    table {
        width: 100%;
        border-collapse: collapse;
    }

    th {
        background-color: #F8F9FA;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        color: #495057;
        border-bottom: 2px solid #DEE2E6;
    }

    td {
        padding: 12px;
        border-bottom: 1px solid #E9ECEF;
    }

    tr:hover {
        background-color: #F8F9FA;
    }

    .status-active {
        color: #28A745;
        font-weight: 600;
    }

    .status-ended {
        color: #6C757D;
    }

    .duration-timer {
        font-family: monospace;
        font-weight: 600;
        color: #D71921;
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
        st.error(f"Firebase initialization failed: {str(e)}")
        return None

# Password check
def check_password(password):
    CORRECT_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # "admin"
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == CORRECT_PASSWORD_HASH

# Check if user is squad lead
def is_squad_lead(username):
    return username.lower() in SQUAD_LEADS

# Fetch data
@st.cache_data(ttl=5)
def get_updates():
    db = init_firebase()
    if not db:
        return pd.DataFrame()

    try:
        docs = db.collection('updates').stream()
        data = []

        for doc in docs:
            d = doc.to_dict()
            d['id'] = doc.id
            data.append(d)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(MANILA_TZ)

        # Sort by timestamp descending
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)

        return df

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return pd.DataFrame()

# Create donut chart
def create_donut(data_dict):
    fig = go.Figure(
        data=[go.Pie(
            labels=list(data_dict.keys()),
            values=list(data_dict.values()),
            hole=0.6,
            marker=dict(colors=['#D71921', '#28A745', '#FFC107', '#17A2B8'])
        )]
    )

    fig.update_layout(
        showlegend=True,
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

# Home View
def home_view(df):
    st.title("Dashboard Overview")
    st.caption("Good morning, Here's what's going on today")

    if df.empty:
        st.warning("No data available. Waiting for long call updates from engineers...")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)

    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # METRICS at top
    with st.container(border=True):
        st.caption("📊 TODAY'S METRICS")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cases = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
            st.metric("CASES TODAY", cases)

        with col2:
            active_cnt = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
            st.metric("ACTIVE (LIVE)", active_cnt)

        with col3:
            ended = 0
            if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    last = df[df['transactionId'] == tid]['timestamp'].max()
                    if last < one_hour_ago:
                        ended += 1
            st.metric("ENDED CALLS", ended)

        with col4:
            over = 0
            if 'timestamp' in today_df.columns and 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    tid_data = df[df['transactionId'] == tid].sort_values('timestamp')
                    if len(tid_data) > 0 and (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds() / 60 >= 60:
                        over += 1
            st.metric(">1HR CALLS", over)

    st.markdown("<br>", unsafe_allow_html=True)

    # Layout (adjust proportions)
    left_col, right_col = st.columns([2.2, 1.8])

    # LEFT: Real-Time Updates TABLE
    with left_col:
        with st.container(border=True):
            st.markdown("### Real-Time Updates")
            st.caption("Live activity feed from all engineers")

            if not df.empty:
                # Build table data
                table_data = []

                # Group by engineer to get their latest status
                for engineer in df['engineer'].unique():
                    eng_data = df[df['engineer'] == engineer].sort_values('timestamp', ascending=False)
                    latest = eng_data.iloc[0]

                    # Determine status
                    time_since = (now - latest['timestamp']).total_seconds() / 60

                    if time_since < 5:
                        status = "Posted update"
                        status_color = "🟢"
                    elif time_since < 60:
                        status = "On call"
                        status_color = "🟢"
                    else:
                        status = "Call ended"
                        status_color = "⚪"

                    # Calculate call duration (from first to last update)
                    tid = latest.get('transactionId', 'N/A')
                    tid_data = df[df['transactionId'] == tid].sort_values('timestamp')

                    if len(tid_data) > 1:
                        duration_sec = (tid_data.iloc[-1]['timestamp'] - tid_data.iloc[0]['timestamp']).total_seconds()
                        duration_min = int(duration_sec / 60)
                        duration_sec = int(duration_sec % 60)
                        duration_str = f"{duration_min:02d}:{duration_sec:02d}"
                    else:
                        duration_str = "—"

                    # Last update TEXT (not time)
                    if latest.get('updateType') == 'initial':
                        last_update_text = latest.get('issue', 'N/A')
                    else:
                        last_update_text = latest.get('updateText', latest.get('reason', 'N/A'))

                    # Truncate if too long
                    if len(last_update_text) > 60:
                        last_update_text = last_update_text[:60] + "..."

                    table_data.append({
                        'Status': status_color,
                        'Engineer': engineer,
                        'Current Status': status,
                        'Duration': duration_str,
                        'Last Update': last_update_text
                    })

                # Display as table with expandable rows
                if table_data:
                    # Table headers
                    header_cols = st.columns([0.5, 2, 2, 1.5, 4, 0.5])
                    with header_cols[0]:
                        st.markdown("**Status**")
                    with header_cols[1]:
                        st.markdown("**Engineer**")
                    with header_cols[2]:
                        st.markdown("**Current Status**")
                    with header_cols[3]:
                        st.markdown("**Duration**")
                    with header_cols[4]:
                        st.markdown("**Last Update**")
                    with header_cols[5]:
                        st.markdown("**Details**")

                    st.markdown("<hr style='margin:0.25rem 0;border-color:#DEE2E6;'>", unsafe_allow_html=True)

                    for idx, row_data in enumerate(table_data):
                        # Create row
                        cols = st.columns([0.5, 2, 2, 1.5, 4, 0.5])

                        with cols[0]:
                            st.markdown(f"<div style='font-size:1.5rem;'>{row_data['Status']}</div>", unsafe_allow_html=True)
                        with cols[1]:
                            st.markdown(f"**{row_data['Engineer']}**")
                        with cols[2]:
                            st.markdown(row_data['Current Status'])
                        with cols[3]:
                            st.markdown(f"<span style='font-family:monospace;font-weight:600;'>{row_data['Duration']}</span>", unsafe_allow_html=True)
                        with cols[4]:
                            st.markdown(row_data['Last Update'])
                        with cols[5]:
                            # Arrow button - navigates to engineer view when clicked
                            if st.button("→", key=f"expand_{idx}", help="View full timeline"):
                                st.session_state.current_view = 'engineer'
                                st.session_state.selected_engineer = row_data['Engineer']
                                st.rerun()

                        # Row divider (no expanded section below!)
                        st.markdown("<hr style='margin:0.5rem 0;border-color:#E9ECEF;'>", unsafe_allow_html=True)
            else:
                st.info("No recent updates")

    # RIGHT: Stacked boxes
    with right_col:
        # Longest Call Running (ONLY show if >22 minutes)
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

                    # Only consider calls > 22 minutes (1320 seconds)
                    if dur > 1320 and dur > longest:
                        longest = dur
                        longest_eng = tid_data.iloc[0].get('engineer', 'Unknown')
                        longest_tid = tid

                if longest_eng and longest > 1320:
                    mins = int(longest // 60)
                    secs = int(longest % 60)

                    st.markdown(f"<div style='font-size:2.5rem;font-weight:700;color:#D71921;font-family:monospace;'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)
                    st.markdown(f"**Engineer (SIEBEL ID):** {longest_eng}")
                    st.markdown(f"**TID:** {longest_tid}")
                else:
                    st.info("No calls over 22 minutes currently")
            else:
                st.info("No active calls")

            st.markdown("---")

            # Update Activity Comparison
            st.markdown("#### Update Activity Comparison")
            if 'engineer' in today_df.columns:
                comp = []
                for eng in today_df['engineer'].unique():
                    eng_data = today_df[today_df['engineer'] == eng]
                    initial = len(eng_data[eng_data['updateType'] == 'initial'])
                    progress = len(eng_data[eng_data['updateType'] == 'progress'])
                    comp.append({'Engineer': eng, 'Initial': initial, 'Progress': progress})

                if comp:
                    st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True, height=200)

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

            if squad_dur and sum(squad_dur.values()) > 0:
                fig = create_donut(squad_dur)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown(f"<div style='text-align:center;padding:2rem;'><div style='font-size:3rem;font-weight:700;color:#D71921;'>{total}m</div><div style='font-size:0.85rem;color:#6C757D;margin-top:0.5rem;'>Sum of all durations today</div></div>", unsafe_allow_html=True)

    # Footer
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#6C757D;font-size:0.85rem;padding:1rem;'>TrendLife | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

# Squad View
def squad_view(df):
    st.title("View by Squad")

    if df.empty:
        st.warning("No data available")
        return

    # Squad selector
    selected_squad = st.selectbox("Select Squad", ["Chris", "Judith", "Josh", "Bea"])

    # Search bar
    search = st.text_input("🔍 Search engineer name", "")

    # Date range
    date_range = st.selectbox("Date Range", ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"])

    # Filter data
    filtered = df[df['squad'].str.contains(selected_squad, case=False, na=False)]

    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]

    st.markdown(f"### Squad {selected_squad} - Engineers")

    if not filtered.empty:
        for engineer in filtered['engineer'].unique():
            eng_data = filtered[filtered['engineer'] == engineer]
            call_count = eng_data['transactionId'].nunique()

            with st.expander(f"👤 {engineer} - {call_count} call(s)"):
                st.dataframe(eng_data[['timestamp', 'transactionId', 'updateType']], use_container_width=True)
    else:
        st.info(f"No engineers found in Squad {selected_squad}")

# Engineer View
def engineer_view(df):
    st.title("View by Engineer")

    if df.empty:
        st.warning("No data available")
        return

    # Engineer selector (use pre-selected if coming from arrow click)
    engineers = sorted(df['engineer'].unique().tolist())

    if 'selected_engineer' in st.session_state and st.session_state.selected_engineer in engineers:
        default_index = engineers.index(st.session_state.selected_engineer)
    else:
        default_index = 0

    selected_eng = st.selectbox("Select Engineer", engineers, index=default_index)

    # Date range
    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "All Time"])

    # Filter
    filtered = df[df['engineer'] == selected_eng]

    st.markdown(f"### {selected_eng}")
    st.caption(f"Total Calls: {filtered['transactionId'].nunique()}")

    # Show all calls
    for tid in filtered['transactionId'].unique():
        tid_data = filtered[filtered['transactionId'] == tid].sort_values('timestamp')
        update_count = len(tid_data)
        first = tid_data.iloc[0]['timestamp'].strftime('%b %d')

        with st.expander(f"TID: {tid} • {first} • {update_count} update(s)"):
            for _, row in tid_data.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')
                utype = row.get('updateType', 'initial').upper()
                st.markdown(f"**{t}** - {utype}")

                if row.get('updateType') == 'initial':
                    st.text(f"Issue: {row.get('issue', 'N/A')}")
                    st.text(f"Reason: {row.get('reason', 'N/A')}")
                else:
                    st.text(f"Update: {row.get('updateText', 'N/A')}")

# History View
def history_view(df):
    st.title("History")

    if df.empty:
        st.warning("No data available")
        return

    # Date range
    date_range = st.selectbox("Date Range", ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"])

    # Group by date
    df_copy = df.copy()
    df_copy['date'] = df_copy['timestamp'].dt.date

    dates = sorted(df_copy['date'].unique(), reverse=True)

    st.markdown("### All History")
    st.caption(f"Total records: {len(df)}")

    for date in dates:
        date_data = df_copy[df_copy['date'] == date]
        count = len(date_data)

        with st.expander(f"📅 {date} - {count} update(s)"):
            st.dataframe(
                date_data[['timestamp', 'engineer', 'transactionId', 'updateType']],
                use_container_width=True,
                hide_index=True
            )

# Main
def main():
    # Login check
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    if not st.session_state.logged_in:
        st.title("Long Call Updates Dashboard")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if check_password(password):
                # Allow ALL users to login (squad leads and engineers)
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.is_squad_lead = is_squad_lead(username)
                st.rerun()
            else:
                st.error("Incorrect password")

        st.info("Password: admin")
        st.caption("Squad Leads: chris, judith, josh, bea")
        return

    # Fetch data
    df = get_updates()

    # Logout button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("Logout", type="primary"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.is_squad_lead = False
            st.rerun()

    # Navigation
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'home'

    # Icon navigation (for squad leads only - show view toggle)
    # For engineers, show simple interface

    if st.session_state.is_squad_lead:
        # Squad Lead Interface - Icon-Only Navigation
        st.sidebar.markdown("### Navigation")

        # Icon buttons (no text)
        if st.sidebar.button("🏠", key="home_btn", help="Home", use_container_width=True):
            st.session_state.current_view = 'home'

        if st.sidebar.button("👥", key="squad_btn", help="Squad", use_container_width=True):
            st.session_state.current_view = 'squad'

        if st.sidebar.button("👤", key="engineer_btn", help="Engineer", use_container_width=True):
            st.session_state.current_view = 'engineer'

        if st.sidebar.button("📅", key="history_btn", help="History", use_container_width=True):
            st.session_state.current_view = 'history'

        # Render view based on current_view
        if st.session_state.current_view == 'home':
            home_view(df)
        elif st.session_state.current_view == 'squad':
            squad_view(df)
        elif st.session_state.current_view == 'engineer':
            engineer_view(df)
        elif st.session_state.current_view == 'history':
            history_view(df)
    else:
        # Engineer Interface - Simple view (personal dashboard)
        st.title(f"My Long Call Updates")
        st.caption(f"Logged in as: {st.session_state.username}")

        # Filter to show only their data
        my_data = df[df['engineer'] == st.session_state.username]

        if not my_data.empty:
            st.success(f"You have {my_data['transactionId'].nunique()} long call(s) tracked")

            # Show their calls
            for tid in my_data['transactionId'].unique():
                tid_data = my_data[my_data['transactionId'] == tid].sort_values('timestamp')
                update_count = len(tid_data)

                with st.expander(f"TID: {tid} • {update_count} update(s)", expanded=True):
                    for _, row in tid_data.iterrows():
                        t = row['timestamp'].strftime('%I:%M %p - %b %d')
                        utype = row.get('updateType', 'initial').upper()
                        st.markdown(f"**{t}** - {utype}")

                        if row.get('updateType') == 'initial':
                            st.text(f"Issue: {row.get('issue', 'N/A')}")
                            st.text(f"Reason: {row.get('reason', 'N/A')}")
                        else:
                            st.text(f"Update: {row.get('updateText', 'N/A')}")
        else:
            st.info("No long call updates yet. Send your first update from the extension!")

if __name__ == "__main__":
    main()
