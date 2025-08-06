import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

def get_chat_db():
    """Get chat database connection."""
    db_path = Path("database/chat.db")
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    
    # Initialize tables
    _initialize_chat_db(conn)
    
    return conn

def _initialize_chat_db(conn: sqlite3.Connection):
    """Initialize chat database tables."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            model_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT DEFAULT '{}'
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()

def create_chat_session(name: str, model_id: str, metadata: Dict = None) -> int:
    """Create a new chat session."""
    conn = get_chat_db()
    
    cursor = conn.execute(
        "INSERT INTO chat_sessions (name, model_id, metadata) VALUES (?, ?, ?)",
        (name, model_id, json.dumps(metadata or {}))
    )
    
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return session_id

def get_chat_sessions() -> List[Dict]:
    """Get all chat sessions."""
    conn = get_chat_db()
    
    cursor = conn.execute("""
        SELECT cs.*, 
               COUNT(cm.id) as message_count,
               MAX(cm.timestamp) as last_message_time
        FROM chat_sessions cs
        LEFT JOIN chat_messages cm ON cs.id = cm.session_id
        GROUP BY cs.id
        ORDER BY cs.updated_at DESC
    """)
    
    sessions = []
    for row in cursor.fetchall():
        session = dict(row)
        session['metadata'] = json.loads(session['metadata'])
        sessions.append(session)
    
    conn.close()
    return sessions

def get_chat_session(session_id: int) -> Optional[Dict]:
    """Get a specific chat session."""
    conn = get_chat_db()
    
    cursor = conn.execute(
        "SELECT * FROM chat_sessions WHERE id = ?",
        (session_id,)
    )
    
    row = cursor.fetchone()
    if row:
        session = dict(row)
        session['metadata'] = json.loads(session['metadata'])
        conn.close()
        return session
    
    conn.close()
    return None

def delete_chat_session(session_id: int) -> bool:
    """Delete a chat session and all its messages."""
    conn = get_chat_db()
    
    cursor = conn.execute(
        "DELETE FROM chat_sessions WHERE id = ?",
        (session_id,)
    )
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted

def add_chat_message(session_id: int, sender: str, content: str, metadata: Dict = None) -> int:
    """Add a message to a chat session."""
    conn = get_chat_db()
    
    cursor = conn.execute(
        "INSERT INTO chat_messages (session_id, sender, content, metadata) VALUES (?, ?, ?, ?)",
        (session_id, sender, content, json.dumps(metadata or {}))
    )
    
    message_id = cursor.lastrowid
    
    # Update session timestamp
    conn.execute(
        "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (session_id,)
    )
    
    conn.commit()
    conn.close()
    
    return message_id

def get_chat_messages(session_id: int) -> List[Dict]:
    """Get all messages for a chat session."""
    conn = get_chat_db()
    
    cursor = conn.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    )
    
    messages = []
    for row in cursor.fetchall():
        message = dict(row)
        message['metadata'] = json.loads(message['metadata'])
        messages.append(message)
    
    conn.close()
    return messages

def clear_chat_messages(session_id: int) -> bool:
    """Clear all messages from a chat session."""
    conn = get_chat_db()
    
    cursor = conn.execute(
        "DELETE FROM chat_messages WHERE session_id = ?",
        (session_id,)
    )
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted 