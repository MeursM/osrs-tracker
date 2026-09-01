import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(
    page_title="Player Dashboard - Gained",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Custom Styling to Match Wise Old Man Theme
st.markdown("""
<style>
    /* Dark Theme Backgrounds */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Header Profile Card */
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

    /* Metric Cards Grid */
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

    /* Subheader Section */
    .section-header {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 16px;
    }

    /* Target specific Streamlit elements for dark theme */
    div[data-baseweb="select"] > div {
        background-color: #0d1117 !important;
        border-color: #30363d !important;
        color: #c9d1d9 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header & Profile Banner
header_col1, header_col2 = st.columns([4, 1])

with header_col1:
    st.markdown("""
        <div class="profile-header">
            <div class="profile-avatar">🏆</div>
            <div>
                <h1 class="profile-title">Phome1</h1>
                <p class="profile-subtitle">Regular · Last updated 2 minutes ago</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with header_col2:
    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        st.button("Update", type="primary", use_container_width=True)
    with btn_col2:
        st.button("•••", use_container_width=True)

st.write("")

# 4. Navigation Sub-Header
nav_tabs = ["Overview", "Gained", "Competitions", "Groups", "Records", "Achievements", "Name Changes"]
selected_tab = st.radio("Navigation", nav_tabs, index=1, horizontal=True, label_visibility="collapsed")

st.divider()

# 5. Top Stats Cards
sc1, sc2, sc3, sc4 = st.columns(4)

with sc1:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Last updated</div>
            <div class="metric-value">2 minutes ago</div>
        </div>
    """, unsafe_allow_html=True)

with sc2:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Last progressed</div>
            <div class="metric-value">6 minutes ago</div>
        </div>
    """, unsafe_allow_html=True)

with sc3:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Earliest snapshot in period</div>
            <div class="metric-value">6 minutes ago</div>
        </div>
    """, unsafe_allow_html=True)

with sc4:
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Exp drop in</div>
            <div class="metric-value">in 1 week</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# 6. Main Dashboard Content Area
st.subheader("Gained")

# Control Dropdowns Row
ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 1, 1])
with ctrl_col1:
    st.caption("Phome1's gains in the last **week**")
with ctrl_col2:
    timeframe = st.selectbox("Timeframe", ["Week", "Month", "Year", "All Time"], label_visibility="collapsed")
with ctrl_col3:
    category = st.selectbox("Category", ["Skills", "Bosses", "Activities"], label_visibility="collapsed")

# 7. Split Layout: Table (Left) vs Detail Panel (Right)
left_col, right_col = st.columns([4, 5])

# Dummy Skill Data Structure
skills_data = [
    {"Skill": "EHP", "Exp.": 0, "Levels": 0, "Rank": 0, "EHP": 0},
    {"Skill": "Overall", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Attack", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
    {"Skill": "Defence", "Exp.": 0, "Levels": 0, "Rank": 0, "EHP": 0},
    {"Skill": "Strength", "Exp.": 0, "Levels": 0, "Rank": 0, "EHP": 0},
    {"Skill": "Hitpoints", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Ranged", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Prayer", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Magic", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Cooking", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Woodcutting", "Exp.": 0, "Levels": 0, "Rank": 0, "EHP": 0},
    {"Skill": "Fletching", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Fishing", "Exp.": 0, "Levels": 0, "Rank": 0, "EHP": 0},
    {"Skill": "Firemaking", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
    {"Skill": "Crafting", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
    {"Skill": "Smithing", "Exp.": 0, "Levels": 0, "Rank": -3, "EHP": 0},
    {"Skill": "Mining", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Herblore", "Exp.": 0, "Levels": 0, "Rank": -4, "EHP": 0},
    {"Skill": "Agility", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
    {"Skill": "Thieving", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
    {"Skill": "Slayer", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
    {"Skill": "Farming", "Exp.": 0, "Levels": 0, "Rank": 0, "EHP": 0},
    {"Skill": "Runecrafting", "Exp.": 0, "Levels": 0, "Rank": -1, "EHP": 0},
    {"Skill": "Hunter", "Exp.": 0, "Levels": 0, "Rank": -2, "EHP": 0},
]
df_skills = pd.DataFrame(skills_data)

with left_col:
    # Interactive Table Selection
    st.write("**Skills Summary**")
    
    # Using st.dataframe with selection enabled to emulate active skill row picking
    event = st.dataframe(
        df_skills,
        column_config={
            "Skill": st.column_config.TextColumn("Skill"),
            "Exp.": st.column_config.NumberColumn("Exp.", format="%d"),
            "Levels": st.column_config.NumberColumn("Levels", format="%d"),
            "Rank": st.column_config.NumberColumn("Rank", format="%d"),
            "EHP": st.column_config.NumberColumn("EHP", format="%d"),
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        height=850
    )

    # Determine selected skill (Default to Magic if none selected)
    selected_skill = "Magic"
    if len(event.selection.rows) > 0:
        row_idx = event.selection.rows[0]
        selected_skill = df_skills.iloc[row_idx]["Skill"]

with right_col:
    # Panel Title & Selector
    r_head1, r_head2 = st.columns([3, 2])
    with r_head1:
        st.markdown(f"### {selected_skill}")
        st.caption("0 exp. gained")
    with r_head2:
        st.selectbox("Metric Type", ["Experience", "Ranks", "EHP"], label_visibility="collapsed")
    
    # Start / End / Gain metrics row
    st.markdown("""
        <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <span style="font-size: 11px; color: #8b949e;">Start</span><br/>
                    <strong>1,941k</strong>
                </div>
                <div>
                    <span style="font-size: 11px; color: #8b949e;">End</span><br/>
                    <strong>1,941k</strong>
                </div>
                <div>
                    <span style="font-size: 11px; color: #8b949e;">%</span><br/>
                    <strong>0.00%</strong>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. Cumulative Experience Gained Plot
    st.write("**Cumulative experience gained**")
    st.caption(f"A timeline of {selected_skill} experience over the past week")
    
    # Generate flat plot data matching image
    dates = [datetime(2026, 8, 25) + timedelta(days=i) for i in range(7)]
    df_line = pd.DataFrame({"Date": dates, "XP": [1941000] * 7})
    
    fig_cum = px.line(df_line, x="Date", y="XP")
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

    # 2. Daily Experience Gained Plot (Empty state in screenshot)
    st.write("**Daily experience gained**")
    st.caption(f"{selected_skill} experience gains over the past week, bucketed by day")
    
    st.markdown("""
        <div style="background-color: #0d1117; border: 1px solid #21262d; border-radius: 6px; height: 180px; display: flex; align-items: center; justify-content: center; color: #8b949e; font-weight: 500;">
            No gains
        </div>
    """, unsafe_allow_html=True)

    st.write("")

    # 3. Heatmap Representation
    st.write("**Gains heatmap**")
    st.caption(f"A heatmap of the past year's {selected_skill} experience gains")
    
    # Dummy heatmap representation
    heatmap_data = pd.DataFrame(
        [[0]*24 for _ in range(7)],
        columns=[f"W{i}" for i in range(24)]
    )
    fig_heat = px.imshow(
        heatmap_data, 
        color_continuous_scale=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    )
    fig_heat.update_layout(
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        height=140,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_showscale=False
    )
    fig_heat.update_xaxes(visible=False)
    fig_heat.update_yaxes(visible=False)
    st.plotly_chart(fig_heat, use_container_width=True)
