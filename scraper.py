import requests
import sqlite3
import pandas as pd
from datetime import datetime

# Group member list
group_members = ["Mas120", "MrBSvenB", "Phome1", "Darallax"]

# OSRS Skill List in order returned by official API
SKILLS = [
    "Overall", "Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer",
    "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing", "Firemaking",
    "Crafting", "Smithing", "Mining", "Herblore", "Agility", "Thieving",
    "Slayer", "Farming", "Runecraft", "Hunter", "Construction", "Sailing"
]

DB_NAME = "gim_tracker.db"

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Skills Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills_log (
            timestamp TEXT,
            player TEXT,
            skill TEXT,
            rank INTEGER,
            level INTEGER,
            xp INTEGER
        )
    ''')
    
    # Create Activities Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities_log (
            timestamp TEXT,
            player TEXT,
            activity TEXT,
            rank INTEGER,
            score INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()

def fetch_player_data(username):
    """Fetch player data using the JSON API (skills and activities)"""
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.json?player={username}"
    headers = {'User-Agent': 'GIM-Tracker-Script'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch data for {username}")
            return None, None
        
        data = response.json()
        timestamp = datetime.now().isoformat()
        
        # Extract Skills
        skills_data = data.get("skills", [])
        player_skills = []
        
        for skill_info in skills_data:
            skill_name = skill_info.get("name")
            if skill_name in SKILLS:
                player_skills.append({
                    "timestamp": timestamp,
                    "player": username,
                    "skill": skill_name,
                    "rank": skill_info.get("rank", -1),
                    "level": skill_info.get("level", 0),
                    "xp": skill_info.get("xp", 0)
                })
        
        # Extract Activities
        activities_data = data.get("activities", [])
        player_activities = []
        
        for activity_info in activities_data:
            player_activities.append({
                "timestamp": timestamp,
                "player": username,
                "activity": activity_info.get("name"),
                "rank": activity_info.get("rank", -1),
                "score": activity_info.get("score", -1)
            })
        
        return player_skills, player_activities
    
    except Exception as e:
        print(f"Error fetching data for {username}: {e}")
        return None, None

# Initialize Database Schema
init_db()

# Collect all data
all_skill_records = []
all_activity_records = []

for member in group_members:
    skills, activities = fetch_player_data(member)
    if skills:
        all_skill_records.extend(skills)
    if activities:
        all_activity_records.extend(activities)

# Save to SQLite Database
conn = sqlite3.connect(DB_NAME)

if all_skill_records:
    df_skills = pd.DataFrame(all_skill_records)
    print("Skills data preview:")
    print(df_skills.head(10))
    df_skills.to_sql("skills_log", conn, if_exists="append", index=False)

if all_activity_records:
    df_activities = pd.DataFrame(all_activity_records)
    print("\nActivities data preview:")
    print(df_activities.head(10))
    df_activities.to_sql("activities_log", conn, if_exists="append", index=False)

conn.close()
print(f"\nSuccessfully updated {DB_NAME}")
