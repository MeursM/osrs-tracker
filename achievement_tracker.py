import os
import sqlite3
import requests
from datetime import datetime

# Database setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "gim_achievements.db")

PLAYERS = {
    "Mas120": "STANDARD",
    "MrBSvenB": "STANDARD",
    "Phome1": "STANDARD",
    "Darallax": "STANDARD"
}

def init_db():
    """Initialize SQLite database schema."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Track logged changes (Unique constraint on player + entry_name)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS achievements_log (
            player TEXT,
            entry_name TEXT,
            detected_timestamp TEXT,
            old_value INTEGER,
            new_value INTEGER,
            PRIMARY KEY (player, entry_name)
        )
    ''')
    
    # Internal cache state table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_current_state (
            player TEXT,
            entry_name TEXT,
            status_value INTEGER,
            PRIMARY KEY (player, entry_name)
        )
    ''')
    
    conn.commit()
    conn.close()

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
                flat_state[f"Quest: {name}"] = int(status) if isinstance(status, (int, bool)) else 0

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

def get_previous_state_from_db(conn, username):
    """Get previously saved state from internal cache table."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT entry_name, status_value FROM player_current_state WHERE player = ?", 
        (username,)
    )
    rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows} if rows else None

def update_player_state_in_db(conn, username, current_state):
    """Upsert full state into the internal cache table."""
    cursor = conn.cursor()
    data_to_upsert = [(username, name, val) for name, val in current_state.items()]
    
    cursor.executemany('''
        INSERT INTO player_current_state (player, entry_name, status_value)
        VALUES (?, ?, ?)
        ON CONFLICT(player, entry_name) DO UPDATE SET
            status_value = excluded.status_value
    ''', data_to_upsert)
    conn.commit()

def upsert_achievement_logs(conn, timestamp, username, changes):
    """Insert or update achievement rows only when actual progress occurs."""
    cursor = conn.cursor()
    
    records = [
        (username, entry_name, timestamp, old_val, new_val)
        for entry_name, old_val, new_val in changes
    ]
    
    # If the player + entry_name exists, update timestamp, old_val, and new_val
    cursor.executemany('''
        INSERT INTO achievements_log (player, entry_name, detected_timestamp, old_value, new_value)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(player, entry_name) DO UPDATE SET
            detected_timestamp = excluded.detected_timestamp,
            old_value = excluded.old_value,
            new_value = excluded.new_value
    ''', records)
    
    conn.commit()

def process_player_achievements(username, profile):
    """Process achievements for a single player."""
    data = fetch_player_data(username, profile)
    if not data:
        print(f"No response from API for {username}. Skipping.")
        return

    current_state = extract_all_progress(data)
    
    conn = sqlite3.connect(DB_NAME)
    prev_state = get_previous_state_from_db(conn, username)
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if prev_state is None:
        print(f"First run for {username}! Setting baseline...")
        # Only log items that already have completed progress (> 0) on the very first run
        initial_changes = [
            (name, 0, status) 
            for name, status in current_state.items() 
            if status > 0
        ]
        if initial_changes:
            upsert_achievement_logs(conn, today_date, username, initial_changes)
    else:
        # Subsequent runs: calculate actual changes
        changes = []
        for name, new_val in current_state.items():
            old_val = prev_state.get(name, 0)
            
            # Log ONLY when value changes (e.g. 0 -> 2, or 1 -> 2)
            if old_val != new_val:
                changes.append((name, old_val, new_val))
                print(f"Update for {username}: {name} ({old_val} -> {new_val})")
        
        if changes:
            upsert_achievement_logs(conn, today_date, username, changes)
        else:
            print(f"No new progress for {username}.")

    # Update cache
    update_player_state_in_db(conn, username, current_state)
    conn.close()

if __name__ == "__main__":
    init_db()
    for username, profile in PLAYERS.items():
        process_player_achievements(username, profile)
    print(f"Tracking complete! Updated {DB_NAME}")
