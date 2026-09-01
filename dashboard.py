import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="GIM Equans Analytics", layout="wide")
st.title("🛡️ Group Ironman Equans Dashboard")

# --- STATIC PLAYER COLOR MAPPING ---
PLAYER_COLORS = {
    "Mas120": "#1f77b4",    # Blue
    "MrBSvenB": "#ff7f0e",  # Orange
    "Phome1": "#2ca02c",    # Green
    "Darallax": "#d62728",   # Red
    "Vagijn": "#7F00FF"     # Violet
}

# --- CATEGORY DEFINITIONS ---
COMBAT_SKILLS = ["Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer", "Magic"]
GATHERING_SKILLS = ["Mining", "Fishing", "Woodcutting", "Hunter", "Farming"]
ARTISAN_SKILLS = ["Cooking", "Crafting", "Fletching", "Smithing", "Herblore", "Firemaking", "Runecraft", "Construction"]
SUPPORT_SKILLS = ["Agility", "Thieving", "Slayer", "Sailing"]

EHP_RATES = {
    "Attack": 85000, "Strength": 100000, "Defence": 85000, "Ranged": 120000, "Magic": 150000, "Prayer": 60000, "Hitpoints": 90000,
    "Mining": 55000, "Fishing": 60000, "Woodcutting": 65000, "Hunter": 110000, "Farming": 100000,
    "Cooking": 250000, "Crafting": 180000, "Fletching": 200000, "Smithing": 250000, "Herblore": 100000, "Firemaking": 220000, "Runecraft": 45000, "Construction": 200000,
    "Agility": 55000, "Thieving": 150000, "Slayer": 35000, "Sailing": 80000
}

LEVEL_XP = [0, 0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833, 2107, 2411, 2746, 3115, 3523, 3973, 4470, 5018, 5624, 6291, 7028, 7842, 8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406, 24815, 27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983, 75127, 83014, 91721, 101333, 111945, 123660, 136594, 150872, 166636, 184040, 203254, 224466, 247886, 273742, 302288, 333804, 368599, 407015, 449428, 496254, 548886, 607652, 675026, 751472, 837999, 936588, 1048576, 1175659, 1321256, 1488065, 1677922, 1894393, 2139645, 2416592, 2730671, 3089470, 3500431, 3970406, 4507715, 5120921, 5821810, 6625521, 7552451, 8647828, 9921681, 11405296, 13103290, 15063236, 17328725, 19949292, 22968871, 26659591, 31199282, 36199861, 42987183, 51063428, 60263407, 71523778, 84292233, 99631662, 117997889, 139916727, 167659943, 201553896, 243330185, 294204840, 354994290, 427926930, 515211955, 620693261, 748398671, 913311385, 1121393688, 1377692594, 1696069776, 2088741856, 2567686353, 3167979496, 3884577840, 4738381338, 5852126185, 7160000000, 13034431]

@st.cache_data(ttl=300)
def load_xp_data():
    """Load XP/Skills data"""
    if not os.path.exists("gim_xp_log.csv"):
        return None
    df = pd.read_csv("gim_xp_log.csv")
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    df_grouped = df.groupby(['date', 'player', 'skill'], as_index=False).agg({
        'xp': lambda x: int(round(x.mean())),
        'level': 'max'
    }).sort_values(by='date')
    return df_grouped

@st.cache_data(ttl=300)
def load_boss_data():
    """Load Boss kill data"""
    if not os.path.exists("boss_kills_log.csv"):
        return None
    df = pd.read_csv("boss_kills_log.csv")
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    df_grouped = df.groupby(['date', 'player', 'boss'], as_index=False).agg({
        'kills': 'max'
    }).sort_values(by='date')
    return df_grouped

