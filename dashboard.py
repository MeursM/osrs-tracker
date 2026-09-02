import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import os

# --- PAGE SETUP ---
st.set_page_config(
    page_title="GIM Wise Old Man Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM DARK THEME STYLING ---
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .profile-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid #21262d;
    }
    .profile-avatar {
        width: 54px;
        height: 54px;
        border-radius: 50%;
        background-color: #161b22;
        border: 2px solid #30363d;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    .profile-title {
        font-size: 24px;
        font-weight: 700;
        color: #f0f6fc;
        margin: 0;
    }
    .profile-subtitle {
        font-size: 13px;
        color: #8b949e;
        margin: 0;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 12px 16px;
    }
    .metric-label {
        font-size: 12px;
        color: #8b949e;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 14px;
        font-weight: 600;
        color: #f0f6fc;
    }
    
    /* WOM Record Card Styles */
    .record-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }
    .record-title {
        font-size: 16px;
        font-weight: 700;
        color: #f0f6fc;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .record-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px dashed #21262d;
        font-size: 12px;
    }
    .record-row:last-child {
        border-bottom: none;
    }
    .record-timeframe {
        color: #8b949e;
    }
    .record-gain-green {
        color: #3fb950;
        font-weight: 700;
    }
    .record-muted {
        color: #484f58;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #c9d1d9 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS ---
DB_FILE = "gim_tracker.db"

LEVEL_XP = [0, 0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833, 2107, 2411, 2746, 3115, 3523, 3973, 4470, 5018, 5624, 6291, 7028, 7842, 8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406, 24815, 27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983, 75127, 83014, 91721, 101333, 111945, 123660, 136594, 150872, 166636, 184040, 203254, 224466, 247886, 273742, 302288, 333804, 368599, 407015, 449428, 496254, 548886, 607652, 675026, 751472, 837999, 936588, 1048576, 1175659, 1321256, 1488065, 1677922, 1894393, 2139645, 2416592, 2730671, 3089470, 3500431, 3970406, 4507715, 5120921, 5821810, 6625521, 7552451, 8647828, 9921681, 11405296, 13103290, 15063236, 17328725, 19949292, 22968871, 26659591, 31199282, 36199861, 42987183, 51063428, 60263407, 71523778, 84292233, 99631662, 117997889, 139916727, 167659943, 201553896, 243330185, 294204840, 354994290, 427926930, 515211955, 620693261, 748398671, 913311385, 1121393688, 1377692594, 1696069776, 2088741856, 2567686353, 3167979496, 3884577840, 4738381338, 5852126185, 7160000000, 13034431]

EHP_RATES = {
    "Attack": 85000, "Strength": 100000, "Defence": 85000, "Ranged": 120000, "Magic": 150000, "Prayer": 60000, "Hitpoints": 90000,
    "Mining": 55000, "Fishing": 60000, "Woodcutting": 65000, "Hunter": 110000, "Farming": 100000,
    "Cooking": 250000, "Crafting": 180000, "Fletching": 200000, "Smithing": 250000, "Herblore": 100000, "Firemaking": 220000, "Runecraft": 45000, "Runecrafting": 45000, "Construction": 200000,
    "Agility": 55000, "Thieving": 150000, "Slayer": 35000, "Sailing": 80000
}

# --- SQLITE DATA LOADERS ---
def get_connection():
    return sqlite3.connect(DB_FILE)

@st.cache_data(ttl=300)
def load_xp_data():
    if not os.path.exists(DB_FILE):
        return None
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM skills_log", conn)
    conn.close()
    if df.empty:
        return None
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

@st.cache_data(ttl=300)
def load_activities_data():
    if not os.path.exists(DB_FILE):
        return None
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM activities_log", conn)
    except Exception:
        conn.close()
        return None
    conn.close()
    if df.empty:
        return None
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Map DB column name 'activity' to 'activitie' to remain compatible with UI logic
    if 'activity' in df.columns:
        df.rename(columns={'activity': 'activitie'}, inplace=True)
        
    df['amount'] = df['amount'].apply(lambda x: 0 if x < 0 else x)
    return df

@st.cache_data(ttl=300)
def load_achievements_data():
    if not os.path.exists(DB_FILE):
        return None
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM achievements_log", conn)
    except Exception:
        conn.close()
        return None
    conn.close()
    if df.empty:
        return None
    
    # Standardize column naming from DB to expected UI names
    column_mapping = {
        'player': 'Player',
        'entry_name': 'Entry_Name',
        'old_value': 'Old_Value',
        'new_value': 'New_Value',
        'detected_timestamp': 'Detected_Timestamp'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    if 'Detected_Timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['Detected_Timestamp'])
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    df['date'] = df['timestamp'].dt.date
    return df

xp_df = load_xp_data()
act_df = load_activities_data()
achievements_df = load_achievements_data()

if xp_df is None:
    st.error(f"❌ Database file ({DB_FILE}) or XP table not found/empty.")
    st.stop()

all_players = sorted(xp_df['player'].unique().tolist())

# --- HEADER SECTION ---
h1, h2 = st.columns([3, 1])

with h1:
    selected_player = st.selectbox("👤 Switch Active Player Profile", all_players, index=0)
    
    p_df_raw = xp_df[xp_df['player'] == selected_player]
    last_snap = p_df_raw['timestamp'].max()
    time_diff = datetime.now() - last_snap if pd.notnull(last_snap) else timedelta(0)
    mins_ago = int(time_diff.total_seconds() // 60)
    
    st.markdown(f"""
        <div class="profile-header">
            <div class="profile-avatar">🛡️</div>
            <div>
                <h1 class="profile-title">{selected_player}</h1>
                <p class="profile-subtitle">Group Ironman Member · Last updated {mins_ago} minutes ago</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with h2:
    st.write("")
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Update Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with b2:
        st.button("•••", use_container_width=True)

st.write("")

# --- NAVIGATION TABS ---
nav_tabs = ["Overview", "Gained", "Bosses & Activities", "Achievements"]
selected_tab = st.radio("Navigation", nav_tabs, index=2, horizontal=True, label_visibility="collapsed")

st.divider()

# --- TOP METRICS CARDS ---
earliest_snap = p_df_raw['timestamp'].min()
sc1, sc2, sc3, sc4 = st.columns(4)

with sc1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last updated</div>
            <div class="metric-value">{mins_ago} minutes ago</div>
        </div>
    """, unsafe_allow_html=True)

with sc2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Last progressed</div>
            <div class="metric-value">{p_df_raw['date'].max()}</div>
        </div>
    """, unsafe_allow_html=True)

with sc3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Earliest snapshot in period</div>
            <div class="metric-value">{earliest_snap.strftime('%Y-%m-%d') if pd.notnull(earliest_snap) else 'N/A'}</div>
        </div>
    """, unsafe_allow_html=True)

with sc4:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Exp drop in</div>
            <div class="metric-value">Active Tracker</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# =========================================================
# TAB: GAINED
# =========================================================
if selected_tab == "Gained":
    st.subheader("Gained")
    
    ctrl1, ctrl2, ctrl3 = st.columns([3, 1, 1])
    with ctrl1:
        timeframe = st.selectbox("Timeframe Window", ["Week", "Month", "Year", "All Time"], index=0)
    with ctrl2:
        category = st.selectbox("Category Filter", ["Skills", "Bosses & Activities"], index=0)
    with ctrl3:
        pass

    max_date = p_df_raw['date'].max()
    if timeframe == "Week":
        start_target = max_date - timedelta(days=7)
    elif timeframe == "Month":
        start_target = max_date - timedelta(days=30)
    elif timeframe == "Year":
        start_target = max_date - timedelta(days=365)
    else:
        start_target = p_df_raw['date'].min()

    st.caption(f"{selected_player}'s gains in the last **{timeframe.lower()}** ({start_target} to {max_date})")

    period_df = p_df_raw[(p_df_raw['date'] >= start_target) & (p_df_raw['date'] <= max_date)]
    
    if not period_df.empty:
        start_records = period_df.sort_values('timestamp').groupby('skill').first().reset_index()
        end_records = period_df.sort_values('timestamp').groupby('skill').last().reset_index()
        
        merged_gains = pd.merge(end_records, start_records, on='skill', suffixes=('_end', '_start'))
        merged_gains['Exp.'] = merged_gains['xp_end'] - merged_gains['xp_start']
        merged_gains['Levels'] = merged_gains['level_end'] - merged_gains['level_start']
        
        merged_gains['EHP'] = merged_gains.apply(
            lambda r: round(r['Exp.'] / EHP_RATES.get(r['skill'], 100000), 2) if r['Exp.'] > 0 else 0.0, axis=1
        )
        
        display_skills = merged_gains[['skill', 'Exp.', 'Levels', 'EHP']].copy()
        display_skills.rename(columns={'skill': 'Skill'}, inplace=True)
        
        left_col, right_col = st.columns([4, 5])
        
        with left_col:
            st.write("**Skills Summary**")
            selection_event = st.dataframe(
                display_skills,
                column_config={
                    "Skill": st.column_config.TextColumn("Skill"),
                    "Exp.": st.column_config.NumberColumn("Exp.", format="%d"),
                    "Levels": st.column_config.NumberColumn("Levels", format="%d"),
                    "EHP": st.column_config.NumberColumn("EHP", format="%.2f"),
                },
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                height=800
            )
            
            selected_skill = "Overall"
            if len(selection_event.selection.rows) > 0:
                selected_idx = selection_event.selection.rows[0]
                selected_skill = display_skills.iloc[selected_idx]['Skill']
        
        with right_col:
            skill_row = merged_gains[merged_gains['skill'] == selected_skill]
            
            if not skill_row.empty:
                exp_gained_val = skill_row['Exp.'].values[0]
                xp_start_val = skill_row['xp_start'].values[0]
                xp_end_val = skill_row['xp_end'].values[0]
                pct_gain = ((exp_gained_val / xp_start_val) * 100) if xp_start_val > 0 else 0.0
            else:
                exp_gained_val, xp_start_val, xp_end_val, pct_gain = 0, 0, 0, 0.0
            
            r_head1, r_head2 = st.columns([3, 2])
            with r_head1:
                st.markdown(f"### {selected_skill}")
                st.caption(f"{exp_gained_val:,} exp. gained")
            with r_head2:
                st.selectbox("Metric Type", ["Experience", "Levels", "EHP"], label_visibility="collapsed")
            
            st.markdown(f"""
                <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <span style="font-size: 11px; color: #8b949e;">Start</span><br/>
                            <strong>{xp_start_val:,}</strong>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #8b949e;">End</span><br/>
                            <strong>{xp_end_val:,}</strong>
                        </div>
                        <div>
                            <span style="font-size: 11px; color: #8b949e;">%</span><br/>
                            <strong>{pct_gain:.2f}%</strong>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("**Cumulative experience gained**")
            st.caption(f"A timeline of {selected_skill} experience over the past {timeframe.lower()}")
            
            skill_timeline = period_df[period_df['skill'] == selected_skill].sort_values('timestamp')
            
            if not skill_timeline.empty:
                fig_cum = px.line(skill_timeline, x="date", y="xp")
                fig_cum.update_traces(line_color="#2f81f7", line_width=2)
                fig_cum.update_layout(
                    plot_bgcolor="#0d1117",
                    paper_bgcolor="#0d1117",
                    font_color="#8b949e",
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=240,
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False)
                )
                st.plotly_chart(fig_cum, use_container_width=True)
            else:
                st.info("No data points recorded for this skill in the period.")
            
            st.write("**Daily experience gained**")
            st.caption(f"{selected_skill} experience gains bucketed by day")
            
            if len(skill_timeline) > 1:
                skill_timeline['daily_gain'] = skill_timeline['xp'].diff().fillna(0)
                skill_timeline['daily_gain'] = skill_timeline['daily_gain'].apply(lambda x: max(0, x))
                
                fig_bar = px.bar(skill_timeline, x="date", y="daily_gain")
                fig_bar.update_traces(marker_color="#238636")
                fig_bar.update_layout(
                    plot_bgcolor="#0d1117",
                    paper_bgcolor="#0d1117",
                    font_color="#8b949e",
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=200,
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.markdown("""
                    <div style="background-color: #0d1117; border: 1px solid #21262d; border-radius: 6px; height: 160px; display: flex; align-items: center; justify-content: center; color: #8b949e;">
                        No daily gains recorded
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No records found for the selected player in this timeframe.")

# =========================================================
# TAB: OVERVIEW
# =========================================================
elif selected_tab == "Overview":
    st.subheader("Player Overview & All-Skills Snapshot")
    latest_date_all = p_df_raw['date'].max()
    latest_player_skills = p_df_raw[p_df_raw['date'] == latest_date_all].sort_values('level', ascending=False)
    
    col_o1, col_o2 = st.columns([1, 1])
    with col_o1:
        st.write("**Current Skill Levels**")
        st.dataframe(
            latest_player_skills[['skill', 'level', 'xp']].rename(columns={'skill': 'Skill', 'level': 'Level', 'xp': 'Total XP'}),
            hide_index=True,
            use_container_width=True
        )
    with col_o2:
        st.write("**Skill XP Distribution**")
        fig_pie = px.pie(latest_player_skills[latest_player_skills['skill'] != 'Overall'], values='xp', names='skill', hole=0.4)
        fig_pie.update_layout(paper_bgcolor="#0d1117", font_color="#c9d1d9")
        st.plotly_chart(fig_pie, use_container_width=True)

# =========================================================
# TAB: BOSSES & ACTIVITIES (WISE OLD MAN RECORDS STYLE GRID)
# =========================================================
elif selected_tab == "Bosses & Activities":
    st.subheader("⚔️ Boss Kills & Activity Records")
    
    if act_df is not None and not act_df.empty:
        p_act = act_df[act_df['player'] == selected_player].copy()
        
        # 1. Filter out entries with 0 total kills / unranked
        p_act_positive = p_act.groupby('activitie')['amount'].max()
        valid_activities = p_act_positive[p_act_positive > 0].index.tolist()
        
        p_act_filtered = p_act[p_act['activitie'].isin(valid_activities)].copy()
        
        if not p_act_filtered.empty:
            activity_summary = []
            
            for act_name, group in p_act_filtered.groupby('activitie'):
                group = group.sort_values('timestamp')
                latest_val = group['amount'].iloc[-1]
                latest_date = group['date'].iloc[-1]
                latest_date_str = latest_date.strftime('%d %b %Y') if hasattr(latest_date, 'strftime') else str(latest_date)
                
                # Helper: get starting amount prior to or at window start relative to this activity's latest date
                def get_gain(days):
                    cutoff = latest_date - timedelta(days=days)
                    past_records = group[group['date'] <= cutoff]
                    if not past_records.empty:
                        base_val = past_records['amount'].iloc[-1]
                    else:
                        base_val = group['amount'].iloc[0]
                    return latest_val - base_val

                gain_day = get_gain(1)
                gain_week = get_gain(7)
                gain_month = get_gain(30)
                gain_year = get_gain(365)
                
                activity_summary.append({
                    'activitie': act_name,
                    'latest_val': latest_val,
                    'latest_date_str': latest_date_str,
                    'gain_day': gain_day,
                    'gain_week': gain_week,
                    'gain_month': gain_month,
                    'gain_year': gain_year,
                    'last_updated_sort': latest_date
                })
            
            summary_df = pd.DataFrame(activity_summary)
            
            # 2. Sort by Most Recent Activity/Kills at top
            summary_df = summary_df.sort_values(
                by=['last_updated_sort', 'gain_week', 'latest_val'], 
                ascending=[False, False, False]
            )
            
            # 3. Render 3-Column Card Grid
            cols = st.columns(3)
            
            for i, (_, row) in enumerate(summary_df.iterrows()):
                col_idx = i % 3
                with cols[col_idx]:
                    def format_gain_row(label, gain_val, date_str):
                        if gain_val > 0:
                            val_html = f'<span class="record-gain-green">+{gain_val:,}</span>'
                            date_html = f'<span style="font-size: 10px; color: #8b949e; margin-left: 6px;">{date_str}</span>'
                        else:
                            val_html = '<span class="record-muted">N/A</span>'
                            date_html = '<span style="font-size: 10px; color: #484f58; margin-left: 6px;">Not set</span>'
                            
                        return f'<div class="record-row"><span class="record-timeframe">{label}</span><div>{val_html}{date_html}</div></div>'

                    day_row = format_gain_row("Day", row['gain_day'], row['latest_date_str'])
                    week_row = format_gain_row("Week", row['gain_week'], row['latest_date_str'])
                    month_row = format_gain_row("Month", row['gain_month'], row['latest_date_str'])
                    year_row = format_gain_row("Year", row['gain_year'], row['latest_date_str'])

                    card_html = (
                        f'<div class="record-card">'
                        f'<div class="record-title">⚔️ {row["activitie"]}'
                        f'<span style="font-size: 12px; font-weight: normal; color: #8b949e; margin-left: auto;">Total: {row["latest_val"]:,}</span>'
                        f'</div>'
                        f'{day_row}'
                        f'{week_row}'
                        f'{month_row}'
                        f'{year_row}'
                        f'</div>'
                    )
                    
                    st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.info("No recorded boss kills or activity points for this player.")
    else:
        st.info("No activity data available.")

# =========================================================
# TAB: ACHIEVEMENTS (2 SUB-TABS: RECENTLY DONE & FINISHED)
# =========================================================
elif selected_tab == "Achievements":
    st.subheader("🎯 Quests & Achievements")
    
    if achievements_df is not None and not achievements_df.empty:
        p_ach = achievements_df[achievements_df['Player'] == selected_player].copy()
        
        # Sub-navigation for achievements
        sub_tab1, sub_tab2 = st.tabs(["⚡ Recently Done", "✅ Finished / All Completed"])
        
        # --- SUB-TAB 1: RECENTLY DONE ---
        with sub_tab1:
            r_col1, r_col2 = st.columns([1, 3])
            with r_col1:
                ach_timeframe = st.selectbox("Timeframe Filter", ["Day", "Week", "Month"], index=1)
            
            max_ach_date = p_ach['date'].max()
            if ach_timeframe == "Day":
                ach_start_date = max_ach_date - timedelta(days=1)
            elif ach_timeframe == "Week":
                ach_start_date = max_ach_date - timedelta(days=7)
            else:
                ach_start_date = max_ach_date - timedelta(days=30)
            
            # Filter entries completed/progressed in timeframe window
            recent_ach = p_ach[(p_ach['date'] >= ach_start_date) & (p_ach['New_Value'] > p_ach['Old_Value'])].copy()
            
            if not recent_ach.empty:
                recent_ach_sorted = recent_ach.sort_values('timestamp', ascending=False)
                
                st.caption(f"Showing achievements completed between **{ach_start_date}** and **{max_ach_date}**")
                
                m1, m2 = st.columns(2)
                m1.metric("Completions in Window", len(recent_ach_sorted))
                m2.metric("Last Achievement Date", str(recent_ach_sorted['date'].max()))
                
                st.write("")
                
                display_recent = pd.DataFrame({
                    "Date": recent_ach_sorted['date'].astype(str),
                    "Achievement / Quest": recent_ach_sorted['Entry_Name'],
                    "Status": recent_ach_sorted['New_Value'].apply(lambda x: "✅ Completed" if x >= 1 else f"Progress: {x}")
                })
                
                st.dataframe(display_recent, hide_index=True, use_container_width=True)
            else:
                st.info(f"No achievements or quests completed in the last {ach_timeframe.lower()}.")

        # --- SUB-TAB 2: FINISHED / ALL COMPLETED ---
        with sub_tab2:
            st.caption("Complete history of all finished quests, diaries, and combat achievements.")
            
            # Filter for completed entries (New_Value >= 1)
            completed_ach = p_ach[p_ach['New_Value'] >= 1].sort_values('timestamp').drop_duplicates('Entry_Name', keep='last')
            
            if not completed_ach.empty:
                f_col1, f_col2 = st.columns([2, 1])
                with f_col1:
                    search_query = st.text_input("🔍 Search Finished Entry", "", placeholder="e.g. Barrows, Dragon Slayer...")
                with f_col2:
                    category_filter = st.selectbox("Category", ["All", "Quest", "Diary", "Combat Achievement", "Music Track"])
                
                filtered_completed = completed_ach.copy()
                
                if search_query:
                    filtered_completed = filtered_completed[filtered_completed['Entry_Name'].str.contains(search_query, case=False, na=False)]
                
                if category_filter != "All":
                    filtered_completed = filtered_completed[filtered_completed['Entry_Name'].str.contains(category_filter, case=False, na=False)]
                
                st.metric("Total Finished Entries", len(filtered_completed))
                
                display_finished = pd.DataFrame({
                    "Achievement / Quest": filtered_completed['Entry_Name'],
                    "Status": "✅ Finished",
                    "Completion Date": filtered_completed['date'].astype(str)
                }).sort_values('Achievement / Quest')
                
                st.dataframe(display_finished, hide_index=True, use_container_width=True)
            else:
                st.info("No finished achievements recorded for this player.")
    else:
        st.info("No achievement data available.")
