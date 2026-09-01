import os
import json
import csv
import requests
from datetime import datetime

# Save files directly in the same directory as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration for each player
PLAYERS = {
    "Mas120": "STANDARD",
    "MrBSvenB": "STANDARD",
    "Phome1": "STANDARD",
    "Darallax": "STANDARD"
}

def fetch_player_data(username, profile):
    """Fetch current raw JSON state from WikiSync API."""
    api_url = f"https://sync.runescape.wiki/runelite/player/{username}/{profile}"
    headers = {"User-Agent": "OSRS-WikiSync-Logger/1.0"}
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Failed to fetch WikiSync data for {username}: {e}")
        return None

def extract_all_progress(data):
    """Extract ALL player categories into a single flat dictionary."""
    flat_state = {}

    # 1. Quests
    quests = data.get("quests", {})
    if isinstance(quests, dict):
        for name, status in quests.items():
            if name != ".":
                flat_state[f"Quest: {name}"] = status

    # 2. Achievement Diaries
    diaries = data.get("achievement_diaries", {})
    if isinstance(diaries, dict):
        for area, tiers in diaries.items():
            if isinstance(tiers, dict):
                for tier, info in tiers.items():
                    if isinstance(info, dict) and "complete" in info:
                        flat_state[f"Diary: {area} ({tier})"] = 1 if info["complete"] else 0

    # 3. Combat Achievements
    ca = data.get("combat_achievements", {})
    if isinstance(ca, dict):
        for task_key, task_val in ca.items():
            if isinstance(task_val, dict):
                is_complete = task_val.get("complete", task_val.get("completed", False))
                flat_state[f"Combat Achievement: {task_key}"] = 1 if is_complete else 0
            else:
                flat_state[f"Combat Achievement: {task_key}"] = 1 if bool(task_val) else 0
    elif isinstance(ca, list):
        for item in ca:
            task_name = item.get("name", str(item)) if isinstance(item, dict) else str(item)
            flat_state[f"Combat Achievement: {task_name}"] = 1

    # 4. Music Tracks
    music = data.get("music_tracks", {})
    if isinstance(music, dict):
        for track, unlocked in music.items():
            flat_state[f"Music Track: {track}"] = 1 if bool(unlocked) else 0

    return flat_state

def load_previous_state(username):
    """Load cached state from disk if it exists."""
    state_file = os.path.join(BASE_DIR, f"previous_state_{username}.json")
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_current_state(username, state):
    """Save full progress state dictionary to previous_state_{username}.json."""
    state_file = os.path.join(BASE_DIR, f"previous_state_{username}.json")
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def append_completion_to_csv(timestamp, username, name, old_val, new_val):
    """Append row entry to achievements_log.csv"""
    csv_file = os.path.join(BASE_DIR, "achievements_log.csv")
    file_exists = os.path.exists(csv_file)

    with open(csv_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Detected_Timestamp", "Player", "Entry_Name", "Old_Value", "New_Value"])
        
        writer.writerow([timestamp, username, name, old_val, new_val])

def process_player_achievements(username, profile):
    """Process achievements for a single player."""
    data = fetch_player_data(username, profile)
    if not data:
        print(f"No response from API for {username}. Skipping.")
        return

    current_state = extract_all_progress(data)
    prev_state = load_previous_state(username)
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # FIRST RUN: Log everything
    if prev_state is None:
        print(f"First run for {username}! Extracted {len(current_state)} total items.")
        for name, status in current_state.items():
            append_completion_to_csv(today_date, username, name, 0, status)
    else:
        # SUBSEQUENT RUNS: Only log changes
        changes_count = 0
        for name, new_val in current_state.items():
            old_val = prev_state.get(name, 0)
            if old_val != new_val:
                append_completion_to_csv(today_date, username, name, old_val, new_val)
                print(f"Change detected for {username}: {name} ({old_val} -> {new_val})")
                changes_count += 1
        
        if changes_count == 0:
            print(f"No changes for {username} today.")

    save_current_state(username, current_state)

if __name__ == "__main__":
    for username, profile in PLAYERS.items():
        process_player_achievements(username, profile)
    print("Achievement tracking complete!")