@st.cache_data(ttl=300)
def load_achievements_data():
    """Load Achievements/Quests data"""
    if not os.path.exists("achievements_log.csv"):
        return None
    df = pd.read_csv("achievements_log.csv")
    df['timestamp'] = pd.to_datetime(df['Detected_Timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

try:
    # Load all data
    xp_df = load_xp_data()
    boss_df = load_boss_data()
    achievements_df = load_achievements_data()
    
    if xp_df is None:
        st.error("❌ XP data not found. Please run the scraper first.")
        st.stop()
    
    players = sorted(xp_df['player'].unique().tolist())
    all_dates = sorted(xp_df['date'].unique().tolist(), reverse=True)
    
    # NAVIGATION TABS
    tab_group, tab_individual, tab_bosses, tab_achievements = st.tabs([
        "📊 Group Comparison", 
        "👤 Individual Focus",
        "⚔️ Boss Tracking",
        "🎯 Achievements & Quests"
    ])

    # =========================================================
    # TAB 1: GROUP COMPARISON VIEW
    # =========================================================
    with tab_group:
        st.header("Group Overview & Comparison")
        
        # Skill Filter
        skills = sorted(xp_df['skill'].unique().tolist())
        def_idx = skills.index("Overall") if "Overall" in skills else 0
        selected_skill = st.selectbox("Compare Specific Skill", skills, index=def_idx)
        
        # 1. Timeline Chart (All Players)
        skill_df = xp_df[xp_df['skill'] == selected_skill]
        fig_line = px.line(
            skill_df, x="date", y="xp", color="player", 
            color_discrete_map=PLAYER_COLORS,
            markers=True,
            title=f"All Players: {selected_skill} XP Growth",
            labels={"date": "Date", "xp": "XP", "player": "Player"}
        )
        fig_line.update_xaxes(type='category')
        fig_line.update_layout(hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # 2. Side-by-side Leaderboard Table for Selected Skill
        with col1:
            st.subheader(f"Current {selected_skill} Leaderboard")
            latest_date = skill_df['date'].max()
            latest_skill_df = skill_df[skill_df['date'] == latest_date].copy()
            latest_skill_df['Formatted XP'] = latest_skill_df['xp'].apply(lambda x: f"{x:,}")
            rankings = latest_skill_df[['player', 'level', 'Formatted XP']].sort_values(by="level", ascending=False)
            rankings.columns = ['Player', 'Level', 'Total XP']
            st.dataframe(rankings, hide_index=True, use_container_width=True)
            
        # 3. Flexible XP Gains Comparison Bar Chart (Choose Window & Target Date)
        with col2:
            st.subheader("XP Gains Comparison")
            c_win, c_date = st.columns(2)
            with c_win:
                gain_window = st.radio("Time Window", ["7 Days", "30 Days"], horizontal=True)
            with c_date:
                chosen_end_date = st.selectbox("End Date", all_dates, index=0)
                
            days_back = 7 if gain_window == "7 Days" else 30
            start_target_date = chosen_end_date - timedelta(days=days_back)
            
            recent_group = skill_df[(skill_df['date'] >= start_target_date) & (skill_df['date'] <= chosen_end_date)]
            
            if not recent_group.empty:
                oldest_g = recent_group[recent_group['date'] == recent_group['date'].min()]
                latest_g = recent_group[recent_group['date'] == recent_group['date'].max()]
                
                merged_g = pd.merge(latest_g, oldest_g, on=['player', 'skill'], suffixes=('_now', '_then'))
                merged_g['xp_gained'] = merged_g['xp_now'] - merged_g['xp_then']
                
                fig_bar_comp = px.bar(
                    merged_g, x='player', y='xp_gained', color='player',
                    color_discrete_map=PLAYER_COLORS,
                    title=f"{selected_skill} XP Gained ({gain_window} up to {chosen_end_date})",
                    text_auto=',d'
                )
                st.plotly_chart(fig_bar_comp, use_container_width=True)
            else:
                st.info("No data available for the selected timeframe.")

        st.divider()
        
        # 4. Group XP Comparison Matrix Table (Skills as rows, Players as columns)
        st.subheader("📋 Latest Group XP Matrix (All Skills)")
        latest_all_df = xp_df[xp_df['date'] == latest_date].copy()
        
        # Pivot table: Rows = Skill, Columns = Player, Values = XP
        pivot_df = latest_all_df.pivot(index='skill', columns='player', values='xp')
        
        # Pandas 2.1+ compatible formatting
        if hasattr(pivot_df, 'map'):
            formatted_pivot = pivot_df.map(lambda x: f"{int(x):,}" if pd.notnull(x) else "0")
        else:
            formatted_pivot = pivot_df.applymap(lambda x: f"{int(x):,}" if pd.notnull(x) else "0")

        formatted_pivot.reset_index(inplace=True)
        formatted_pivot.rename(columns={'skill': 'Skill'}, inplace=True)
        
        st.dataframe(formatted_pivot, hide_index=True, use_container_width=True)

    # =========================================================
    # TAB 2: INDIVIDUAL PLAYER FOCUS VIEW
    # =========================================================
    with tab_individual:
        selected_player = st.selectbox("👤 Select Player to Analyze", players)
        player_df = xp_df[xp_df['player'] == selected_player].copy()
        player_color = PLAYER_COLORS.get(selected_player, "#1f77b4")
        
        st.header(f"Personal Analytics: {selected_player}")
        
        # Inner tabs for organizing personal data
        tab_p_overview, tab_p_evolution, tab_p_breakdown = st.tabs([
            "📈 Overview & Targets", 
            "📊 XP Evolution Charts", 
            "📅 Trained Skills Breakdown"
        ])

        # --- SUB-TAB 1: OVERVIEW & TARGETS ---
        with tab_p_overview:
            st.subheader("🗓️ 7-Day Performance Snapshot")
            latest_date = player_df['date'].max()
            week_ago_date = latest_date - timedelta(days=7)
            
            recent_df = player_df[player_df['date'] >= week_ago_date]
            oldest_recent = recent_df[recent_df['date'] == recent_df['date'].min()]
            latest_recent = recent_df[recent_df['date'] == latest_date]
            
            merged_week = pd.merge(latest_recent, oldest_recent, on=['skill'], suffixes=('_now', '_then'))
            merged_week['xp_gained'] = merged_week['xp_now'] - merged_week['xp_then']
            merged_week['levels_gained'] = merged_week['level_now'] - merged_week['level_then']
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Weekly XP Gain", f"{merged_week['xp_gained'].sum():,} XP")
            m2.metric("Levels Gained", f"+{merged_week['levels_gained'].sum()}")
            m3.metric("Active Days (Last 7 Days)", f"{recent_df['date'].nunique()} / 7 Days")
            
            st.divider()

            st.subheader("🎯 Time-to-Target (EHP Remaining)")
            latest_skills = latest_recent[latest_recent['skill'] != 'Overall']
            
            b70_ehp = sum([(LEVEL_XP[70] - r['xp']) / EHP_RATES.get(r['skill'], 50000) for _, r in latest_skills.iterrows() if r['xp'] < LEVEL_XP[70]])
            b80_ehp = sum([(LEVEL_XP[80] - r['xp']) / EHP_RATES.get(r['skill'], 50000) for _, r in latest_skills.iterrows() if r['xp'] < LEVEL_XP[80]])
            max_ehp = sum([(13034431 - r['xp']) / EHP_RATES.get(r['skill'], 50000) for _, r in latest_skills.iterrows() if r['xp'] < 13034431])
            
            t1, t2, t3 = st.columns(3)
            t1.metric("Base 70s Target", f"{round(b70_ehp, 1)} hrs")
            t2.metric("Base 80s Target", f"{round(b80_ehp, 1)} hrs")
            t3.metric("Max Cape Target", f"{round(max_ehp, 1)} hrs")
            
            tot_xp_week = merged_week['xp_gained'].sum()
            daily_rate = tot_xp_week / 7 if tot_xp_week > 0 else 1
            predictions = []
            for _, row in latest_skills.iterrows():
                if row['level'] < 99:
                    needed = LEVEL_XP[row['level'] + 1] - row['xp']
                    days_left = needed / daily_rate if daily_rate > 0 else 999
                    predictions.append({
                        "Skill": row['skill'], "Current Level": row['level'], 
                        "Next Level": row['level'] + 1, "Est. Date": (datetime.now() + timedelta(days=days_left)).strftime("%Y-%m-%d") if days_left < 365 else "365+ Days"
                    })
            st.dataframe(pd.DataFrame(predictions).head(5), hide_index=True, use_container_width=True)

            st.divider()

            c_don, c_step = st.columns([1, 1])
            with c_don:
                st.subheader("🍩 Current XP Breakdown")
                st.plotly_chart(px.pie(latest_skills, values='xp', names='skill', hole=0.4), use_container_width=True)
            with c_step:
                st.subheader("📈 Level Progression (Overall)")
                fig_step_chart = px.line(
                    player_df[player_df['skill'] == 'Overall'], 
                    x='date', y='level', line_shape='hv',
                    color_discrete_sequence=[player_color]
                )
                st.plotly_chart(fig_step_chart, use_container_width=True)

        # --- SUB-TAB 2: XP EVOLUTION CHARTS ---
        with tab_p_evolution:
            st.subheader("📈 XP Evolution per Skill")
            
            col_time, col_filter = st.columns([1, 2])
            with col_time:
                timeframe = st.selectbox("Select Timeframe Interval", ["Daily", "Weekly", "Monthly"])
            
            with col_filter:
                available_skills = sorted(player_df['skill'].unique().tolist())
                selected_skills = st.multiselect("Filter Skills to View", available_skills, default=["Overall"] if "Overall" in available_skills else available_skills[:3])

            p_df_evo = player_df.copy()
            p_df_evo['datetime'] = pd.to_datetime(p_df_evo['date'])

            if selected_skills:
                p_df_evo = p_df_evo[p_df_evo['skill'].isin(selected_skills)]

            if timeframe == "Weekly":
                p_df_evo['Period'] = p_df_evo['datetime'].dt.to_period('W').dt.start_time
            elif timeframe == "Monthly":
                p_df_evo['Period'] = p_df_evo['datetime'].dt.to_period('M').dt.start_time
            else:
                p_df_evo['Period'] = p_df_evo['datetime']

            resampled_df = p_df_evo.groupby(['Period', 'skill'], as_index=False)['xp'].max()

            fig_evo = px.line(
                resampled_df,
                x='Period',
                y='xp',
                color='skill',
                markers=True,
                title=f"{selected_player}'s XP Progress ({timeframe} View)",
                labels={"Period": "Date / Period", "xp": "XP", "skill": "Skill"}
            )
            fig_evo.update_layout(hovermode="x unified")
            st.plotly_chart(fig_evo, use_container_width=True)

        # --- SUB-TAB 3: TRAINED SKILLS BREAKDOWN TABLE ---
        with tab_p_breakdown:
            st.subheader("📋 Trained Skills Breakdown")
            
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                breakdown_type = st.radio("Group By Period", ["Weekly", "Monthly"], horizontal=True)
            
            player_df['datetime'] = pd.to_datetime(player_df['date'])
            
            if breakdown_type == "Weekly":
                player_df['period_str'] = player_df['datetime'].dt.to_period('W').astype(str)
            else:
                player_df['period_str'] = player_df['datetime'].dt.to_period('M').astype(str)
                
            available_periods = sorted(player_df['period_str'].unique().tolist(), reverse=True)
            
            with b_col2:
                selected_period = st.selectbox("Select Time Period", available_periods)
                
            # Filter data for selected period
            period_df = player_df[player_df['period_str'] == selected_period]
            
            if not period_df.empty:
                min_d = period_df['date'].min()
                max_d = period_df['date'].max()
                
                start_records = period_df[period_df['date'] == min_d]
                end_records = period_df[period_df['date'] == max_d]
                
                merged_breakdown = pd.merge(end_records, start_records, on='skill', suffixes=('_end', '_start'))
                merged_breakdown['xp_gained'] = merged_breakdown['xp_end'] - merged_breakdown['xp_start']
                merged_breakdown['levels_gained'] = merged_breakdown['level_end'] - merged_breakdown['level_start']
                
                # Filter OUT non-trained skills (XP gained > 0) and excluding 'Overall' for the breakdown
                trained_df = merged_breakdown[(merged_breakdown['xp_gained'] > 0) & (merged_breakdown['skill'] != 'Overall')].copy()
                
                if not trained_df.empty:
                    trained_df = trained_df.sort_values(by='xp_gained', ascending=False)
                    
                    # Summary metrics
                    sm1, sm2, sm3 = st.columns(3)
                    sm1.metric("Skills Trained", f"{len(trained_df)}")
                    sm2.metric("Total XP Gained", f"{trained_df['xp_gained'].sum():,} XP")
                    sm3.metric("Total Levels Gained", f"+{trained_df['levels_gained'].sum()}")
                    
                    # Clean up table for display
                    display_breakdown = pd.DataFrame({
                        "Skill": trained_df['skill'],
                        "XP Gained": trained_df['xp_gained'].apply(lambda x: f"{x:,}"),
                        "Levels Gained": trained_df['levels_gained'].apply(lambda x: f"+{x}" if x > 0 else "0"),
                        "Start Level": trained_df['level_start'],
                        "End Level": trained_df['level_end'],
                        "End Total XP": trained_df['xp_end'].apply(lambda x: f"{x:,}")
                    })
                    
                    st.dataframe(display_breakdown, hide_index=True, use_container_width=True)
                else:
                    st.info(f"No individual skill XP gained recorded for period: {selected_period}")
            else:
                st.info("No data available for this timeframe.")

    # =========================================================
    # TAB 3: BOSS TRACKING
    # =========================================================
    with tab_bosses:
        st.header("⚔️ Boss Kill Tracking")
        
        if boss_df is None or boss_df.empty:
            st.warning("⚠️ No boss data available yet. Boss tracker will start collecting data on the next run.")
        else:
            # Filter controls
            col_boss_filter = st.columns(3)
            
            with col_boss_filter[0]:
                selected_boss_player = st.selectbox("Select Player", sorted(boss_df['player'].unique()), key="boss_player")
            
            with col_boss_filter[1]:
                boss_names = sorted(boss_df['boss'].unique().tolist())
                selected_boss = st.selectbox("Select Boss", boss_names, key="boss_name")
            
            with col_boss_filter[2]:
                latest_boss_date = boss_df['date'].max()
                week_ago_boss_date = latest_boss_date - timedelta(days=7)
                boss_window = st.radio("Time Window", ["7 Days", "30 Days", "All Time"], horizontal=True, key="boss_window")
            
            # Apply filters
            filtered_boss_df = boss_df[boss_df['player'] == selected_boss_player]
            filtered_boss_df = filtered_boss_df[filtered_boss_df['boss'] == selected_boss]
            
            if boss_window == "7 Days":
                filtered_boss_df = filtered_boss_df[filtered_boss_df['date'] >= week_ago_boss_date]
            elif boss_window == "30 Days":
                filtered_boss_df = filtered_boss_df[filtered_boss_df['date'] >= (latest_boss_date - timedelta(days=30))]
            
            if not filtered_boss_df.empty:
                col_chart, col_stats = st.columns([2, 1])
                
                with col_chart:
                    st.subheader(f"{selected_boss} - {selected_boss_player}")
                    fig_boss_line = px.line(
                        filtered_boss_df, x="date", y="kills", 
                        color_discrete_sequence=[PLAYER_COLORS.get(selected_boss_player, "#1f77b4")],
                        markers=True,
                        title=f"Kill Count Over Time",
                        labels={"date": "Date", "kills": "Total Kills"}
                    )
                    fig_boss_line.update_xaxes(type='category')
                    st.plotly_chart(fig_boss_line, use_container_width=True)
                
                with col_stats:
                    latest_boss = filtered_boss_df[filtered_boss_df['date'] == filtered_boss_df['date'].max()]
                    oldest_boss = filtered_boss_df[filtered_boss_df['date'] == filtered_boss_df['date'].min()]
                    
                    if not latest_boss.empty and not oldest_boss.empty:
                        current_kills = latest_boss['kills'].values[0]
                        kills_gained = current_kills - oldest_boss['kills'].values[0]
                        
                        st.metric("Current Kills", f"{int(current_kills):,}")
                        st.metric("Kills Gained", f"+{int(kills_gained):,}")
                        st.metric("Date Range", f"{oldest_boss['date'].values[0]} to {latest_boss['date'].values[0]}")
                    else:
                        st.metric("Current Kills", "N/A")
            else:
                st.info("No data available for this boss in the selected time window.")
            
            st.divider()
            
            # Group Boss Comparison
            st.subheader("📊 Group Boss Comparison (Latest)")
            latest_all_bosses = boss_df[boss_df['date'] == boss_df['date'].max()]
            
            if not latest_all_bosses.empty:
                # Pivot: Rows = Boss, Columns = Player, Values = Kills
                pivot_bosses = latest_all_bosses.pivot(index='boss', columns='player', values='kills')
                
                if hasattr(pivot_bosses, 'map'):
                    formatted_bosses = pivot_bosses.map(lambda x: f"{int(x):,}" if pd.notnull(x) else "-")
                else:
                    formatted_bosses = pivot_bosses.applymap(lambda x: f"{int(x):,}" if pd.notnull(x) else "-")
                
                formatted_bosses.reset_index(inplace=True)
                formatted_bosses.rename(columns={'boss': 'Boss'}, inplace=True)
                
                st.dataframe(formatted_bosses, hide_index=True, use_container_width=True)

    # =========================================================
    # TAB 4: ACHIEVEMENTS & QUESTS
    # =========================================================
    with tab_achievements:
        st.header("🎯 Achievements, Quests & Diaries")
        
        if achievements_df is None or achievements_df.empty:
            st.warning("⚠️ No achievement data available yet. Achievement tracker will start collecting data on the next run.")
        else:
            # Filter controls
            col_ach_filter = st.columns(2)
            
            with col_ach_filter[0]:
                selected_ach_player = st.selectbox("Select Player", sorted(achievements_df['Player'].unique()), key="ach_player")
            
            with col_ach_filter[1]:
                ach_type = st.selectbox(
                    "Filter by Type",
                    ["All", "Quest", "Diary", "Combat Achievement", "Music Track"],
                    key="ach_type"
                )
            
            # Filter data
            filtered_ach_df = achievements_df[achievements_df['Player'] == selected_ach_player].copy()
            
            if ach_type != "All":
                filtered_ach_df = filtered_ach_df[filtered_ach_df['Entry_Name'].str.contains(ach_type, case=False, na=False)]
            
            if not filtered_ach_df.empty:
                # New Completions (where Old_Value < New_Value)
                new_completions = filtered_ach_df[filtered_ach_df['New_Value'] > filtered_ach_df['Old_Value']].copy()
                
                col_ach_stats = st.columns(3)
                with col_ach_stats[0]:
                    st.metric("Total Entries", len(filtered_ach_df['Entry_Name'].unique()))
                with col_ach_stats[1]:
                    st.metric("Recent Changes", len(new_completions))
                with col_ach_stats[2]:
                    st.metric("Last Updated", filtered_ach_df['date'].max() if not filtered_ach_df.empty else "N/A")
                
                st.divider()
                
                # Recent Completions Table
                if not new_completions.empty:
                    st.subheader("✨ Recent Completions")
                    new_completions_display = new_completions.sort_values('timestamp', ascending=False).head(20)
                    
                    display_ach = pd.DataFrame({
                        "Date": new_completions_display['date'],
                        "Entry": new_completions_display['Entry_Name'],
                        "Status": new_completions_display['New_Value'].apply(lambda x: "✅ Completed" if x == 1 else f"Progress: {x}"),
                    })
                    
                    st.dataframe(display_ach, hide_index=True, use_container_width=True)
                
                st.divider()
                
                # All Entries Status Table
                st.subheader("📋 All Entries Status")
                latest_ach_status = filtered_ach_df.sort_values('timestamp').drop_duplicates('Entry_Name', keep='last')
                
                status_display = pd.DataFrame({
                    "Entry": latest_ach_status['Entry_Name'],
                    "Status": latest_ach_status['New_Value'].apply(lambda x: "✅" if x == 1 else f"({x})"),
                    "Last Update": latest_ach_status['date']
                })
                
                status_display = status_display.sort_values('Entry')
                st.dataframe(status_display, hide_index=True, use_container_width=True)
            else:
                st.info("No achievement data available for this player/filter combination.")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.write(f"Details: {str(e)}")
