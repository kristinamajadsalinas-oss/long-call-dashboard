"""
Long Call Updates Dashboard v1.0
Squad Leads: 4-icon sidebar (Home, Squad, Engineer, History)
Engineers: 2-icon sidebar (Home, My Updates)
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

# Squad leads ONLY (kristinamajasa is engineer!)
SQUAD_LEADS = ["chris", "judith", "josh", "bea"]

st.set_page_config(
    page_title="Long Call Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS - Narrow 60px sidebar with single-color icons
st.markdown("""
<style>
    /* 60px narrow sidebar */
    [data-testid="stSidebar"] {
        min-width: 60px !important;
        max-width: 60px !important;
    }
    
    [data-testid="stSidebar"] > div {
        width: 60px !important;
        padding: 0.5rem 0 !important;
    }
    
    /* Single-color icon buttons - NO BORDERS! */
    [data-testid="stSidebar"] button {
        width: 48px !important;
        height: 48px !important;
        padding: 0 !important;
        margin: 4px auto !important;
        background-color: transparent !important;
        border: none !important;
        color: #6C757D !important;
        font-size: 1.8rem !important;
    }

    [data-testid="stSidebar"] button:hover {
        color: #D71921 !important;
        background-color: transparent !important;
    }

    /* Active button - RED color */
    [data-testid="stSidebar"] button[data-baseweb="button"][kind="primary"] {
        background-color: transparent !important;
        border: none !important;
        color: #D71921 !important;
    }
    
    /* Hide labels */
    [data-testid="stSidebar"] label {
        display: none !important;
    }
    
    /* Main styling */
    .main {
        background-color: #FFFFFF;
    }
    
    h1 {color: #D71921; font-weight: 700;}
    
    [data-testid="stMetricValue"] {
        color: #D71921;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6C757D;
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def check_password(password):
    return hashlib.sha256(password.encode()).hexdigest() == "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

def is_squad_lead(username):
    return username.lower() in SQUAD_LEADS

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
        
        return df.sort_values('timestamp', ascending=False)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def create_donut(data_dict):
    fig = go.Figure(data=[go.Pie(
        labels=list(data_dict.keys()),
        values=list(data_dict.values()),
        hole=.6,
        marker=dict(colors=['#D71921', '#28A745', '#FFC107', '#6C757D'])
    )])
    fig.update_layout(showlegend=True, height=280, margin=dict(t=0,b=0,l=0,r=0))
    return fig

# Real-Time Updates Table with clickable arrows
def show_realtime_table(df):
    now = datetime.now(MANILA_TZ)

    if df.empty:
        st.info("No updates")
        return

    table_rows = []
    engineer_data_map = {}

    for eng in df['engineer'].unique():
        eng_df = df[df['engineer'] == eng].sort_values('timestamp', ascending=False)
        latest = eng_df.iloc[0]

        time_since = (now - latest['timestamp']).total_seconds() / 60
        status = "Posted update" if time_since < 5 else ("On call" if time_since < 60 else "Call ended")
        icon = "🟢" if time_since < 60 else "⚪"

        tid = latest.get('transactionId', 'N/A')
        tid_df = df[df['transactionId'] == tid].sort_values('timestamp')

        dur_str = f"{int((tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() / 60):02d}:{int((tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() % 60):02d}" if len(tid_df) > 1 else "—"

        last_text = latest.get('issue' if latest.get('updateType') == 'initial' else 'updateText', 'N/A')
        if isinstance(last_text, str):
            last_text = last_text.split('\n')[0][:40] + ("..." if len(last_text) > 40 else "")

        table_rows.append({
            'Status': icon,
            'Engineer': eng,
            'Current Status': status,
            'Duration': dur_str,
            'Last Update': last_text,
            'View': '→'
        })

        # Store full timeline data
        engineer_data_map[eng] = tid_df

    # Display table
    table_df = pd.DataFrame(table_rows)
    st.dataframe(table_df, use_container_width=True, hide_index=True, height=400)

    # Show buttons to view timeline for each engineer
    st.markdown("**Click to view full timeline:**")
    cols = st.columns(min(len(engineer_data_map), 4))

    for idx, (eng, tid_df) in enumerate(engineer_data_map.items()):
        with cols[idx % 4]:
            if st.button(f"→ {eng}", key=f"view_{eng}", use_container_width=True):
                st.session_state.selected_engineer = eng

    # Show timeline for selected engineer
    if 'selected_engineer' in st.session_state and st.session_state.selected_engineer in engineer_data_map:
        selected = st.session_state.selected_engineer
        tid_df = engineer_data_map[selected]
        tid = tid_df.iloc[0].get('transactionId', 'N/A')

        st.markdown("---")
        st.markdown(f"### Full Timeline - {selected} - TID: {tid}")

        for _, row in tid_df.iterrows():
            t = row['timestamp'].strftime('%I:%M %p')
            if row.get('updateType') == 'initial':
                st.markdown(f"**{t}** - INITIAL UPDATE")
                st.markdown(f"**Issue:** {row.get('issue', 'N/A')}")
                st.markdown(f"**Reason:** {row.get('reason', 'N/A')}")
            else:
                st.markdown(f"**{t}** - PROGRESS UPDATE")
                st.markdown(f"**Update:** {row.get('updateText', 'N/A')}")
            st.markdown("---")

# Home View (Squad Lead)
def home_view_squad(df):
    st.title("Dashboard Overview")
    st.caption("Real-time monitoring for extended customer calls")
    
    if df.empty:
        st.warning("No data")
        return
    
    now = datetime.now(MANILA_TZ)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_hour_ago = now - timedelta(hours=1)
    today_df = df[df['timestamp'] >= today_start]
    
    # Metrics
    with st.container(border=True):
        st.caption("📊 TODAY'S METRICS")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.metric("CASES TODAY", today_df['transactionId'].nunique() if 'transactionId' in today_df.columns else 0)
        with c2:
            st.metric("ACTIVE (LIVE)", df[df['timestamp'] > one_hour_ago]['engineer'].nunique() if 'timestamp' in df.columns else 0)
        with c3:
            ended = sum(1 for tid in today_df['transactionId'].unique() if df[df['transactionId'] == tid]['timestamp'].max() < one_hour_ago) if 'transactionId' in today_df.columns else 0
            st.metric("ENDED CALLS", ended)
        with c4:
            over = sum(1 for tid in today_df['transactionId'].unique() if (df[df['transactionId'] == tid].sort_values('timestamp').iloc[-1]['timestamp'] - df[df['transactionId'] == tid].sort_values('timestamp').iloc[0]['timestamp']).total_seconds() / 60 >= 60) if 'transactionId' in today_df.columns and len(today_df) > 0 else 0
            st.metric(">1HR CALLS", over)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    left, right = st.columns([2.2, 1])
    
    with left:
        with st.container(border=True):
            st.markdown("### Real-Time Updates")
            st.caption("Live activity feed from all engineers")
            show_realtime_table(df)
    
    with right:
        with st.container(border=True):
            st.markdown("### Longest Call Running")
            active = df[df['timestamp'] > one_hour_ago]
            longest = 0
            longest_eng = None
            longest_tid = None
            
            for tid in active['transactionId'].unique() if not active.empty else []:
                tid_df = df[df['transactionId'] == tid].sort_values('timestamp')
                dur = (now - tid_df.iloc[0]['timestamp']).total_seconds()
                if dur > 1320 and dur > longest:
                    longest = dur
                    longest_eng = tid_df.iloc[0].get('engineer', 'Unknown')
                    longest_tid = tid
            
            if longest_eng:
                st.markdown(f"<div style='text-align:center;font-size:2.5rem;font-weight:700;color:#D71921;font-family:monospace;'>{int(longest//60):02d}:{int(longest%60):02d}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;'><strong>{longest_eng}</strong><br>TID: {longest_tid}</div>", unsafe_allow_html=True)
            else:
                st.info("No calls over 22 min")
        
        with st.container(border=True):
            st.markdown("### Update Activity Comparison")
            comp = [{'Engineer': eng, 'Initial': len(today_df[(today_df['engineer'] == eng) & (today_df['updateType'] == 'initial')]), 'Progress': len(today_df[(today_df['engineer'] == eng) & (today_df['updateType'] == 'progress')])} for eng in today_df['engineer'].unique()]
            if comp:
                st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True, height=150)
        
        with st.container(border=True):
            st.markdown("### Total Combined Duration")
            total = sum(int((df[df['transactionId'] == tid].sort_values('timestamp').iloc[-1]['timestamp'] - df[df['transactionId'] == tid].sort_values('timestamp').iloc[0]['timestamp']).total_seconds() / 60) for tid in today_df['transactionId'].unique() if len(df[df['transactionId'] == tid]) > 0)
            squad_dur = {}
            for tid in today_df['transactionId'].unique():
                tid_df = df[df['transactionId'] == tid].sort_values('timestamp')
                if len(tid_df) > 0:
                    mins = int((tid_df.iloc[-1]['timestamp'] - tid_df.iloc[0]['timestamp']).total_seconds() / 60)
                    squad = tid_df.iloc[0].get('squad', 'Unknown')
                    squad_dur[squad] = squad_dur.get(squad, 0) + mins
            
            if squad_dur and sum(squad_dur.values()) > 0:
                st.plotly_chart(create_donut(squad_dur), use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown(f"<div style='text-align:center;padding:1.5rem;'><div style='font-size:3rem;font-weight:700;color:#D71921;'>{total}m</div><div style='color:#6C757D;font-size:0.85rem;'>Sum today</div></div>", unsafe_allow_html=True)
    
    st.markdown("<hr><div style='text-align:center;color:#6C757D;font-size:0.85rem;'>TrendLife | Where intelligence meets care • v1.0</div>", unsafe_allow_html=True)

# Home View (Engineer) - SAME table as squad lead!
def home_view_engineer(df):
    st.title("Team Updates")
    st.caption("Real-time monitoring for extended customer calls")
    
    with st.container(border=True):
        st.markdown("### Real-Time Updates")
        st.caption("Live activity feed from all engineers")
        show_realtime_table(df)

# My Updates (Engineer) - with Edit
def my_updates_view(df, username):
    st.title("My Updates")
    st.caption(f"Your personal call history - {username}")

    my_df = df[df['engineer'] == username]

    if my_df.empty:
        st.info("No updates yet. Updates will appear when you submit from the extension.")
        return

    st.markdown(f"**Total Calls:** {my_df['transactionId'].nunique()}")

    for tid in my_df['transactionId'].unique():
        tid_df = my_df[my_df['transactionId'] == tid].sort_values('timestamp')
        date = tid_df.iloc[0]['timestamp'].strftime('%b %d')

        with st.expander(f"TID: {tid} • {date} • {len(tid_df)} update(s)", expanded=False):
            for idx, row in tid_df.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')

                if row.get('updateType') == 'initial':
                    st.markdown(f"**{t}** - INITIAL UPDATE")

                    # Show current + editable
                    st.markdown(f"**Issue:** {row.get('issue', 'N/A')}")
                    new_issue = st.text_area("Edit Issue:", row.get('issue', ''), key=f"issue_{idx}", height=80)

                    st.markdown(f"**Reason:** {row.get('reason', 'N/A')}")
                    new_reason = st.text_area("Edit Reason:", row.get('reason', ''), key=f"reason_{idx}", height=100)

                    if st.button("💾 Save Changes", key=f"save_{idx}"):
                        st.success("Changes saved! (Firebase update coming soon)")
                else:
                    st.markdown(f"**{t}** - PROGRESS UPDATE")

                    st.markdown(f"**Update:** {row.get('updateText', 'N/A')}")
                    new_update = st.text_area("Edit Update:", row.get('updateText', ''), key=f"update_{idx}", height=80)

                    if st.button("💾 Save Changes", key=f"save_up_{idx}"):
                        st.success("Changes saved! (Firebase update coming soon)")

                st.markdown("---")

def squad_view(df):
    st.title("View by Squad")
    if df.empty:
        st.warning("No data")
        return
    
    squad = st.selectbox("Select Squad", ["Chris", "Judith", "Josh", "Bea"])
    search = st.text_input("🔍 Search", "")
    
    filtered = df[df['squad'].str.contains(squad, case=False, na=False)]
    if search:
        filtered = filtered[filtered['engineer'].str.contains(search, case=False, na=False)]
    
    st.markdown(f"### Squad {squad}")
    
    for eng in filtered['engineer'].unique() if not filtered.empty else []:
        eng_df = filtered[filtered['engineer'] == eng]
        with st.expander(f"{eng} - {eng_df['transactionId'].nunique()} call(s)"):
            for tid in eng_df['transactionId'].unique():
                tid_df = eng_df[eng_df['transactionId'] == tid].sort_values('timestamp')
                st.markdown(f"**TID: {tid}**")
                for _, row in tid_df.iterrows():
                    t = row['timestamp'].strftime('%I:%M %p')
                    st.markdown(f"- {t}: {'INITIAL' if row.get('updateType') == 'initial' else 'UPDATE'}")
                st.markdown("---")

def engineer_view(df):
    st.title("View by Engineer")
    if df.empty:
        st.warning("No data")
        return

    eng = st.selectbox("Engineer", sorted(df['engineer'].unique()))
    eng_df = df[df['engineer'] == eng]

    st.markdown(f"### {eng} - {eng_df['transactionId'].nunique()} calls")

    for tid in eng_df['transactionId'].unique():
        tid_df = eng_df[eng_df['transactionId'] == tid].sort_values('timestamp')
        date = tid_df.iloc[0]['timestamp'].strftime('%b %d')

        with st.expander(f"TID: {tid} • {date} • {len(tid_df)} update(s)"):
            for _, row in tid_df.iterrows():
                t = row['timestamp'].strftime('%I:%M %p')

                if row.get('updateType') == 'initial':
                    st.markdown(f"**{t}** - INITIAL UPDATE")
                    st.markdown(f"**Issue:** {row.get('issue', 'N/A')}")
                    st.markdown(f"**Reason:** {row.get('reason', 'N/A')}")
                else:
                    st.markdown(f"**{t}** - PROGRESS UPDATE")
                    st.markdown(f"**Update:** {row.get('updateText', 'N/A')}")

                st.markdown("---")

def history_view(df):
    st.title("History")
    if df.empty:
        st.warning("No data")
        return
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        date_opt = st.selectbox("Date Range", [
            "Last 7 Days",
            "This Day",
            "This Month",
            "All Time",
            "Custom Date Range"
        ])

    now = datetime.now(MANILA_TZ)
    filtered = df.copy()

    if date_opt == "Last 7 Days":
        # All data from last 7 days combined
        filtered = df[df['timestamp'] >= now - timedelta(days=7)]
    elif date_opt == "This Day":
        # Today only
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        filtered = df[(df['timestamp'] >= today_start) & (df['timestamp'] < tomorrow_start)]
    elif date_opt == "This Month":
        # This entire month combined
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        filtered = df[df['timestamp'] >= month_start]
    elif date_opt == "Custom Date Range":
        # Select custom from/to dates
        col_from, col_to = st.columns(2)
        with col_from:
            from_date = st.date_input("From Date", now.date() - timedelta(days=7))
        with col_to:
            to_date = st.date_input("To Date", now.date())

        start = MANILA_TZ.localize(datetime.combine(from_date, datetime.min.time()))
        end = MANILA_TZ.localize(datetime.combine(to_date, datetime.max.time()))
        filtered = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
    # else: All Time (no filter)
    
    if not filtered.empty:
        records = []
        for tid in filtered['transactionId'].unique():
            tid_df = filtered[filtered['transactionId'] == tid].sort_values('timestamp')
            initial = tid_df[tid_df['updateType'] == 'initial'].iloc[0] if len(tid_df[tid_df['updateType'] == 'initial']) > 0 else tid_df.iloc[0]
            progress = ', '.join([str(u) for u in tid_df[tid_df['updateType'] == 'progress']['updateText'].tolist() if u and str(u) != 'nan']) or '—'
            
            records.append({
                'Timestamp': initial['timestamp'].strftime('%b %d %I:%M %p'),
                'Engineer': initial.get('engineer', 'Unknown'),
                'Transaction ID': tid,
                'Issue': initial.get('issue', 'N/A'),
                'Reason': initial.get('reason', 'N/A'),
                'Updates': progress
            })
        
        history_df = pd.DataFrame(records)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button("📥 Download", history_df.to_csv(index=False).encode('utf-8'), f"history_{now.strftime('%Y%m%d')}.csv", "text/csv", type="primary")
        
        st.markdown(f"### Total: {len(records)}")
        st.dataframe(history_df, use_container_width=True, hide_index=True, height=600)
    else:
        st.info("No data")

def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
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
        return
    
    df = get_updates()
    
    # SQUAD LEAD INTERFACE - 4 icons
    if st.session_state.is_squad_lead:
        with st.sidebar:
            st.markdown("<div style='text-align:center;padding:1rem 0;'>TL</div><hr>", unsafe_allow_html=True)
            
            if 'view' not in st.session_state:
                st.session_state.view = 'home'
            
            if st.button("🏠", help="Home"):
                st.session_state.view = 'home'
                st.rerun()
            if st.button("👥", help="Squad"):
                st.session_state.view = 'squad'
                st.rerun()
            if st.button("👤", help="Engineer"):
                st.session_state.view = 'engineer'
                st.rerun()
            if st.button("📅", help="History"):
                st.session_state.view = 'history'
                st.rerun()
            
            st.markdown("<div style='position:fixed;bottom:20px;width:60px;text-align:center;'>", unsafe_allow_html=True)
            if st.button("←", help="Logout", type="primary"):
                st.session_state.logged_in = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.view == 'home':
            home_view_squad(df)
        elif st.session_state.view == 'squad':
            squad_view(df)
        elif st.session_state.view == 'engineer':
            engineer_view(df)
        else:
            history_view(df)
    
    # ENGINEER INTERFACE - 2 icons
    else:
        with st.sidebar:
            st.markdown("<div style='text-align:center;padding:1rem 0;'>TL</div><hr>", unsafe_allow_html=True)
            
            if 'eng_view' not in st.session_state:
                st.session_state.eng_view = 'home'
            
            if st.button("🏠", help="Home"):
                st.session_state.eng_view = 'home'
                st.rerun()
            if st.button("📝", help="My Updates"):
                st.session_state.eng_view = 'updates'
                st.rerun()
            
            st.markdown("<div style='position:fixed;bottom:20px;width:60px;text-align:center;'>", unsafe_allow_html=True)
            if st.button("←", help="Logout", type="primary"):
                st.session_state.logged_in = False
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.eng_view == 'home':
            home_view_engineer(df)
        else:
            my_updates_view(df, st.session_state.username)

if __name__ == "__main__":
    main()
