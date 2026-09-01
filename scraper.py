import requests
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
    """Fetch player data using the JSON API (includes bosses)"""
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.json?player={username}"
    headers = {'User-Agent': 'GIM-Tracker-Script'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch data for {username}")
            return None, None
        
        data = response.json()
        
        # Extract Skills
        skills_data = data.get("skills", {})
        player_data = []
        
        for skill in SKILLS:
            if skill in skills_data:
                skill_info = skills_data[skill]
                player_data.append({
                    "timestamp": datetime.now().isoformat(),
                    "player": username,
                    "skill": skill,
                    "rank": skill_info.get("rank", -1),
                    "level": skill_info.get("level", 0),
                    "xp": skill_info.get("experience", 0)
                })
        
        # Extract Bosses
        bosses_data = data.get("bosses", {})
        boss_data = []
        
        for boss_name, boss_info in bosses_data.items():
            boss_data.append({
                "timestamp": datetime.now().isoformat(),
                "player": username,
                "boss": boss_name,
                "rank": boss_info.get("rank", -1),
                "kills": boss_info.get("score", 0)
            })
        
        return player_data, boss_data
    
    except Exception as e:
        print(f"Error fetching data for {username}: {e}")
        return None, None

# Collect all data
all_skill_records = []
all_boss_records = []

for member in group_members:
    skills, bosses = fetch_player_data(member)
    if skills:
        all_skill_records.extend(skills)
    if bosses:
        all_boss_records.extend(bosses)

# Save Skills CSV
if all_skill_records:
    df_skills = pd.DataFrame(all_skill_records)
    print("Skills data:")
    print(df_skills.head(10))
    df_skills.to_csv("gim_xp_log.csv", mode='a', header=not pd.io.common.file_exists("gim_xp_log.csv"), index=False)

# Save Bosses CSV
if all_boss_records:
    df_bosses = pd.DataFrame(all_boss_records)
    print("\nBosses data:")
    print(df_bosses.head(10))
    df_bosses.to_csv("boss_kills_log.csv", mode='a', header=not pd.io.common.file_exists("boss_kills_log.csv"), index=False)
