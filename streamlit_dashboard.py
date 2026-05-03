"""
Long Call Updates Dashboard v1.0
Final consolidated version with all features
Squad Lead: Icon navigation (Home, Squad, Engineer, History)
Engineer: Simple 2 tabs (Home, My Updates)
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import pandas as pd
import pytz
import hashlib
import plotly.graph_objects as go

# Manila timezone
MANILA_TZ = pytz.timezone('Asia/Manila')

# Squad Leads list
SQUAD_LEADS = ["chris", "judith", "josh", "bea", "kristinamajasa"]

# Page config
st.set_page_config(
    page_title="Long Call Updates Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Narrow 60px sidebar
st.markdown("""
<style>
    /* Narrow icon-only sidebar */
    [data-testid="stSidebar"] {
        min-width: 60px !important;
        max-width: 60px !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: 60px !important;
        padding: 1rem 0.5rem !important;
    }
    
    /* Center sidebar content */
    [data-testid="stSidebar"] button {
        width: 48px !important;
        height: 48px !important;
        padding: 0 !important;
        margin: 4px auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 1.5rem !important;
    }
    
    /* Hide sidebar labels */
    [data-testid="stSidebar"] label {
        display: none !important;
    }
    
    /* Main content */
    .main {
        background-color: #FFFFFF;
    }
    
    /* Headers */
    h1 {
        color: #D71921;
        font-weight: 700;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #D71921;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6C757D;
        font-size: 0.85rem;
        text-transform: uppercase;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def check_password(password):
    correct_hash = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
    return hashlib.sha256(password.encode()).hexdigest() == correct_hash

def is_squad_lead(username):
    return username.lower() in SQUAD_LEADS

@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred_dict = dict(st.secrets["gcp_service_account"])
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return None

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
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df['timestamp'] = df['timestamp'].dt.tz_convert(MANILA_TZ)

        df = df.sort_values('timestamp', ascending=False)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def create_donut(data_dict):
    labels = list(data_dict.keys())
    values = list(data_dict.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.6,
        marker=dict(colors=['#D71921', '#28A745', '#FFC107', '#6C757D'])
    )])

    fig.update_layout(showlegend=True, height=280, margin=dict(t=0,b=0,l=0,r=0))
    return fig

