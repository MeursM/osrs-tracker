import requests
import pandas as pd
from datetime import datetime

# Group member list extracted from your highscores page
group_members = ["Mas120", "MrBSvenB", "Phome1", "Darallax","vagijn"]

# OSRS Skill List in order returned by official API
SKILLS = [
    "Overall", "Attack", "Defence", "Strength", "Hitpoints", "Ranged", "Prayer",
    "Magic", "Cooking", "Woodcutting", "Fletching", "Fishing", "Firemaking",
    "Crafting", "Smithing", "Mining", "Herblore", "Agility", "Thieving",
    "Slayer", "Farming", "Runecraft", "Hunter", "Construction", "Sailing"
]

def fetch_player_data(username):
    # Official OSRS Hiscore API endpoint (Normal/GIM use standard IM/main API)
    url = f"https://services.runescape.com/m=hiscore_oldschool/index_lite.ws?player={username}"
    headers = {'User-Agent': 'GIM-Tracker-Script'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data for {username}")
        return None
    
    # Parse lines (Rank, Level, XP)
    lines = response.text.strip().split("\n")
    player_data = []
    
    for i, skill in enumerate(SKILLS):
        if i < len(lines):
            parts = lines[i].split(",")
            player_data.append({
                "timestamp": datetime.now().isoformat(),
                "player": username,
                "skill": skill,
                "rank": int(parts[0]),
                "level": int(parts[1]),
                "xp": int(parts[2])
            })
            
    return player_data

# Collect all data
all_records = []
for member in group_members:
    data = fetch_player_data(member)
    if data:
        all_records.extend(data)

# Convert to Pandas DataFrame for easy storage or dashboard feeding
df = pd.DataFrame(all_records)
print(df.head(10))

# Save to CSV (append mode for historical tracking over time)
df.to_csv("gim_xp_log.csv", mode='a', header=not pd.io.common.file_exists("gim_xp_log.csv"), index=False)
