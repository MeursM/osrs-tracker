import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="GIM Equans Analytics", layout="wide")
st.title("🛡️ Group Ironman Equans Dashboard")

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

QUEST_CAPES_REQ = {"Herblore": 70, "Mining": 72, "Smithing": 70, "Hunter": 70, "Woodcutting": 70, "Agility": 70, "Farming": 70, "Thieving": 70, "Construction": 70}
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
    
    # SETUP NAVIGATION TABS
    tab_group, tab_individual = st.tabs(["📊 Group Comparison", "👤 Individual Focus"])

    # =========================================================
    # TAB 1: GROUP COMPARISON VIEW
    # =========================================================
    with tab_group:
        st.header("Group Overview & Comparison")
        
        # Skill Filter
        skills = sorted(df['skill'].unique().tolist())
        def_idx = skills.index("Overall") if "Overall" in skills else 0
        selected_skill = st.selectbox("Compare Specific Skill", skills, index=def_idx)
        
        # 1. Timeline Chart (All Players)
        skill_df = df[df['skill'] == selected_skill]
        fig_line = px.line(
            skill_df, x="date", y="xp", color="player", markers=True,
            title=f"All Players: {selected_skill} XP Growth",
            labels={"date": "Date", "xp": "XP", "player": "Player"}
        )
        fig_line.update_xaxes(type='category')
        fig_line.update_layout(hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # 2. Side-by-side Leaderboard Table
        with col1:
            st.subheader(f"Current {selected_skill} Leaderboard")
            latest_date = skill_df['date'].max()
            latest_skill_df = skill_df[skill_df['date'] == latest_date].copy()
            latest_skill_df['Formatted XP'] = latest_skill_df['xp'].apply(lambda x: f"{x:,}")
            rankings = latest_skill_df[['player', 'level', 'Formatted XP']].sort_values(by="level", ascending=False)
            rankings.columns = ['Player', 'Level', 'Total XP']
            st.dataframe(rankings, hide_index=True, use_container_width=True)
            
        # 3. Weekly Progress Comparison Bar Chart
        with col2:
            st.subheader("7-Day XP Gains Comparison")
            week_ago = latest_date - timedelta(days=7)
            recent_group = skill_df[skill_df['date'] >= week_ago]
            
            oldest_g = recent_group[recent_group['date'] == recent_group['date'].min()]
            latest_g = recent_group[recent_group['date'] == latest_date]
            
            merged_g = pd.merge(latest_g, oldest_g, on=['player', 'skill'], suffixes=('_now', '_then'))
            merged_g['xp_gained'] = merged_g['xp_now'] - merged_g['xp_then']
            
            fig_bar_comp = px.bar(
                merged_g, x='player', y='xp_gained', color='player',
                title=f"{selected_skill} XP Gained (Last 7 Days)",
                text_auto=',d'
            )
            st.plotly_chart(fig_bar_comp, use_container_width=True)

        st.divider()
        
        # 4. Multi-Player Archetype Overlay Chart
        st.subheader("🕸️ Group Archetype Balance Comparison")
        latest_all = df[(df['date'] == latest_date) & (df['skill'] != 'Overall')]
        
        radar_rows = []
        for p in players:
            p_data = latest_all[latest_all['player'] == p]
            c_xp, g_xp, a_xp, s_xp = 0, 0, 0, 0
            for _, r in p_data.iterrows():
                sk = r['skill']
                if sk in COMBAT_SKILLS: c_xp += r['xp']
                elif sk in GATHERING_SKILLS: g_xp += r['xp']
                elif sk in ARTISAN_SKILLS: a_xp += r['xp']
                elif sk in SUPPORT_SKILLS: s_xp += r['xp']
            
            radar_rows.extend([
                {"Player": p, "Category": "Combat", "XP": c_xp},
                {"Player": p, "Category": "Gathering", "XP": g_xp},
                {"Player": p, "Category": "Artisan", "XP": a_xp},
                {"Player": p, "Category": "Support", "XP": s_xp}
            ])
            
        df_group_radar = pd.DataFrame(radar_rows)
        fig_group_radar = px.line_polar(
            df_group_radar, r='XP', theta='Category', color='Player', 
            line_close=True, title="Group Archetype Distribution Comparison"
        )
        st.plotly_chart(fig_group_radar, use_container_width=True)

    # =========================================================
    # TAB 2: INDIVIDUAL PLAYER FOCUS VIEW
    # =========================================================
    with tab_individual:
        selected_player = st.selectbox("👤 Select Player to Analyze", players)
        player_df = df[df['player'] == selected_player]
        
        st.header(f"Personal Analytics: {selected_player}")
        
        # 1. Weekly Snapshot
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

        # 2. Time-to-Target & Individual Radar
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("🎯 Time-to-Target (EHP Remaining)")
            latest_skills = latest_recent[latest_recent['skill'] != 'Overall']
            
            b70_ehp = sum([(LEVEL_XP[70] - r['xp']) / EHP_RATES.get(r['skill'], 50000) for _, r in latest_skills.iterrows() if r['xp'] < LEVEL_XP[70]])
            b80_ehp = sum([(LEVEL_XP[80] - r['xp']) / EHP_RATES.get(r['skill'], 50000) for _, r in latest_skills.iterrows() if r['xp'] < LEVEL_XP[80]])
            max_ehp = sum([(13034431 - r['xp']) / EHP_RATES.get(r['skill'], 50000) for _, r in latest_skills.iterrows() if r['xp'] < 13034431])
            
            t1, t2, t3 = st.columns(3)
            t1.metric("Base 70s", f"{round(b70_ehp, 1)} hrs")
            t2.metric("Base 80s", f"{round(b80_ehp, 1)} hrs")
            t3.metric("Max Cape", f"{round(max_ehp, 1)} hrs")
            
            # Predictions
            tot_xp_week = merged_week['xp_gained'].sum()
            daily_rate = tot_xp_week / 7 if tot_xp_week > 0 else 1
            predictions = []
            for _, row in latest_skills.iterrows():
                if row['level'] < 99:
                    needed = LEVEL_XP[row['level'] + 1] - row['xp']
                    days_left = needed / daily_rate if daily_rate > 0 else 999
                    predictions.append({
                        "Skill": row['skill'], "Current": row['level'], 
                        "Next": row['level'] + 1, "Est. Date": (datetime.now() + timedelta(days=days_left)).strftime("%Y-%m-%d") if days_left < 365 else "365+ Days"
                    })
            st.dataframe(pd.DataFrame(predictions).head(5), hide_index=True, use_container_width=True)

        with col_right:
            st.subheader("🕸️ Personal Archetype Profile")
            cat_xp = {"Combat": 0, "Gathering": 0, "Artisan": 0, "Support": 0}
            for _, r in latest_skills.iterrows():
                s = r['skill']
                if s in COMBAT_SKILLS: cat_xp["Combat"] += r['xp']
                elif s in GATHERING_SKILLS: cat_xp["Gathering"] += r['xp']
                elif s in ARTISAN_SKILLS: cat_xp["Artisan"] += r['xp']
                elif s in SUPPORT_SKILLS: cat_xp["Support"] += r['xp']
                
            fig_rad = go.Figure(data=go.Scatterpolar(r=list(cat_xp.values()), theta=list(cat_xp.keys()), fill='toself'))
            st.plotly_chart(fig_rad, use_container_width=True)

        st.divider()

        # 3. Heatmap & Quest Prerequisites
        c_heat, c_syn = st.columns([2, 1])
        with c_heat:
            st.subheader("🔥 Daily Activity Heatmap")
            p_dates = player_df.groupby('date')['xp'].sum().reset_index()
            p_dates['daily_gain'] = p_dates['xp'].diff().fillna(0)
            st.plotly_chart(px.bar(p_dates, x='date', y='daily_gain', labels={"daily_gain": "XP Earned"}), use_container_width=True)
            
        with c_syn:
            st.subheader("⚠️ Quest Cape Warnings")
            unmet = []
            for skill, req_lvl in QUEST_CAPES_REQ.items():
                cur = latest_skills[latest_skills['skill'] == skill]['level'].values
                c_lvl = cur[0] if len(cur) > 0 else 1
                if c_lvl < req_lvl: unmet.append({"Skill": skill, "Current": c_lvl, "Required": req_lvl})
            if unmet:
                st.warning("Missing Prerequisites:")
                st.dataframe(pd.DataFrame(unmet), hide_index=True, use_container_width=True)
            else:
                st.success("All Prerequisites Met!")

        st.divider()

        # 4. Donut & Step Growth
        c_don, c_step = st.columns([1, 1])
        with c_don:
            st.subheader("🍩 XP Distribution")
            st.plotly_chart(px.pie(latest_skills, values='xp', names='skill', hole=0.4), use_container_width=True)
        with c_step:
            st.subheader("📈 Level Step-Graph")
            st.plotly_chart(px.line(player_df[player_df['skill'] == 'Overall'], x='date', y='level', line_shape='hv'), use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