# Squad Lead - Home View
def home_view(df):
    st.title("Dashboard Overview")
    st.caption("Real-time monitoring for extended customer calls")

    if df.empty:
        st.warning("No data")
        return

    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)
    today_df = df[df['timestamp'] >= today_start] if 'timestamp' in df.columns else df

    # Metrics
    with st.container(border=True):
        st.caption("📊 TODAY'S METRICS")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            cases = today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0
            st.metric("CASES TODAY", cases)
        
        with c2:
            active = df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0
            st.metric("ACTIVE (LIVE)", active)
        
        with c3:
            ended = 0
            if 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    last_time = df[df['transactionId'] == tid]['timestamp'].max()
                    if last_time < one_hour_ago:
                        ended += 1
            st.metric("ENDED CALLS", ended)
        
        with c4:
            over_1hr = 0
            if 'transactionId' in today_df.columns:
                for tid in today_df['transactionId'].unique():
                    tid_df = df[df['transactionId'] == tid].sort_values('timestamp')
                    if len(tid_df) > 0:
                        dur = (tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() / 60
                        if dur >= 60:
                            over_1hr += 1
            st.metric(">1HR CALLS", over_1hr)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main layout
    left, right = st.columns([2.2, 1])

    # Real-Time Updates (Expandable)
    with left:
        with st.container(border=True):
            st.markdown("### Real-Time Updates")
            st.caption("Live activity feed from all engineers")

            if not df.empty:
                # Group by engineer
                for eng in df['engineer'].unique():
                    eng_df = df[df['engineer'] == eng].sort_values('timestamp', ascending=False)
                    latest = eng_df.iloc[0]
                    
                    time_since = (now - latest['timestamp']).total_seconds() / 60
                    status = "Posted update" if time_since < 5 else ("On call" if time_since < 60 else "Call ended")
                    icon = "🟢" if time_since < 60 else "⚪"
                    
                    tid = latest.get('transactionId', 'N/A')
                    tid_df = df[df['transactionId'] == tid].sort_values('timestamp')
                    dur_str = f"{int((tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() / 60):02d}:{int((tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() % 60):02d}" if len(tid_df) > 1 else "—"
                    
                    last_text = latest.get('issue', latest.get('updateText', 'N/A')) if latest.get('updateType') == 'initial' else latest.get('updateText', 'N/A')
                    if isinstance(last_text, str):
                        last_text = last_text.split('\n')[0][:40] + ("..." if len(last_text) > 40 else "")
                    
                    # Expandable row
                    with st.expander(f"{icon} {eng} - {status} - {dur_str} - {last_text}", expanded=False):
                        st.markdown(f"**Timeline - TID: {tid}**")
                        for _, row in tid_df.iterrows():
                            t = row['timestamp'].strftime('%I:%M %p')
                            if row.get('updateType') == 'initial':
                                st.markdown(f"**{t}** - INITIAL")
                                st.markdown(f"*Issue:* {row.get('issue', 'N/A')}")
                                st.markdown(f"*Reason:* {row.get('reason', 'N/A')}")
                            else:
                                st.markdown(f"**{t}** - PROGRESS")
                                st.markdown(f"*Update:* {row.get('updateText', 'N/A')}")
                            st.markdown("---")

    # Right column
    with right:
        # Longest Call
        with st.container(border=True):
            st.markdown("### Longest Call Running")
            
            active_df = df[df['timestamp'] > one_hour_ago]
            longest = 0
            longest_eng = None
            longest_tid = None
            
            if not active_df.empty and 'transactionId' in active_df.columns:
                for tid in active_df['transactionId'].unique():
                    tid_df = df[df['transactionId'] == tid].sort_values('timestamp')
                    dur = (now - tid_df.iloc[0]['timestamp']).total_seconds()
                    if dur > 1320 and dur > longest:
                        longest = dur
                        longest_eng = tid_df.iloc[0].get('engineer', 'Unknown')
                        longest_tid = tid
                
                if longest_eng:
                    st.markdown(f"<div style='text-align:center;font-size:2.5rem;font-weight:700;color:#D71921;font-family:monospace;'>{int(longest//60):02d}:{int(longest%60):02d}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;'><strong>{longest_eng}</strong></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='text-align:center;'>TID: {longest_tid}</div>", unsafe_allow_html=True)
                else:
                    st.info("No calls over 22 min")
            else:
                st.info("No active calls")
        
        # Comparison
        with st.container(border=True):
            st.markdown("### Update Activity Comparison")
            comp = []
            for eng in today_df['engineer'].unique():
                eng_today = today_df[today_df['engineer'] == eng]
                initial = len(eng_today[eng_today['updateType'] == 'initial'])
                progress = len(eng_today[eng_today['updateType'] == 'progress'])
                comp.append({'Engineer': eng, 'Initial': initial, 'Progress': progress})
            
            if comp:
                st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True, height=150)
        
        # Combined Duration
        with st.container(border=True):
            st.markdown("### Total Combined Duration")
            total = 0
            squad_dur = {}
            
            for tid in today_df['transactionId'].unique():
                tid_df = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_df) > 0:
                    mins = int((tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() / 60)
                    total += mins
                    squad = tid_df.iloc[0].get('squad', 'Unknown')
                    squad_dur[squad] = squad_dur.get(squad, 0) + mins
            
            if squad_dur and sum(squad_dur.values()) > 0:
                fig = create_donut(squad_dur)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown(f"<div style='text-align:center;padding:1.5rem;'><div style='font-size:3rem;font-weight:700;color:#D71921;'>{total}m</div><div style='color:#6C757D;font-size:0.85rem;'>Sum of all durations today</div></div>", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#6C757D;font-size:0.85rem;'>TrendLife | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

# Squad View
def squad_view(df):
    st.title("View by Squad")
    
    if df.empty:
        st.warning("No data")
        return
    
    squad = st.selectbox("Select Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search engineer", "")
    
    filtered = df[df['squad'].str.contains(squad, case=False, na=False)]
    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]
    
    st.markdown(f"### Squad {squad}")
    
    if not filtered.empty:
        for eng in filtered['engineer'].unique():
            eng_df = filtered[filtered['engineer'] == eng]
            with st.expander(f"👤 {eng} - {eng_df['transactionId'].nunique()} call(s)"):
                for tid in eng_df['transactionId'].unique():
                    tid_df = eng_df[eng_df['transactionId'] == tid].sort_values('timestamp')
                    st.markdown(f"**TID: {tid}**")
                    for _, row in tid_df.iterrows():
                        t = row['timestamp'].strftime('%I:%M %p')
                        if row.get('updateType') == 'initial':
                            st.markdown(f"- {t}: INITIAL - {row.get('issue', 'N/A')}")
                        else:
                            st.markdown(f"- {t}: UPDATE - {row.get('updateText', 'N/A')}")
                    st.markdown("---")

# Engineer View
def engineer_view(df):
    st.title("View by Engineer")
    
    if df.empty:
        st.warning("No data")
        return
    
    engineers = sorted(df['engineer'].unique())
    eng = st.selectbox("Select Engineer", engineers)
    
    eng_df = df[df['engineer'] == eng]
    st.markdown(f"### {eng}")
    st.markdown(f"**Total Calls:** {eng_df['transactionId'].nunique()}")
    
    for tid in eng_df['transactionId'].unique():
        tid_df = eng_df[eng_df['transactionId'] == tid].sort_values('timestamp')
        date = tid_df.iloc[0]['timestamp'].strftime('%b %d')
        
        with st.expander(f"TID: {tid} • {date} • {len(tid_df)} update(s)"):
            for _, row in tid_df.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')
                if row.get('updateType') == 'initial':
                    st.markdown(f"**{t}** - INITIAL")
                    st.markdown(f"Issue: {row.get('issue', 'N/A')}")
                    st.markdown(f"Reason: {row.get('reason', 'N/A')}")
                else:
                    st.markdown(f"**{t}** - PROGRESS")
                    st.markdown(f"Update: {row.get('updateText', 'N/A')}")
                st.markdown("---")

# History View
def history_view(df):
    st.title("History")
    
    if df.empty:
        st.warning("No data")
        return
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        date_opt = st.selectbox("Date Range", [
            "Last 7 Days",
            "Single Day",
            "This Month",
            "Custom Month",
            "All Time"
        ])
    
    now = datetime.now(MANILA_TZ)
    filtered = df.copy()
    
    if date_opt == "Last 7 Days":
        filtered = df[df['timestamp'] >= now - timedelta(days=7)]
    elif date_opt == "Single Day":
        sel_date = st.date_input("Select Date", now.date())
        day_start = MANILA_TZ.localize(datetime.combine(sel_date, datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        filtered = df[(df['timestamp'] >= day_start) & (df['timestamp'] < day_end)]
    elif date_opt == "This Month":
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        filtered = df[df['timestamp'] >= month_start]
    elif date_opt == "Custom Month":
        sel_month = st.date_input("Select Month", now.date())
        month_start = MANILA_TZ.localize(datetime(sel_month.year, sel_month.month, 1))
        next_month = month_start + timedelta(days=32)
        month_end = MANILA_TZ.localize(datetime(next_month.year, next_month.month, 1))
        filtered = df[(df['timestamp'] >= month_start) & (df['timestamp'] < month_end)]
    
    if not filtered.empty:
        records = []
        for tid in filtered['transactionId'].unique():
            tid_df = filtered[filtered['transactionId'] == tid].sort_values('timestamp')
            initial = tid_df[tid_df['updateType'] == 'initial'].iloc[0] if len(tid_df[tid_df['updateType'] == 'initial']) > 0 else tid_df.iloc[0]
            
            progress = tid_df[tid_df['updateType'] == 'progress']['updateText'].tolist()
            updates_str = ', '.join([str(u) for u in progress if u and str(u) != 'nan']) or '—'
            
            records.append({
                'Timestamp': initial['timestamp'].strftime('%b %d %I:%M %p'),
                'Engineer': initial.get('engineer', 'Unknown'),
                'Transaction ID': tid,
                'Issue': initial.get('issue', 'N/A'),
                'Reason': initial.get('reason', 'N/A'),
                'Updates': updates_str
            })
        
        history_df = pd.DataFrame(records)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            csv = history_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download", csv, f"history_{now.strftime('%Y%m%d')}.csv", "text/csv", type="primary")
        
        st.markdown(f"### Total Records: {len(records)}")
        st.dataframe(history_df, use_container_width=True, hide_index=True, height=600)
    else:
        st.info("No data for selected range")

# Engineer Personal View
def engineer_personal_view(df, username):
    st.title("My Long Call Updates")
    st.caption(f"Logged in as: {username}")
    
    my_df = df[df['engineer'] == username]
    
    tab1, tab2 = st.tabs(["🏠 Home - Team Updates", "📝 My Updates"])
    
    with tab1:
        st.markdown("### Real-Time Team Activity")
        if not df.empty:
            recent = df.head(10)
            for _, row in recent.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')
                eng = row.get('engineer', 'Unknown')
                action = "started call" if row.get('updateType') == 'initial' else "posted update"
                st.info(f"🟢 {t} - {eng} {action}")
    
    with tab2:
        st.markdown("### My Call History")
        if not my_df.empty:
            st.markdown(f"**Total Calls:** {my_df['transactionId'].nunique()}")
            
            for tid in my_df['transactionId'].unique():
                tid_df = my_df[my_df['transactionId'] == tid].sort_values('timestamp')
                date = tid_df.iloc[0]['timestamp'].strftime('%b %d')
                
                with st.expander(f"TID: {tid} • {date} • {len(tid_df)} update(s)"):
                    for _, row in tid_df.iterrows():
                        t = row['timestamp'].strftime('%I:%M %p')
                        if row.get('updateType') == 'initial':
                            st.markdown(f"**{t}** - INITIAL")
                            st.markdown(f"Issue: {row.get('issue', 'N/A')}")
                            st.markdown(f"Reason: {row.get('reason', 'N/A')}")
                        else:
                            st.markdown(f"**{t}** - PROGRESS")
                            st.markdown(f"Update: {row.get('updateText', 'N/A')}")
                        st.markdown("---")
        else:
            st.info("No updates yet")

# Main
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_squad_lead = False
    
    if not st.session_state.logged_in:
        st.title("Long Call Updates Dashboard")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", type="primary"):
            if check_password(password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.is_squad_lead = is_squad_lead(username)
                st.rerun()
            else:
                st.error("Incorrect password")
        
        st.info("Password: **admin**")
        st.caption("Squad Leads: chris, judith, josh, bea")
        return
    
    df = get_updates()
    
    # Squad Lead Interface
    if st.session_state.is_squad_lead:
        with st.sidebar:
            st.markdown("<div style='text-align:center;padding:1rem 0;'>", unsafe_allow_html=True)
            try:
                st.image("icons/icon48.png", width=45)
            except:
                st.markdown("<div style='background:#6C757D;color:white;padding:8px;border-radius:8px;font-size:0.7rem;font-weight:700;'>TL</div>", unsafe_allow_html=True)
            st.markdown("</div><hr>", unsafe_allow_html=True)
            
            if 'view' not in st.session_state:
                st.session_state.view = 'home'
            
            if st.button("🏠", help="Home", use_container_width=True):
                st.session_state.view = 'home'
                st.rerun()
            
            if st.button("👥", help="Squad", use_container_width=True):
                st.session_state.view = 'squad'
                st.rerun()
            
            if st.button("👤", help="Engineer", use_container_width=True):
                st.session_state.view = 'engineer'
                st.rerun()
            
            if st.button("📅", help="History", use_container_width=True):
                st.session_state.view = 'history'
                st.rerun()
            
            st.markdown("<div style='position:fixed;bottom:20px;'>", unsafe_allow_html=True)
            if st.button("🚪", help="Logout", type="primary"):
                st.session_state.logged_in = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.view == 'home':
            home_view(df)
        elif st.session_state.view == 'squad':
            squad_view(df)
        elif st.session_state.view == 'engineer':
            engineer_view(df)
        elif st.session_state.view == 'history':
            history_view(df)
    
    # Engineer Interface
    else:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("Logout", type="primary"):
                st.session_state.logged_in = False
                st.rerun()
        
        engineer_personal_view(df, st.session_state.username)

if __name__ == "__main__":
    main()
