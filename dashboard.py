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

    /* Player Achievement Square/Card Styles */
    .player-ach-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        min-height: 180px;
    }
    .player-ach-header {
        font-size: 16px;
        font-weight: 700;
        color: #58a6ff;
        padding-bottom: 8px;
        margin-bottom: 12px;
        border-bottom: 1px solid #30363d;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .ach-item {
        font-size: 12px;
        padding: 4px 0;
        color: #c9d1d9;
        display: flex;
        justify-content: space-between;
    }
    .ach-date {
        color: #8b949e;
        font-size: 10px;
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
DB_FILE_A = "gim_achievements.db"

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
    
def get_connection_A():
    return sqlite3.connect(DB_FILE_A)

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
    
    if 'activity' in df.columns:
        df.rename(columns={'activity': 'activity'}, inplace=True)
        
    df['score'] = df['score'].apply(lambda x: 0 if x < 0 else x)
    return df

@st.cache_data(ttl=300)
def load_achievements_data():
    if not os.path.exists(DB_FILE_A):
        return pd.DataFrame()
    
    conn = get_connection_A()
    df = pd.DataFrame()
    
    try:
        df = pd.read_sql_query("SELECT * FROM achievements_log", conn)
    except Exception:
        pass
        
    if df.empty:
        try:
            df_state = pd.read_sql_query("SELECT * FROM player_current_state", conn)
            if not df_state.empty:
                df = df_state.rename(columns={
                    'player': 'Player',
                    'entry_name': 'Entry_Name',
                    'status_value': 'New_Value',
                    'last_updated': 'Detected_Timestamp'
                })
                df['Old_Value'] = 0
        except Exception:
            pass

    conn.close()
    
    if df.empty:
        return pd.DataFrame()
        
    cols = {col: col.title() for col in df.columns}
    df.rename(columns=cols, inplace=True)
    
    time_col = None
    for possible in ['Detected_Timestamp', 'Timestamp', 'Detected_time', 'Date']:
        if possible in df.columns:
            time_col = possible
            break
            
    if time_col:
        df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
    else:
        df['timestamp'] = pd.Timestamp.now()
        
    df['New_Value'] = pd.to_numeric(df.get('New_Value', 1), errors='coerce').fillna(1)
    return df

xp_df = load_xp_data()
act_df = load_activities_data()
achievements_df = load_achievements_data()

if xp_df is None:
    st.error(f"❌ Database file ({DB_FILE}) or XP table not found/empty.")
    st.stop()

all_players = sorted(xp_df['player'].unique().tolist())

# --- MAIN NAVIGATION ---
main_tab_group, main_tab_indiv = st.tabs(["👥 Group Overview", "👤 Individual Profile"])

# =========================================================
# MAIN TAB 1: GROUP OVERVIEW
# =========================================================
with main_tab_group:
    st.markdown("""
        <div class="profile-header">
            <div class="profile-avatar">⚔️</div>
            <div>
                <h1 class="profile-title">Group Ironman Overview</h1>
                <p class="profile-subtitle">Comparing all group members across Skills, Bosses, and Achievements</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Calculate Current Snapshot per Player
    latest_date_group = xp_df['date'].max()
    latest_xp_df = xp_df[xp_df['date'] == latest_date_group].copy()

    # Calculate Total EHP per Player
    latest_xp_df['EHP'] = latest_xp_df.apply(
        lambda r: round(r['xp'] / EHP_RATES.get(r['skill'], 100000), 2) if r['skill'] != 'Overall' else 0, axis=1
    )
    player_ehp = latest_xp_df.groupby('player')['EHP'].sum().reset_index()

    # Extract Overall XP & Total Level
    overall_stats = latest_xp_df[latest_xp_df['skill'] == 'Overall'][['player', 'level', 'xp']].rename(
        columns={'level': 'Total Level', 'xp': 'Total XP'}
    )
    
    group_summary = pd.merge(overall_stats, player_ehp, on='player')
    group_summary = group_summary.sort_values(by='Total XP', ascending=False)

    # Top Metric Banner
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    with col_g1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Group Members</div>
                <div class="metric-value">{len(all_players)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_g2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Combined Total XP</div>
                <div class="metric-value">{group_summary['Total XP'].sum():,}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_g3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Combined EHP</div>
                <div class="metric-value">{group_summary['EHP'].sum():,.2f}</div>
            </div>
        """, unsafe_allow_html=True)
    with col_g4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Total Level</div>
                <div class="metric-value">{int(group_summary['Total Level'].mean()):,}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # Sub-tabs within Group Overview
    g_tab1, g_tab_prog, g_tab2, g_tab3 = st.tabs([
        "📊 Standings", 
        "📈 Group Progression & Charts", 
        "⚔️ Bosses & Activities", 
        "🎯 Group Achievements"
    ])

    with g_tab1:
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.write("**Leaderboard**")
            st.dataframe(
                group_summary,
                column_config={
                    "player": st.column_config.TextColumn("Player"),
                    "Total Level": st.column_config.NumberColumn("Total Level", format="%d"),
                    "Total XP": st.column_config.NumberColumn("Total XP", format="%d"),
                    "EHP": st.column_config.NumberColumn("EHP", format="%.2f"),
                },
                hide_index=True,
                use_container_width=True
            )

        with c_right:
            st.write("**Total XP Comparison**")
            fig_xp_comp = px.bar(
                group_summary, 
                x="player", 
                y="Total XP", 
                color="player",
                text_auto=',.0f'
            )
            fig_xp_comp.update_layout(
                plot_bgcolor="#0d1117",
                paper_bgcolor="#0d1117",
                font_color="#8b949e",
                showlegend=False,
                height=300,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_xp_comp, use_container_width=True)

        st.divider()

        st.write("**Skill Level Matrix**")
        pivoted_skills = latest_xp_df[latest_xp_df['skill'] != 'Overall'].pivot(
            index='skill', columns='player', values='level'
        ).fillna(1).astype(int)
        
        st.dataframe(pivoted_skills, use_container_width=True)

    # GROUP PROGRESSION OVER TIME PER CATEGORY (BASELINED AT 0)
    with g_tab_prog:
        st.subheader("📈 Group Relative Progression Over Time")
        
        gc1, gc2, gc3, gc4 = st.columns([2, 2, 2, 2])
        
        with gc1:
            data_type = st.selectbox("Category Type", ["Skills", "Bosses & Activities"], key="group_cat_type")
        
        with gc2:
            if data_type == "Skills":
                available_cats = sorted(xp_df['skill'].unique().tolist())
                selected_cat = st.selectbox("Select Skill", available_cats, index=available_cats.index("Overall") if "Overall" in available_cats else 0, key="group_cat_select")
            else:
                if act_df is not None and not act_df.empty:
                    available_cats = sorted(act_df['activity'].unique().tolist())
                    selected_cat = st.selectbox("Select Activity/Boss", available_cats, index=0, key="group_act_select")
                else:
                    available_cats = []
                    selected_cat = None
                    st.selectbox("Select Activity/Boss", ["None Available"], disabled=True)

        with gc3:
            timeframe_g = st.selectbox("Timeframe", ["Week", "Month", "Year", "All Time"], index=3, key="group_timeframe")

        with gc4:
            view_mode = st.selectbox("Display Mode", ["Individual Overlay", "Group Aggregate Total"], key="group_view_mode")

        st.write("")

        # Calculate Timeframe Cutoff
        max_dt = xp_df['date'].max()
        if timeframe_g == "Week":
            min_dt = max_dt - timedelta(days=7)
        elif timeframe_g == "Month":
            min_dt = max_dt - timedelta(days=30)
        elif timeframe_g == "Year":
            min_dt = max_dt - timedelta(days=365)
        else:
            min_dt = xp_df['date'].min()

        # Render Chart based on Selection
        if data_type == "Skills":
            cat_df = xp_df[(xp_df['skill'] == selected_cat) & (xp_df['date'] >= min_dt) & (xp_df['date'] <= max_dt)].copy()
            val_col = 'xp'
            unit_label = "Experience"
        else:
            if act_df is not None and not act_df.empty and selected_cat:
                cat_df = act_df[(act_df['activity'] == selected_cat) & (act_df['date'] >= min_dt) & (act_df['date'] <= max_dt)].copy()
                val_col = 'score'
                unit_label = "Kills / Score"
            else:
                cat_df = pd.DataFrame()

        if not cat_df.empty:
            cat_df = cat_df.sort_values('timestamp')

            # BASELINE TO ZERO: Compute relative gains starting at 0 from the start of the selected timeframe
            if view_mode == "Individual Overlay":
                start_vals = cat_df.groupby('player')[val_col].transform('first')
                cat_df['relative_val'] = cat_df[val_col] - start_vals
                y_chart_col = 'relative_val'
            else:
                agg_df = cat_df.groupby('date')[val_col].sum().reset_index()
                agg_df['relative_val'] = agg_df[val_col] - agg_df[val_col].iloc[0]
                y_chart_col = 'relative_val'

            ch_col1, ch_col2 = st.columns([1, 1])

            with ch_col1:
                st.write(f"**Gained {selected_cat} {unit_label} (Starting at 0)**")
                st.caption(f"Relative progression over time during the selected {timeframe_g.lower()}")
                
                if view_mode == "Individual Overlay":
                    fig_group_cum = px.line(cat_df, x="date", y=y_chart_col, color="player", labels={'relative_val': f'Gained {unit_label}'})
                else:
                    fig_group_cum = px.line(agg_df, x="date", y=y_chart_col, labels={'relative_val': f'Group Gained {unit_label}'})
                    fig_group_cum.update_traces(line_color="#2f81f7", line_width=2.5)

                fig_group_cum.update_layout(
                    plot_bgcolor="#0d1117",
                    paper_bgcolor="#0d1117",
                    font_color="#8b949e",
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=300,
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False)
                )
                st.plotly_chart(fig_group_cum, use_container_width=True)

            with ch_col2:
                st.write(f"**Daily {selected_cat} Gains**")
                st.caption(f"Daily increase in {selected_cat.lower()}")
                
                if view_mode == "Individual Overlay":
                    cat_df['daily_gain'] = cat_df.groupby('player')[val_col].diff().fillna(0)
                    cat_df['daily_gain'] = cat_df['daily_gain'].apply(lambda x: max(0, x))
                    fig_group_bar = px.bar(cat_df, x="date", y="daily_gain", color="player", barmode="group", labels={'daily_gain': f'Daily {unit_label}'})
                else:
                    agg_df['daily_gain'] = agg_df[val_col].diff().fillna(0)
                    agg_df['daily_gain'] = agg_df['daily_gain'].apply(lambda x: max(0, x))
                    fig_group_bar = px.bar(agg_df, x="date", y="daily_gain", labels={'daily_gain': f'Daily Group {unit_label}'})
                    fig_group_bar.update_traces(marker_color="#238636")

                fig_group_bar.update_layout(
                    plot_bgcolor="#0d1117",
                    paper_bgcolor="#0d1117",
                    font_color="#8b949e",
                    margin=dict(l=20, r=20, t=10, b=20),
                    height=300,
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor="#21262d", zeroline=False)
                )
                st.plotly_chart(fig_group_bar, use_container_width=True)
        else:
            st.info(f"No records available for {selected_cat} in the selected timeframe.")

    # =========================================================
    # TAB: GROUP BOSSES & ACTIVITIES (TIMEFRAME GAINS ONLY)
    # =========================================================
    with g_tab2:
        st.write("**Group Boss Kills & Activity Gains**")

        if 'group_act_filter' not in st.session_state:
            st.session_state.group_act_filter = "Week"

        b_day, b_week, b_month, b_year, b_all, _ = st.columns([1, 1, 1, 1, 1, 2])
        if b_day.button("Day", key="gab_day", use_container_width=True, type="primary" if st.session_state.group_act_filter == "Day" else "secondary"):
            st.session_state.group_act_filter = "Day"
            st.rerun()
        if b_week.button("Week", key="gab_week", use_container_width=True, type="primary" if st.session_state.group_act_filter == "Week" else "secondary"):
            st.session_state.group_act_filter = "Week"
            st.rerun()
        if b_month.button("Month", key="gab_month", use_container_width=True, type="primary" if st.session_state.group_act_filter == "Month" else "secondary"):
            st.session_state.group_act_filter = "Month"
            st.rerun()
        if b_year.button("Year", key="gab_year", use_container_width=True, type="primary" if st.session_state.group_act_filter == "Year" else "secondary"):
            st.session_state.group_act_filter = "Year"
            st.rerun()
        if b_all.button("All Time", key="gab_all", use_container_width=True, type="primary" if st.session_state.group_act_filter == "All Time" else "secondary"):
            st.session_state.group_act_filter = "All Time"
            st.rerun()

        st.divider()

        if act_df is not None and not act_df.empty:
            max_act_date = act_df['date'].max()
            tf = st.session_state.group_act_filter

            if tf == "Day":
                min_act_date = max_act_date - timedelta(days=1)
            elif tf == "Week":
                min_act_date = max_act_date - timedelta(days=7)
            elif tf == "Month":
                min_act_date = max_act_date - timedelta(days=30)
            elif tf == "Year":
                min_act_date = max_act_date - timedelta(days=365)
            else:
                min_act_date = act_df['date'].min()

            # Filter data up to the cutoff
            act_window = act_df[(act_df['date'] >= min_act_date) & (act_df['date'] <= max_act_date)].copy()

            if not act_window.empty:
                # Get start and end values per player/activity in window
                start_acts = act_window.sort_values('timestamp').groupby(['activity', 'player'])['score'].first().reset_index()
                end_acts = act_window.sort_values('timestamp').groupby(['activity', 'player'])['score'].last().reset_index()

                merged_act = pd.merge(end_acts, start_acts, on=['activity', 'player'], suffixes=('_end', '_start'))
                
                if tf == "All Time":
                    merged_act['Gain'] = merged_act['score_end']
                else:
                    merged_act['Gain'] = merged_act['score_end'] - merged_act['score_start']

                merged_act['Gain'] = merged_act['Gain'].apply(lambda x: max(0, x))

                # Pivot data to show Activity x Players
                act_pivot = merged_act.pivot(index='activity', columns='player', values='Gain').fillna(0).astype(int)
                
                # Add total group gain column
                act_pivot['Group Total Gain'] = act_pivot.sum(axis=1)

                # Filter out activities where NO ONE gained anything during the period
                active_pivot = act_pivot[act_pivot['Group Total Gain'] > 0].sort_values(by='Group Total Gain', ascending=False)

                if not active_pivot.empty:
                    st.caption(f"Showing **{len(active_pivot)}** bosses/activities completed or gained during the selected timeframe (**{tf}**)")
                    
                    column_cfgs = {
                        "Group Total Gain": st.column_config.NumberColumn("Group Total Gain", format="%d")
                    }
                    for p in all_players:
                        if p in active_pivot.columns:
                            column_cfgs[p] = st.column_config.NumberColumn(f"{p}", format="%d")

                    st.dataframe(active_pivot, column_config=column_cfgs, use_container_width=True)
                else:
                    st.info(f"No boss kills or activity points recorded in the selected timeframe (**{tf}**).")
            else:
                st.info(f"No activity records found within the timeframe (**{tf}**).")
        else:
            st.info("No activity data available.")

    # =========================================================
    # TAB: GROUP ACHIEVEMENTS (SQUARES PER PLAYER LAYOUT)
    # =========================================================
    with g_tab3:
        st.write("**Group Achievements & Quests Completed**")

        if 'group_ach_filter' not in st.session_state:
            st.session_state.group_ach_filter = "Week"

        a_day, a_week, a_month, a_year, a_all, _ = st.columns([1, 1, 1, 1, 1, 2])
        if a_day.button("Day", key="ga_day", use_container_width=True, type="primary" if st.session_state.group_ach_filter == "Day" else "secondary"):
            st.session_state.group_ach_filter = "Day"
            st.rerun()
        if a_week.button("Week", key="ga_week", use_container_width=True, type="primary" if st.session_state.group_ach_filter == "Week" else "secondary"):
            st.session_state.group_ach_filter = "Week"
            st.rerun()
        if a_month.button("Month", key="ga_month", use_container_width=True, type="primary" if st.session_state.group_ach_filter == "Month" else "secondary"):
            st.session_state.group_ach_filter = "Month"
            st.rerun()
        if a_year.button("Year", key="ga_year", use_container_width=True, type="primary" if st.session_state.group_ach_filter == "Year" else "secondary"):
            st.session_state.group_ach_filter = "Year"
            st.rerun()
        if a_all.button("All Time", key="ga_all", use_container_width=True, type="primary" if st.session_state.group_ach_filter == "All Time" else "secondary"):
            st.session_state.group_ach_filter = "All Time"
            st.rerun()

        st.divider()

    if achievements_df is not None and not achievements_df.empty:
                now = pd.Timestamp.now()
                tf_ach = st.session_state.group_ach_filter
    
                if tf_ach == "Day":
                    start_boundary = now.floor('D')
                elif tf_ach == "Week":
                    start_boundary = now - pd.Timedelta(days=7)
                elif tf_ach == "Month":
                    start_boundary = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                elif tf_ach == "Year":
                    start_boundary = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    start_boundary = pd.Timestamp.min
    
                # Ensure timestamps are uniform pandas datetimes and strip timezones for safe comparison
                ach_df_copy = achievements_df.copy()
                ach_df_copy['timestamp'] = pd.to_datetime(ach_df_copy['timestamp']).dt.tz_localize(None)
    
                # Filter completed achievements by period
                completed_ach = ach_df_copy[
                    (ach_df_copy['New_Value'] >= 1) & 
                    (ach_df_copy['timestamp'] >= start_boundary)
                ].sort_values('timestamp', ascending=False)
    
                # Display a Card / Square for each player side-by-side
                ach_cols = st.columns(len(all_players))
    
                for idx, player_name in enumerate(all_players):
                    player_completed = completed_ach[completed_ach['Player'] == player_name]
                    
                    with ach_cols[idx]:
                        ach_items_html = ""
                        if not player_completed.empty:
                            for _, row in player_completed.iterrows():
                                date_str = row['timestamp'].strftime('%b %d') if pd.notnull(row['timestamp']) else ""
                                ach_items_html += f"""
                                    <div class="ach-item">
                                        <span>✅ {row['Entry_Name']}</span>
                                        <span class="ach-date">{date_str}</span>
                                    </div>
                                """
                        else:
                            ach_items_html = '<div style="color: #484f58; font-size: 12px; font-style: italic;">No achievements in this timeframe</div>'
                
                        card_html = f"""
                            <div class="player-ach-card">
                                <div class="player-ach-header">
                                    <span>👤 {player_name}</span>
                                    <span style="font-size: 12px; color: #8b949e; font-weight: normal;">({len(player_completed)})</span>
                                </div>
                                {ach_items_html}
                            </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info("No achievement data available.")

# =========================================================
# MAIN TAB 2: INDIVIDUAL PROFILE (ORIGINAL DASHBOARD CODE)
# =========================================================
with main_tab_indiv:
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
            
            p_act_positive = p_act.groupby('activity')['score'].max()
            valid_activities = p_act_positive[p_act_positive > 0].index.tolist()
            
            p_act_filtered = p_act[p_act['activity'].isin(valid_activities)].copy()
            
            if not p_act_filtered.empty:
                activity_summary = []
                
                for act_name, group in p_act_filtered.groupby('activity'):
                    group = group.sort_values('timestamp')
                    latest_val = group['score'].iloc[-1]
                    latest_date = group['date'].iloc[-1]
                    latest_date_str = latest_date.strftime('%d %b %Y') if hasattr(latest_date, 'strftime') else str(latest_date)
                    
                    def get_gain(days):
                        cutoff = latest_date - timedelta(days=days)
                        past_records = group[group['date'] <= cutoff]
                        if not past_records.empty:
                            base_val = past_records['score'].iloc[-1]
                        else:
                            base_val = group['score'].iloc[0]
                        return latest_val - base_val

                    gain_day = get_gain(1)
                    gain_week = get_gain(7)
                    gain_month = get_gain(30)
                    gain_year = get_gain(365)
                    
                    activity_summary.append({
                        'activity': act_name,
                        'latest_val': latest_val,
                        'latest_date_str': latest_date_str,
                        'gain_day': gain_day,
                        'gain_week': gain_week,
                        'gain_month': gain_month,
                        'gain_year': gain_year,
                        'last_updated_sort': latest_date
                    })
                
                summary_df = pd.DataFrame(activity_summary)
                
                summary_df = summary_df.sort_values(
                    by=['last_updated_sort', 'gain_week', 'latest_val'], 
                    ascending=[False, False, False]
                )
                
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
                            f'<div class="record-title">⚔️ {row["activity"]}'
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
    # TAB: ACHIEVEMENTS
    # =========================================================
    elif selected_tab == "Achievements":
        st.subheader("🎯 Quests & Achievements")

        if 'ach_filter' not in st.session_state:
            st.session_state.ach_filter = "Day"

        st.write("**Filter Completion Period:**")
        col_day, col_week, col_month, col_year, _ = st.columns([1, 1, 1, 1, 2])

        if col_day.button("Day", use_container_width=True, type="primary" if st.session_state.ach_filter == "Day" else "secondary"):
            st.session_state.ach_filter = "Day"
            st.rerun()

        if col_week.button("Week", use_container_width=True, type="primary" if st.session_state.ach_filter == "Week" else "secondary"):
            st.session_state.ach_filter = "Week"
            st.rerun()

        if col_month.button("Month", use_container_width=True, type="primary" if st.session_state.ach_filter == "Month" else "secondary"):
            st.session_state.ach_filter = "Month"
            st.rerun()

        if col_year.button("Year", use_container_width=True, type="primary" if st.session_state.ach_filter == "Year" else "secondary"):
            st.session_state.ach_filter = "Year"
            st.rerun()

        st.divider()

        if achievements_df is not None and not achievements_df.empty:
            p_ach = achievements_df[
                (achievements_df['Player'] == selected_player) & 
                (achievements_df['New_Value'] >= 1)
            ].copy()

            if p_ach.empty:
                st.info(f"No completed achievement records found for player: {selected_player}")
            else:
                now = pd.Timestamp.now()
                selected_filter = st.session_state.ach_filter

                if selected_filter == "Day":
                    start_boundary = now.floor('D')
                    period_label = "today"
                elif selected_filter == "Week":
                    start_boundary = now - pd.Timedelta(days=7)
                    period_label = "in the last 7 days"
                elif selected_filter == "Month":
                    start_boundary = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    period_label = "this month"
                elif selected_filter == "Year":
                    start_boundary = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    period_label = "this year"

                filtered_ach = p_ach[p_ach['timestamp'] >= start_boundary].copy()

                if not filtered_ach.empty:
                    filtered_ach = filtered_ach.sort_values('timestamp', ascending=False)

                    st.metric(label=f"Completed {period_label.capitalize()}", value=len(filtered_ach))

                    display_df = pd.DataFrame({
                        "Achievement / Quest": filtered_ach['Entry_Name'],
                        "Completion Date": filtered_ach['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S'),
                        "Status": "✅ Completed"
                    })

                    st.dataframe(display_df, hide_index=True, use_container_width=True)
                else:
                    st.info(f"No achievements or quests completed {period_label}.")
        else:
            st.info("No achievement data available in the database.")
