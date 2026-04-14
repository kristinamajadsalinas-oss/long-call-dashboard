"""
Long Call Update Dashboard - Two Separate Views
1. Engineer's Personal Dashboard (editable, own data only)
2. Squad Lead's Team Dashboard (read-only, all engineers)
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

# Custom CSS for better appearance
st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #1a1a1a;
        color: #ffffff;
    }

    /* Header styling */
    h1 {
        color: #DC3545;
        font-weight: 900;
    }

    h2, h3 {
        color: #ffffff;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: bold;
    }

    /* Cards */
    .stExpander {
        background-color: #2d2d2d;
        border: 1px solid #444;
        border-radius: 8px;
        margin-bottom: 10px;
    }

    /* Info boxes */
    .stAlert {
        background-color: #2d2d2d;
        border-left: 4px solid #28a745;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
    }

    /* Buttons */
    .stButton button {
        background-color: #DC3545;
        color: white;
        font-weight: bold;
        border-radius: 4px;
    }

    /* Text inputs */
    .stTextArea textarea, .stTextInput input {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #444;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        color: #888;
        font-size: 0.9rem;
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
        st.error(f"Failed to initialize Firebase: {e}")
        return None

# Password protection
def check_password():
    """Simple password protection"""
    # Store password as SHA256 hash
    # To generate: hashlib.sha256("your_password".encode()).hexdigest()
    CORRECT_PASSWORD_HASH = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # "admin"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("## 🔐 Long Call Updates Dashboard")
        st.markdown("Please enter password to access")

        password = st.text_input("Password", type="password", key="password_input")

        if st.button("Login"):
            if hashlib.sha256(password.encode()).hexdigest() == CORRECT_PASSWORD_HASH:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")

        st.info("💡 Default password: admin")
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

        # Convert timestamp to datetime if it exists
        if 'timestamp' in df.columns:
            # Force all timestamps to UTC first (handles mixed timezones)
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            # Then convert to Manila timezone
            df['timestamp'] = df['timestamp'].dt.tz_convert(MANILA_TZ)

        # Sort by timestamp descending (newest first)
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)

        return df

    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Submit update from engineer dashboard
def submit_update_from_dashboard(engineer_siebel, transaction_id, update_text):
    """Submit a progress update from engineer's dashboard"""
    try:
        db = init_firebase()
        if not db:
            st.error("Firebase not initialized")
            return False

        # Get engineer settings
        settings = st.session_state.get('engineer_settings', {})

        update_data = {
            'timestamp': datetime.now(MANILA_TZ).isoformat(),
            'engineer': engineer_siebel,
            'transactionId': transaction_id,
            'squad': settings.get('squad', 'Unknown'),
            'skillset': settings.get('skillset', 'Unknown'),
            'updateType': 'progress',
            'updateText': update_text,
            'callDuration': 'Unknown'
        }

        # Add to Firestore
        db.collection('updates').add(update_data)
        return True

    except Exception as e:
        st.error(f"Error submitting update: {e}")
        return False

