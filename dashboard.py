import os
import sqlite3
import pandas as pd
import streamlit as st

# ==========================================
# 1. DATABASE PATH RESOLUTION
# ==========================================
# Use absolute paths so SQLite connects to the correct file
# regardless of where Streamlit is executed from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "gim_tracker.db")


# ==========================================
# 2. CONNECTION & SCHEMA INITIALIZATION
# ==========================================
def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)


def init_db():
    """Ensures all required tables exist before running queries."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create achievements_log if missing
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS achievements_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT,
            entry_name TEXT,
            old_value TEXT,
            new_value TEXT,
            detected_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create xp_log if missing
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS xp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT,
            skill TEXT,
            xp_gained INTEGER,
            detected_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create activities_log if missing
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS activities_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player TEXT,
            activity TEXT,
            score INTEGER,
            detected_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()


# Initialize database tables on app start
init_db()


# ==========================================
# 3. DATA LOADERS
# ==========================================
@st.cache_data(ttl=0)
def load_achievements_data():
    """Loads and standardizes achievement log data."""
    if not os.path.exists(DB_FILE):
        return None

    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM achievements_log", conn)
    except Exception as e:
        st.error(f"SQL Error loading achievements_log: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        return None

    # Step 1: Normalize column names (strip whitespace and lowercase)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Step 2: Safely parse timestamp using lowercase names first
    timestamp_col = None
    if "detected_timestamp" in df.columns:
        timestamp_col = "detected_timestamp"
    elif "timestamp" in df.columns:
        timestamp_col = "timestamp"

    if timestamp_col:
        df["timestamp"] = pd.to_datetime(df[timestamp_col], errors="coerce")
        df = df.dropna(subset=["timestamp"])

    if df.empty:
        return None

    # Step 3: Standardize output column naming
    column_mapping = {
        "player": "Player",
        "entry_name": "Entry_Name",
        "old_value": "Old_Value",
        "new_value": "New_Value",
        "detected_timestamp": "Detected_Timestamp",
    }
    df.rename(columns=column_mapping, inplace=True)

    # Clean string fields
    if "Player" in df.columns:
        df["Player"] = df["Player"].astype(str).str.strip()

    df["date"] = df["timestamp"].dt.date
    return df


@st.cache_data(ttl=0)
def load_xp_data():
    """Loads and standardizes XP log data."""
    if not os.path.exists(DB_FILE):
        return None

    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM xp_log", conn)
    except Exception as e:
        st.error(f"SQL Error loading xp_log: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        return None

    df.columns = [str(c).strip().lower() for c in df.columns]

    if "detected_timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["detected_timestamp"], errors="coerce"
        )
        df = df.dropna(subset=["timestamp"])

    if df.empty:
        return None

    df.rename(
        columns={
            "player": "Player",
            "skill": "Skill",
            "xp_gained": "XP_Gained",
        },
        inplace=True,
    )
    df["date"] = df["timestamp"].dt.date
    return df


@st.cache_data(ttl=0)
def load_activities_data():
    """Loads and standardizes activity log data."""
    if not os.path.exists(DB_FILE):
        return None

    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM activities_log", conn)
    except Exception as e:
        st.error(f"SQL Error loading activities_log: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        return None

    df.columns = [str(c).strip().lower() for c in df.columns]

    if "detected_timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["detected_timestamp"], errors="coerce"
        )
        df = df.dropna(subset=["timestamp"])

    if df.empty:
        return None

    df.rename(
        columns={"player": "Player", "activity": "Activity", "score": "Score"},
        inplace=True,
    )
    df["date"] = df["timestamp"].dt.date
    return df


# ==========================================
# 4. STREAMLIT INTERFACE
# ==========================================
st.set_page_config(page_title="GIM Tracker", layout="wide")
st.title("Group Ironman Tracker Dashboard")

# Refresh Button
if st.sidebar.button("Update Data"):
    st.cache_data.clear()
    st.rerun()

# Load Data
achievements_df = load_achievements_data()
xp_df = load_xp_data()
activities_df = load_activities_data()

# Navigation Tabs
tab1, tab2, tab3 = st.tabs(["Achievements", "XP Gains", "Activities"])

with tab1:
    st.header("Achievements Log")
    if achievements_df is not None and not achievements_df.empty:
        st.dataframe(achievements_df, use_container_width=True)
    else:
        st.info("No achievement records found in the database.")

with tab2:
    st.header("XP Gains Log")
    if xp_df is not None and not xp_df.empty:
        st.dataframe(xp_df, use_container_width=True)
    else:
        st.info("No XP records found in the database.")

with tab3:
    st.header("Activities Log")
    if activities_df is not None and not activities_df.empty:
        st.dataframe(activities_df, use_container_width=True)
    else:
        st.info("No activity records found in the database.")
