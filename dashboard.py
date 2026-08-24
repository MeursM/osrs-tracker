import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="GIM Equans Analytics", layout="wide")
st.title("🛡️ Group Ironman Equans Advanced Dashboard")

# --- SKILL CATEGORY MAPPINGS ---
COMBAT_SKILLS = ["Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer", "Magic"]
GATHERING_SKILLS = ["Mining", "Fishing", "Woodcutting", "Hunter", "Farming"]
ARTISAN_SKILLS = ["Cooking", "Crafting", "Fletching", "Smithing", "Herblore", "Firemaking", "Runecraft", "Construction"]
SUPPORT_SKILLS = ["Agility", "Thieving", "Slayer", "Sailing"]

# Baseline Ironman EHP Rates (XP / Hour) for Time-to-Target Estimations
EHP_RATES = {
    "Attack": 85000, "Strength": 100000, "Defence": 85000, "Ranged": 120000, "Magic": 150000, "Prayer": 60000, "Hitpoints": 90000,
    "Mining": 55000, "Fishing": 60000, "Woodcutting": 65000, "Hunter": 110000, "Farming": 100000,
    "Cooking": 250000, "Crafting": 180000, "Fletching": 200000, "Smithing": 250000, "Herblore": 100000, "Firemaking": 220000, "Runecraft": 45000, "Construction": 200000,
    "Agility": 55000, "Thieving": 150000, "Slayer": 35000, "Sailing": 80000
}

# Standard Quest Cape Prerequisites (e.g., SOTE, DS2, DT2)
QUEST_CAPES_REQ = {"Herblore": 70, "Mining": 72, "Smithing": 70, "Hunter": 70, "Woodcutting": 70, "Agility": 70, "Farming": 70, "Thieving": 70, "Construction": 70}

# Standard Level Experience Table
LEVEL_XP = [0, 0, 83, 174, 276, 388, 512, 650, 801, 969, 1154, 1358, 1584, 1833, 2107, 2411, 2746, 3115, 3523, 3973, 4470, 5018, 5624, 6291, 7028, 7842, 8740, 9730, 10824, 12031, 13363, 14833, 16456, 18247, 20224, 22406, 24815, 27473, 30408, 33648, 37224, 41171, 45529, 50339, 55649, 61512, 67983, 75127, 83014, 91721, 101333, 111945, 123660, 136594, 150872, 166636, 184040, 203209, 224389, 247786, 273642, 302228, 333804, 368699, 407239, 449782, 496686, 548404, 605522, 668517, 737927, 814445, 898807, 991728, 1094043, 1206735, 1331026, 1468240, 1619720, 1786912, 1971216, 2174257, 2398000, 2644563, 2916519, 3216480, 3547034, 3911361, 4312840, 4755255, 5242820, 5780362, 6372422, 7024982, 7744078, 8537750, 9412992, 10378872, 11443830, 12516410, 13034431]

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv("gim_xp_log.csv")
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    df_grouped = df.groupby(['date', 'player', 'skill'], as_index=False).agg({
        'xp': lambda x: int(round(x.mean())),
        'level': 'max'
    }).sort_values(by='date')
    return df_grouped