# ============================================
# ENGINEER'S DASHBOARD VIEW
# ============================================
def engineer_view():
    """Engineer's personal dashboard - see own data, add updates"""

    st.title("📊 My Long Call Updates")
    st.markdown("### Your Personal Call History & Updates")

    # Get engineer's Siebel ID from URL parameter or input
    params = st.query_params
    engineer_siebel = params.get("engineer", None)

    if not engineer_siebel:
        st.info("🔑 Enter your Siebel ID to view your dashboard")
        engineer_siebel = st.text_input("Siebel ID", placeholder="e.g., kristinamajasa")

        if st.button("Access My Dashboard"):
            if engineer_siebel:
                st.query_params["engineer"] = engineer_siebel
                st.rerun()
        return

    st.success(f"👤 Logged in as: **{engineer_siebel}**")

    # Get all updates
    df = get_updates()

    if df.empty:
        st.warning("No data found. Send your first long call update from the extension!")
        return

    # Filter to only THIS engineer's data
    engineer_df = df[df['engineer'] == engineer_siebel].copy()

    if engineer_df.empty:
        st.info(f"No updates found for {engineer_siebel}. Your updates will appear here once you send them from the extension.")
        return

    # ===== ACTIVE CALLS SECTION =====
    st.markdown("---")
    st.header("🟢 Active Call")

    # Find active calls (group by TID, check if recent)
    one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)

    active_calls = {}
    for tid in engineer_df['transactionId'].unique():
        tid_data = engineer_df[engineer_df['transactionId'] == tid].sort_values('timestamp')
        latest_update = tid_data.iloc[-1]

        # Consider active if last update was within 1 hour
        if 'timestamp' in latest_update and latest_update['timestamp'] > one_hour_ago:
            active_calls[tid] = tid_data

    if active_calls:
        for tid, call_data in active_calls.items():
            with st.container():
                st.subheader(f"📞 Transaction ID: {tid}")

                # Show timeline
                st.markdown("**📜 Update Timeline:**")
                for idx, update in call_data.iterrows():
                    time_str = update['timestamp'].strftime('%I:%M %p') if 'timestamp' in update else 'N/A'
                    update_type = update.get('updateType', 'initial')

                    if update_type == 'initial':
                        st.info(f"⏰ **{time_str} - INITIAL UPDATE**\n\n"
                               f"**Issue:** {update.get('issue', 'N/A')}\n\n"
                               f"**Reason:** {update.get('reason', 'N/A')}")
                    else:
                        st.success(f"⏰ **{time_str} - PROGRESS UPDATE**\n\n"
                                  f"{update.get('updateText', 'N/A')}")

                # Add update form
                st.markdown("**➕ Add Progress Update:**")
                with st.form(key=f"update_form_{tid}"):
                    new_update = st.text_area(
                        "New Update",
                        placeholder="Enter your progress update here...",
                        height=100,
                        key=f"update_text_{tid}"
                    )

                    submitted = st.form_submit_button("🔄 Submit Update", use_container_width=True)

                    if submitted and new_update.strip():
                        # Get squad and skillset from first entry
                        first_entry = call_data.iloc[0]
                        st.session_state.engineer_settings = {
                            'squad': first_entry.get('squad', 'Unknown'),
                            'skillset': first_entry.get('skillset', 'Unknown')
                        }

                        if submit_update_from_dashboard(engineer_siebel, tid, new_update):
                            st.success("✅ Update submitted successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to submit update")
    else:
        st.info("No active calls. Active calls will appear here once you answer a call.")

    # ===== HISTORY SECTION =====
    st.markdown("---")
    st.header("📋 My Call History (Last 7 Days)")

    # Group by Transaction ID
    seven_days_ago = datetime.now(MANILA_TZ) - timedelta(days=7)
    recent_calls = engineer_df[engineer_df['timestamp'] > seven_days_ago]

    if not recent_calls.empty:
        # Group by TID
        for tid in recent_calls['transactionId'].unique():
            if tid in active_calls:
                continue  # Skip active calls (already shown above)

            tid_data = recent_calls[recent_calls['transactionId'] == tid].sort_values('timestamp')
            first_update = tid_data.iloc[0]
            last_update = tid_data.iloc[-1]

            # Calculate duration from first to last update
            if len(tid_data) > 1:
                duration = last_update['timestamp'] - first_update['timestamp']
                duration_str = f"{int(duration.total_seconds() / 60)}m"
            else:
                duration_str = first_update.get('callDuration', 'Unknown')

            date_str = first_update['timestamp'].strftime('%b %d, %Y')

            with st.expander(f"📞 TID: {tid} - {date_str} - {duration_str} - {len(tid_data)} update(s)"):
                for idx, update in tid_data.iterrows():
                    time_str = update['timestamp'].strftime('%I:%M %p')
                    update_type = update.get('updateType', 'initial')

                    if update_type == 'initial':
                        st.info(f"⏰ **{time_str} - INITIAL UPDATE**\n\n"
                               f"**Issue:** {update.get('issue', 'N/A')}\n\n"
                               f"**Reason:** {update.get('reason', 'N/A')}")
                    else:
                        st.success(f"⏰ **{time_str} - UPDATE**\n\n"
                                  f"{update.get('updateText', 'N/A')}")
    else:
        st.info("No call history in the last 7 days.")

    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>TrendLife | Where intelligence meets care<br>Long Call Update Dashboard v1.0</div>", unsafe_allow_html=True)

