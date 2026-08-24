import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GIM Equans Tracker", layout="wide")

st.title("🛡️ Group Ironman Equans Progress Tracker")

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv("gim_xp_log.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

try:
    df = load_data()

    # Sidebar Filter for Skills
    skill_list = df['skill'].unique().tolist()
    selected_skill = st.sidebar.selectbox("Select Skill", skill_list, index=0)

    # Filtered Data
    filtered_df = df[df['skill'] == selected_skill]

    # XP Progress Chart
    st.subheader(f"{selected_skill} XP Over Time")
    fig = px.line(
        filtered_df, 
        x="timestamp", 
        y="xp", 
        color="player", 
        markers=True,
        title=f"Total {selected_skill} XP Growth"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Display Current Stats Table
    st.subheader("Current Player Rankings")
    latest_date = df['timestamp'].max()
    latest_df = df[df['timestamp'] == latest_date]
    st.dataframe(latest_df[['player', 'skill', 'level', 'xp']].sort_values(by="xp", ascending=False))

except Exception as e:
    st.error(f"Waiting for initial data... Ensure `gim_xp_log.csv` is populated. ({e})")