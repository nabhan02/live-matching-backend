import sqlite3
import secrets
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / 'matrimonial.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Participants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            gender TEXT NOT NULL,
            email TEXT NOT NULL,
            unique_token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Selections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            selector_id INTEGER NOT NULL,
            selected_id INTEGER NOT NULL,
            rank INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(selector_id, selected_id),
            FOREIGN KEY (selector_id) REFERENCES participants(id),
            FOREIGN KEY (selected_id) REFERENCES participants(id)
        )
    ''')
    
    # Matches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant1_id INTEGER NOT NULL,
            participant2_id INTEGER NOT NULL,
            rank1 INTEGER DEFAULT 0,
            rank2 INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (participant1_id) REFERENCES participants(id),
            FOREIGN KEY (participant2_id) REFERENCES participants(id)
        )
    ''')
    
    # Admin credentials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def generate_unique_token():
    """Generate a unique token for participant links"""
    return secrets.token_urlsafe(16)

def add_participant(participant_id, first_name, gender, email):
    """Add a participant to the database"""
    conn = get_db()
    cursor = conn.cursor()
    
    token = generate_unique_token()
    
    try:
        cursor.execute(
            'INSERT INTO participants (id, first_name, gender, email, unique_token) VALUES (?, ?, ?, ?, ?)',
            (participant_id, first_name, gender, email, token)
        )
        conn.commit()
        conn.close()
        return token
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_all_participants():
    """Get all participants"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, first_name, gender, email, unique_token FROM participants ORDER BY id')
    participants = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return participants

def get_participant_by_token(token):
    """Get participant by their unique token"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, first_name, gender FROM participants WHERE unique_token = ?', (token,))
    participant = cursor.fetchone()
    conn.close()
    return dict(participant) if participant else None

def add_selection(selector_id, selected_id, rank=0):
    """Add a selection (who selected whom) with ranking"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO selections (selector_id, selected_id, rank) VALUES (?, ?, ?)',
            (selector_id, selected_id, rank)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_selections_by_participant(participant_id):
    """Get all selections made by a participant with ranks"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT selected_id, rank FROM selections WHERE selector_id = ? ORDER BY rank', (participant_id,))
    selections = [{'selected_id': row[0], 'rank': row[1]} for row in cursor.fetchall()]
    conn.close()
    return selections

def clear_selections(participant_id):
    """Clear all selections for a participant"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM selections WHERE selector_id = ?', (participant_id,))
    conn.commit()
    conn.close()

def clear_all_data():
    """Clear all participants, selections, and matches"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM matches')
    cursor.execute('DELETE FROM selections')
    cursor.execute('DELETE FROM participants')
    conn.commit()
    conn.close()

def get_all_matches():
    """Get all matches with participant names and ranks"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            m.id,
            m.participant1_id,
            p1.first_name as name1,
            m.participant2_id,
            p2.first_name as name2,
            m.rank1,
            m.rank2
        FROM matches m
        JOIN participants p1 ON m.participant1_id = p1.id
        JOIN participants p2 ON m.participant2_id = p2.id
        ORDER BY m.id
    ''')
    
    matches = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return matches

def clear_matches():
    """Clear all matches"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM matches')
    conn.commit()
    conn.close()

def add_match(participant1_id, participant2_id, rank1=0, rank2=0):
    """Add a match to the database with mutual ranks"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO matches (participant1_id, participant2_id, rank1, rank2) VALUES (?, ?, ?, ?)',
        (participant1_id, participant2_id, rank1, rank2)
    )
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