# ============================================
# SQUAD LEAD'S DASHBOARD VIEW
# ============================================
def squad_lead_view():
    """Squad Lead's team dashboard - monitor all engineers"""

    st.title("📊 Long Call Updates Dashboard")
    st.markdown("### Real-time monitoring for extended customer calls")

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")

        # Squad filter
        squad_options = ["All", "Chris", "Judith", "Josh", "Bea"]
        squad_filter = st.selectbox("Squad", squad_options, key="squad_filter")

        # Engineer filter
        df_all = get_updates()
        if not df_all.empty and 'engineer' in df_all.columns:
            engineers = ["All"] + sorted(df_all['engineer'].unique().tolist())
        else:
            engineers = ["All"]
        engineer_filter = st.selectbox("Engineer", engineers, key="engineer_filter")

        # Date range filter
        date_options = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "All Time"]
        date_filter = st.selectbox("Date Range", date_options, index=4, key="date_filter")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh (every 5 seconds)", value=True)

        # Manual refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Get data
    df = get_updates()

    if df.empty:
        st.warning("📭 No data available. Waiting for long call updates from engineers...")
        return

    # Apply filters
    filtered_df = df.copy()

    # Squad filter
    if squad_filter != "All" and 'squad' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['squad'].str.contains(squad_filter, case=False, na=False)]

    # Engineer filter
    if engineer_filter != "All" and 'engineer' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['engineer'] == engineer_filter]

    # Date filter
    if 'timestamp' in filtered_df.columns:
        now = datetime.now(MANILA_TZ)
        if date_filter == "Today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered_df = filtered_df[filtered_df['timestamp'] >= start_of_day]
        elif date_filter == "Yesterday":
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            filtered_df = filtered_df[(filtered_df['timestamp'] >= start) & (filtered_df['timestamp'] < end)]
        elif date_filter == "Last 7 Days":
            week_ago = now - timedelta(days=7)
            filtered_df = filtered_df[filtered_df['timestamp'] >= week_ago]
        elif date_filter == "Last 30 Days":
            month_ago = now - timedelta(days=30)
            filtered_df = filtered_df[filtered_df['timestamp'] >= month_ago]

    # ===== METRICS =====
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 TOTAL", len(filtered_df))

    with col2:
        # Active = updates in last hour
        if 'timestamp' in filtered_df.columns:
            one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)
            active_count = len(filtered_df[filtered_df['timestamp'] > one_hour_ago])
        else:
            active_count = 0
        st.metric("🟢 ACTIVE", active_count)

    with col3:
        # Recent = unique TIDs in last hour
        if 'timestamp' in filtered_df.columns and 'transactionId' in filtered_df.columns:
            one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)
            recent_tids = filtered_df[filtered_df['timestamp'] > one_hour_ago]['transactionId'].nunique()
        else:
            recent_tids = 0
        st.metric("⏰ RECENT", recent_tids)

    # ===== RECENT ACTIVITIES =====
    st.markdown("---")
    st.header("📢 Recent Activities (Last Hour)")

    if 'timestamp' in filtered_df.columns:
        one_hour_ago = datetime.now(MANILA_TZ) - timedelta(hours=1)
        recent = filtered_df[filtered_df['timestamp'] > one_hour_ago]

        if not recent.empty:
            for idx, update in recent.iterrows():
                time_str = update['timestamp'].strftime('%I:%M %p')
                engineer = update.get('engineer', 'Unknown')
                squad = update.get('squad', 'Unknown')
                tid = update.get('transactionId', 'N/A')
                update_type = update.get('updateType', 'initial')

                if update_type == 'initial':
                    issue = update.get('issue', 'N/A')
                    st.success(f"🟢 **{time_str} - {engineer} ({squad})**\n\nTID: {tid} - INITIAL: \"{issue}\"")
                else:
                    update_text = update.get('updateText', 'N/A')
                    st.info(f"🟢 **{time_str} - {engineer} ({squad})**\n\nTID: {tid} - UPDATE: \"{update_text}\"")
        else:
            st.info("No recent activities in the last hour")

    # ===== BY ENGINEER =====
    st.markdown("---")
    st.header("👨‍💻 By Engineer")

    if 'engineer' in filtered_df.columns and 'transactionId' in filtered_df.columns:
        # Group by engineer
        for engineer in filtered_df['engineer'].unique():
            eng_data = filtered_df[filtered_df['engineer'] == engineer]
            squad = eng_data.iloc[0].get('squad', 'Unknown') if not eng_data.empty else 'Unknown'
            unique_calls = eng_data['transactionId'].nunique()

            with st.expander(f"👤 {engineer} ({squad}) - {unique_calls} call(s)"):
                # Group by Transaction ID
                for tid in eng_data['transactionId'].unique():
                    tid_data = eng_data[eng_data['transactionId'] == tid].sort_values('timestamp')

                    st.markdown(f"**📞 TID: {tid}** - {len(tid_data)} update(s)")

                    # Show timeline
                    for idx, update in tid_data.iterrows():
                        time_str = update['timestamp'].strftime('%I:%M %p')
                        update_type = update.get('updateType', 'initial')

                        if update_type == 'initial':
                            st.info(f"⏰ **{time_str} - INITIAL**\n\n"
                                   f"Issue: {update.get('issue', 'N/A')}\n\n"
                                   f"Reason: {update.get('reason', 'N/A')}")
                        else:
                            st.success(f"⏰ **{time_str} - UPDATE**\n\n"
                                      f"{update.get('updateText', 'N/A')}")

                    st.markdown("---")

    # ===== BY DATE =====
    st.markdown("---")
    st.header("📅 By Date")

    if 'timestamp' in filtered_df.columns:
        # Group by date
        filtered_df['date'] = filtered_df['timestamp'].dt.date
        dates = sorted(filtered_df['date'].unique(), reverse=True)

        for date in dates:
            date_data = filtered_df[filtered_df['date'] == date]
            date_str = date.strftime('%B %d, %Y')

            with st.expander(f"📅 {date_str} - {len(date_data)} update(s)"):
                for idx, update in date_data.iterrows():
                    time_str = update['timestamp'].strftime('%I:%M %p')
                    engineer = update.get('engineer', 'Unknown')
                    tid = update.get('transactionId', 'N/A')
                    update_type = update.get('updateType', 'initial')

                    if update_type == 'initial':
                        issue = update.get('issue', 'N/A')
                        st.info(f"**{time_str} - {engineer}** - TID: {tid}\n\nIssue: {issue}")
                    else:
                        update_text = update.get('updateText', 'N/A')
                        st.success(f"**{time_str} - {engineer}** - TID: {tid}\n\nUpdate: {update_text}")

    # Footer
    st.markdown("---")
    st.markdown("<div class='footer'>TrendLife | Where intelligence meets care<br>Long Call Update Dashboard v1.0</div>", unsafe_allow_html=True)

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

# ============================================
# MAIN ROUTER
# ============================================
def main():
    if not check_password():
        return

    # Get view type from URL parameter
    params = st.query_params
    view_type = params.get("view", "squad")  # Default to squad lead view

    # Sidebar - View selector
    with st.sidebar:
        st.header("👁️ View")

        view_options = {
            "Squad Lead View": "squad",
            "Engineer View": "engineer"
        }

        selected_view = st.radio(
            "Select View",
            options=list(view_options.keys()),
            index=0 if view_type == "squad" else 1
        )

        # Update URL parameter if changed
        if view_options[selected_view] != view_type:
            st.query_params["view"] = view_options[selected_view]
            st.rerun()

    # Route to appropriate view
    if view_type == "engineer":
        engineer_view()
    else:
        squad_lead_view()

if __name__ == "__main__":
    main()
