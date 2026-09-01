import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# --- PAGE SETUP ---
st.set_page_config(
    page_title="GIM Wise Old Man Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- WOM CUSTOM DARK THEME STYLING ---
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
    div[data-baseweb="select"] > div {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        color: #c9d1d9 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS ---
LEVEL_XP = [0, 0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833, 2107, 2411, 2746, 3115, 3523, 3973, 4470, 5018, 5624, 6291, 7028, 7842, 8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406, 24815, 27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983, 75127, 83014, 91721, 101333, 111945, 123660, 136594, 150872, 166636, 184040, 203254, 224466, 247886, 273742, 302288, 333804, 368599, 407015, 449428, 496254, 548886, 607652, 675026, 751472, 837999, 936588, 1048576, 1175659, 1321256, 1488065, 1677922, 1894393, 2139645, 2416592, 2730671, 3089470, 3500431, 3970406, 4507715, 5120921, 5821810, 6625521, 7552451, 8647828, 9921681, 11405296, 13103290, 15063236, 17328725, 19949292, 22968871, 26659591, 31199282, 36199861, 42987183, 51063428, 60263407, 71523778, 84292233, 99631662, 117997889, 139916727, 167659943, 201553896, 243330185, 294204840, 354994290, 427926930, 515211955, 620693261, 748398671, 913311385, 1121393688, 1377692594, 1696069776, 2088741856, 2567686353, 3167979496, 3884577840, 4738381338, 5852126185, 7160000000, 13034431]

EHP_RATES = {
    "Attack": 85000, "Strength": 100000, "Defence": 85000, "Ranged": 120000, "Magic": 150000, "Prayer": 60000, "Hitpoints": 90000,
    "Mining": 55000, "Fishing": 60000, "Woodcutting": 65000, "Hunter": 110000, "Farming": 100000,
    "Cooking": 250000, "Crafting": 180000, "Fletching": 200000, "Smithing": 250000, "Herblore": 100000, "Firemaking": 220000, "Runecraft": 45000, "Runecrafting": 45000, "Construction": 200000,
    "Agility": 55000, "Thieving": 150000, "Slayer": 35000, "Sailing": 80000
}

# --- DATA LOADERS ---
@st.cache_data(ttl=300)
def load_xp_data():
    if not os.path.exists("gim_xp_log.csv"):
        return None
    df = pd.read_csv("gim_xp_log.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

@st.cache_data(ttl=300)
def load_activities_data():
    if not os.path.exists("gim_activities_log.csv"):
        return None
    df = pd.read_csv("gim_activities_log.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['amount'] = df['amount'].apply(lambda x: 0 if x < 0 else x)
    return df

@st.cache_data(ttl=300)
def load_achievements_data():
    if not os.path.exists("achievements_log.csv"):
        return None
    df = pd.read_csv("achievements_log.csv")
    df['timestamp'] = pd.to_datetime(df['Detected_Timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

xp_df = load_xp_data()
act_df = load_activities_data()
achievements_df = load_achievements_data()

if xp_df is None:
    st.error("❌ XP data (gim_xp_log.csv) not found in directory.")
    st.stop()

all_players = sorted(xp_df['player'].unique().tolist())

# --- HEADER SECTION ---
h1, h2 = st.columns([3, 1])

with h1:
    selected_player = st.selectbox("👤 Switch Active Player Profile", all_players, index=0)
    
    # Calculate profile subtitle metadata
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

# --- TOP NAVIGATION TABS ---
nav_tabs = ["Overview", "Gained", "Bosses & Activities", "Achievements"]
selected_tab = st.radio("Navigation", nav_tabs, index=1, horizontal=True, label_visibility="collapsed")

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
# TAB: GAINED (WOM UI LAYOUT WITH LIVE CSV DATA)
# =========================================================
if selected_tab == "Gained":
    st.subheader("Gained")
    
    # Filter Row
    ctrl1, ctrl2, ctrl3 = st.columns([3, 1, 1])
    
    with ctrl1:
        timeframe = st.selectbox("Timeframe Window", ["Week", "Month", "Year", "All Time"], index=0)
    with ctrl2:
        category = st.selectbox("Category Filter", ["Skills", "Bosses & Activities"], index=0)
    with ctrl3:
        pass

    # Timeframe calculation
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

    # Filter player records within chosen timeframe window
    period_df = p_df_raw[(p_df_raw['date'] >= start_target) & (p_df_raw['date'] <= max_date)]
    
    if not period_df.empty:
        # Determine starting and ending XP/levels per skill in window
        start_records = period_df.sort_values('timestamp').groupby('skill').first().reset_index()
        end_records = period_df.sort_values('timestamp').groupby('skill').last().reset_index()
        
        merged_gains = pd.merge(end_records, start_records, on='skill', suffixes=('_end', '_start'))
        merged_gains['Exp.'] = merged_gains['xp_end'] - merged_gains['xp_start']
        merged_gains['Levels'] = merged_gains['level_end'] - merged_gains['level_start']
        
        # Calculate EHP
        merged_gains['EHP'] = merged_gains.apply(
            lambda r: round(r['Exp.'] / EHP_RATES.get(r['skill'], 100000), 2) if r['Exp.'] > 0 else 0.0, axis=1
        )
        
        # Compute summary table dataframe
        display_skills = merged_gains[['skill', 'Exp.', 'Levels', 'EHP']].copy()
        display_skills.rename(columns={'skill': 'Skill'}, inplace=True)
        
        # Split WOM Layout (Left Table vs Right Detail Panel)
        left_col, right_col = st.columns([4, 5])
        
        with left_col:
            st.write("**Skills Summary**")
            
            # Interactive Streamlit Dataframe with single row select
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
            # Selected Skill Details
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
            
            # Start / End / % Box
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
            
            # Cumulative Graph
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
            
            # Daily Experience Gained Bar Chart
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
# TAB: BOSSES & ACTIVITIES
# =========================================================
elif selected_tab == "Bosses & Activities":
    st.subheader("⚔️ Boss Kills & Activity Logs")
    if act_df is not None and not act_df.empty:
        p_act = act_df[act_df['player'] == selected_player]
        latest_act_date = p_act['date'].max()
        latest_act = p_act[p_act['date'] == latest_act_date]
        
        st.dataframe(
            latest_act[['activitie', 'amount']].rename(columns={'activitie': 'Activity / Boss', 'amount': 'Count / KC'}),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No activity data available.")

# =========================================================
# TAB: ACHIEVEMENTS
# =========================================================
elif selected_tab == "Achievements":
    st.subheader("🎯 Quests, Diaries & Achievements")
    if achievements_df is not None and not achievements_df.empty:
        p_ach = achievements_df[achievements_df['Player'] == selected_player]
        st.dataframe(
            p_ach[['date', 'Entry_Name', 'New_Value']].rename(columns={'date': 'Date', 'Entry_Name': 'Quest / Achievement', 'New_Value': 'Status Code'}),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No achievement data available.")
