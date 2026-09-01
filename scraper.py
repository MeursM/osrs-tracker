import requests
import os
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
        
        # Parse skills array from JSON
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
        
        # Extract Activities (Bosses, Clues, Minigames, etc.)
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

# Collect all data
all_skill_records = []
all_activity_records = []

for member in group_members:
    skills, activities = fetch_player_data(member)
    if skills:
        all_skill_records.extend(skills)
    if activities:
        all_activity_records.extend(activities)

# Save Skills CSV
if all_skill_records:
    df_skills = pd.DataFrame(all_skill_records)
    print("Skills data:")
    print(df_skills.head(10))
    df_skills.to_csv("gim_xp_log.csv", mode='a', header=not os.path.exists("gim_xp_log.csv"), index=False)

# Save Activities CSV
if all_activity_records:
    df_activities = pd.DataFrame(all_activity_records)
    print("\nActivities data:")
    print(df_activities.head(10))
    df_activities.to_csv("gim_activities_log.csv", mode='a', header=not os.path.exists("gim_activities_log.csv"), index=False)
