import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GIM Equans Tracker", layout="wide")

st.title("🛡️ Group Ironman Equans Progress Tracker")

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv("gim_xp_log.csv")
    
    # 1. Convert timestamp to Date only (YYYY-MM-DD), removing hours/minutes/seconds
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    # 2. Group by date, player, and skill to average multiple logs on the same day
    # Takes max level and mean XP (rounded) for any given day
    df_grouped = df.groupby(['date', 'player', 'skill'], as_index=False).agg({
        'xp': lambda x: int(round(x.mean())),
        'level': 'max'
    })
    
    # Sort chronologically
    df_grouped = df_grouped.sort_values(by='date')
    return df_grouped

try:
    df = load_data()

    # Sidebar Filter for Skills
    skill_list = sorted(df['skill'].unique().tolist())
    
    # Default to 'Overall' if available, otherwise first skill in list
    default_idx = skill_list.index("Overall") if "Overall" in skill_list else 0
    selected_skill = st.sidebar.selectbox("Select Skill", skill_list, index=default_idx)

    # Filter Data by Selected Skill
    filtered_df = df[df['skill'] == selected_skill]

    # XP Progress Chart
    st.subheader(f"{selected_skill} XP Over Time")
    
    fig = px.line(
        filtered_df, 
        x="date", 
        y="xp", 
        color="player", 
        markers=True,
        title=f"Total {selected_skill} XP Growth",
        labels={"date": "Date", "xp": "XP", "player": "Player"}
    )
    
    # Format x-axis to explicitly display dates
    fig.update_xaxes(type='category')
    fig.update_layout(hovermode="x unified")
    
    st.plotly_chart(fig, use_container_width=True)

    # Current Player Rankings Table
    st.subheader(f"Current {selected_skill} Rankings")
    
    # Get the latest entry date available for the selected skill
    latest_date = filtered_df['date'].max()
    latest_df = filtered_df[filtered_df['date'] == latest_date].copy()
    
    # Format XP with commas for readability (e.g. 1,500,000)
    latest_df['xp_formatted'] = latest_df['xp'].apply(lambda x: f"{x:,}")
    
    # Display table sorted by highest XP
    rankings = latest_df[['player', 'level', 'xp_formatted']].sort_values(by="level", ascending=False)
    rankings.columns = ['Player', 'Level', 'Total XP']
    
    st.dataframe(rankings, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")