try:
    df = load_data()
    players = sorted(df['player'].unique().tolist())
    
    # Global Player Selection Filter
    selected_player = st.sidebar.selectbox("👤 Select Player Focus", players)
    player_df = df[df['player'] == selected_player]
    
    st.header(f"Recap & Analytics for {selected_player}")
    
    # -------------------------------------------------------------
    # 1. INDIVIDUAL WEEKLY RECAP
    # -------------------------------------------------------------
    st.subheader("🗓️ 7-Day Performance Snapshot")
    
    latest_date = player_df['date'].max()
    week_ago_date = latest_date - timedelta(days=7)
    
    recent_df = player_df[player_df['date'] >= week_ago_date]
    oldest_recent = recent_df[recent_df['date'] == recent_df['date'].min()]
    latest_recent = recent_df[recent_df['date'] == latest_date]
    
    merged_week = pd.merge(latest_recent, oldest_recent, on=['skill'], suffixes=('_now', '_then'))
    merged_week['xp_gained'] = merged_week['xp_now'] - merged_week['xp_then']
    merged_week['levels_gained'] = merged_week['level_now'] - merged_week['level_then']
    
    tot_xp_week = merged_week['xp_gained'].sum()
    tot_lvl_week = merged_week['levels_gained'].sum()
    active_days = player_df[player_df['date'] >= week_ago_date]['date'].nunique()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Weekly XP Gain", f"{tot_xp_week:,} XP")
    m2.metric("Levels Gained", f"+{tot_lvl_week}")
    m3.metric("Active Days (Last 7 Days)", f"{active_days} / 7 Days")
    
    st.divider()

    # -------------------------------------------------------------
    # 2. PROGRESSION & MILESTONES (EHP + Predictions + Spider)
    # -------------------------------------------------------------
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("🎯 Time-to-Target & EHP Remaining")
        
        latest_skills = latest_recent[latest_recent['skill'] != 'Overall']
        
        # Calculate EHP Hours remaining to hit key targets
        base70_ehp = 0
        base80_ehp = 0
        max_ehp = 0
        
        for _, row in latest_skills.iterrows():
            s = row['skill']
            rate = EHP_RATES.get(s, 50000)
            
            # Base 70 (737,927 XP)
            if row['xp'] < LEVEL_XP[70]: base70_ehp += (LEVEL_XP[70] - row['xp']) / rate
            # Base 80 (1,971,216 XP)
            if row['xp'] < LEVEL_XP[80]: base80_ehp += (LEVEL_XP[80] - row['xp']) / rate
            # Max (13,034,431 XP)
            if row['xp'] < 13034431: max_ehp += (13034431 - row['xp']) / rate
            
        t1, t2, t3 = st.columns(3)
        t1.metric("EHP to Base 70s", f"{round(base70_ehp, 1)} hrs")
        t2.metric("EHP to Base 80s", f"{round(base80_ehp, 1)} hrs")
        t3.metric("EHP to Max Cape", f"{round(max_ehp, 1)} hrs")
        
        # Level Up Date Predictions
        st.write("**Next Upcoming Level Predictions (At current weekly rate):**")
        daily_rate = tot_xp_week / 7 if tot_xp_week > 0 else 1
        
        predictions = []
        for _, row in latest_skills.iterrows():
            current_lvl = row['level']
            if current_lvl < 99:
                next_xp = LEVEL_XP[current_lvl + 1]
                needed = next_xp - row['xp']
                days_left = needed / daily_rate if daily_rate > 0 else 999
                pred_date = datetime.now() + timedelta(days=days_left)
                predictions.append({
                    "Skill": row['skill'], "Current Level": current_lvl, 
                    "Next Level": current_lvl + 1, "Est. Date": pred_date.strftime("%Y-%m-%d") if days_left < 365 else "365+ Days"
                })
        
        st.dataframe(pd.DataFrame(predictions).head(5), hide_index=True, use_container_width=True)

    with col_right:
        st.subheader("🕸️ Milestone Radar (Archetype Balance)")
        
        # Aggregate current XP into official archetypes
        cat_xp = {"Combat": 0, "Gathering": 0, "Artisan": 0, "Support": 0}
        for _, row in latest_skills.iterrows():
            s = row['skill']
            if s in COMBAT_SKILLS: cat_xp["Combat"] += row['xp']
            elif s in GATHERING_SKILLS: cat_xp["Gathering"] += row['xp']
            elif s in ARTISAN_SKILLS: cat_xp["Artisan"] += row['xp']
            elif s in SUPPORT_SKILLS: cat_xp["Support"] += row['xp']
            
        radar_df = pd.DataFrame(list(cat_xp.items()), columns=['Category', 'XP'])
        
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=radar_df['XP'], theta=radar_df['Category'], fill='toself', name=selected_player
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # -------------------------------------------------------------
    # 3. SESSION & ACTIVE ANALYTICS
    # -------------------------------------------------------------
    st.subheader("🔥 Daily Activity Heatmap & Velocity")
    
    # Calculate daily XP gains
    p_dates = player_df.groupby('date')['xp'].sum().reset_index()
    p_dates['daily_gain'] = p_dates['xp'].diff().fillna(0)
    
    c_heat, c_synergy = st.columns([2, 1])
    
    with c_heat:
        fig_bar = px.bar(
            p_dates, x='date', y='daily_gain', 
            title="Daily XP Contribution Trend", 
            labels={"date": "Date", "daily_gain": "XP Earned"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c_synergy:
        st.subheader("⚠️ Quest Cape Warnings")
        unmet = []
        for skill, req_lvl in QUEST_CAPES_REQ.items():
            current_lvl = latest_skills[latest_skills['skill'] == skill]['level'].values
            c_lvl = current_lvl[0] if len(current_lvl) > 0 else 1
            if c_lvl < req_lvl:
                unmet.append({"Skill": skill, "Current": c_lvl, "Required": req_lvl})
                
        if unmet:
            st.warning("Unmet prerequisites for Quest Cape:")
            st.dataframe(pd.DataFrame(unmet), hide_index=True, use_container_width=True)
        else:
            st.success("All Quest Cape skill prerequisites met!")

    st.divider()

    # -------------------------------------------------------------
    # 4. COMPARATIVE & CONTEXTUAL INSIGHTS
    # -------------------------------------------------------------
    c_donut, c_step = st.columns([1, 1])
    
    with c_donut:
        st.subheader("🍩 Overall XP Distribution")
        fig_donut = px.pie(
            latest_skills, values='xp', names='skill', 
            hole=0.4, title="Account XP Allocation"
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        
    with c_step:
        st.subheader("📈 Historical Level Growth")
        fig_step = px.line(
            player_df[player_df['skill'] == 'Overall'], 
            x='date', y='level', line_shape='hv', 
            title="Total Level Growth Step-Chart"
        )
        st.plotly_chart(fig_step, use_container_width=True)

except Exception as e:
    st.error(f"Error loading analytics layout: {e}")
