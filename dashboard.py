@st.cache_data(ttl=0)
def load_achievements_data():
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

    # Normalize column names: trim spaces and lowercase
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map database column names safely
    column_mapping = {
        'player': 'Player',
        'entry_name': 'Entry_Name',
        'old_value': 'Old_Value',
        'new_value': 'New_Value',
        'detected_timestamp': 'Detected_Timestamp',
    }
    df.rename(columns=column_mapping, inplace=True)

    # Clean player values
    if 'Player' in df.columns:
        df['Player'] = df['Player'].astype(str).str.strip()

    # Parse timestamps safely
    if 'Detected_Timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(
            df['Detected_Timestamp'], errors='coerce'
        )
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Drop rows where timestamp parsing completely failed to avoid downstream crashes
    df = df.dropna(subset=['timestamp'])

    if df.empty:
        return None

    df['date'] = df['timestamp'].dt.date
    return df
