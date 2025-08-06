import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

def get_app_data_dir() -> Path:
    """Get platform-appropriate user data directory."""
    if os.name == 'nt':  # Windows
        data_dir = Path(os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))) / 'Termitas'
    elif sys.platform == 'darwin':  # macOS
        data_dir = Path.home() / 'Library' / 'Application Support' / 'Termitas'
    else:  # Linux
        data_dir = Path.home() / '.local' / 'share' / 'Termitas'
    
    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_models_dir() -> Path:
    """Get directory where downloaded models are stored."""
    models_dir = get_app_data_dir() / 'downloaded_models'
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir

def get_db_path() -> Path:
    """Get path to the SQLite database."""
    return get_app_data_dir() / 'models.db'

class ModelsDatabase:
    def __init__(self):
        self.db_path = get_db_path()
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database tables."""
        with self.get_connection() as conn:
            # Models table - tracks downloaded models
            conn.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    local_path TEXT NOT NULL,
                    download_date TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    parameter_count INTEGER,
                    model_type TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'downloaded',
                    last_used TEXT,
                    downloads_count INTEGER DEFAULT 0,
                    likes_count INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Downloads table - tracks download progress and history
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percent REAL DEFAULT 0,
                    downloaded_bytes INTEGER DEFAULT 0,
                    total_bytes INTEGER DEFAULT 0,
                    download_speed REAL DEFAULT 0,
                    eta_seconds INTEGER,
                    error_message TEXT,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    paused_at TEXT,
                    FOREIGN KEY (model_id) REFERENCES models (model_id)
                )
            ''')
            
            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_models_model_id ON models (model_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_downloads_model_id ON downloads (model_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads (status)')
            
            conn.commit()
    
    def add_model(self, model_id: str, display_name: str, local_path: str, 
                  parameter_count: Optional[int] = None, model_type: str = "text-generation",
                  description: str = "", downloads_count: int = 0, likes_count: int = 0,
                  metadata: Dict = None) -> bool:
        """Add a new model to the database."""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO models 
                    (model_id, display_name, local_path, download_date, parameter_count, 
                     model_type, description, downloads_count, likes_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    model_id, display_name, local_path, datetime.now().isoformat(),
                    parameter_count, model_type, description, downloads_count, 
                    likes_count, json.dumps(metadata or {})
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding model to database: {e}")
            return False
    
    def get_model(self, model_id: str) -> Optional[Dict]:
        """Get model information by model_id."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM models WHERE model_id = ?', (model_id,)
                )
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Parse JSON metadata
                    if result.get('metadata'):
                        try:
                            result['metadata'] = json.loads(result['metadata'])
                        except:
                            result['metadata'] = {}
                    return result
                return None
        except Exception as e:
            print(f"Error getting model from database: {e}")
            return None
    
    def get_all_models(self) -> List[Dict]:
        """Get all downloaded models."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    'SELECT * FROM models ORDER BY download_date DESC'
                )
                models = []
                for row in cursor.fetchall():
                    result = dict(row)
                    # Parse JSON metadata
                    if result.get('metadata'):
                        try:
                            result['metadata'] = json.loads(result['metadata'])
                        except:
                            result['metadata'] = {}
                    models.append(result)
                return models
        except Exception as e:
            print(f"Error getting all models: {e}")
            return []
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model from database and filesystem."""
        try:
            # Get model info first
            model = self.get_model(model_id)
            if not model:
                return False
            
            # Delete from filesystem
            model_path = Path(model['local_path'])
            if model_path.exists():
                import shutil
                if model_path.is_dir():
                    shutil.rmtree(model_path)
                else:
                    model_path.unlink()
            
            # Delete from database
            with self.get_connection() as conn:
                conn.execute('DELETE FROM models WHERE model_id = ?', (model_id,))
                conn.execute('DELETE FROM downloads WHERE model_id = ?', (model_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error deleting model: {e}")
            return False
    
    def update_model_usage(self, model_id: str):
        """Update last_used timestamp for a model."""
        try:
            with self.get_connection() as conn:
                conn.execute(
                    'UPDATE models SET last_used = ? WHERE model_id = ?',
                    (datetime.now().isoformat(), model_id)
                )
                conn.commit()
        except Exception as e:
            print(f"Error updating model usage: {e}")
    
    def is_model_downloaded(self, model_id: str) -> bool:
        """Check if a model is already downloaded."""
        model = self.get_model(model_id)
        if not model:
            return False
        
        # Check if local path still exists
        local_path = Path(model['local_path'])
        return local_path.exists()
    
    # Download tracking methods
    def start_download(self, model_id: str) -> int:
        """Start tracking a new download. Returns download_id."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    INSERT INTO downloads (model_id, status, started_at)
                    VALUES (?, 'downloading', ?)
                ''', (model_id, datetime.now().isoformat()))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error starting download tracking: {e}")
            return -1
    
    def update_download_progress(self, download_id: int, progress_percent: float, 
                               downloaded_bytes: int, total_bytes: int, 
                               download_speed: float = 0, eta_seconds: Optional[int] = None):
        """Update download progress."""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE downloads SET 
                        progress_percent = ?, downloaded_bytes = ?, total_bytes = ?,
                        download_speed = ?, eta_seconds = ?
                    WHERE id = ?
                ''', (progress_percent, downloaded_bytes, total_bytes, 
                      download_speed, eta_seconds, download_id))
                conn.commit()
        except Exception as e:
            print(f"Error updating download progress: {e}")
    
    def pause_download(self, download_id: int):
        """Mark download as paused."""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE downloads SET status = 'paused', paused_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), download_id))
                conn.commit()
        except Exception as e:
            print(f"Error pausing download: {e}")
    
    def resume_download(self, download_id: int):
        """Mark download as resumed."""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE downloads SET status = 'downloading', paused_at = NULL
                    WHERE id = ?
                ''', (download_id,))
                conn.commit()
        except Exception as e:
            print(f"Error resuming download: {e}")
    
    def complete_download(self, download_id: int, success: bool = True, error_message: str = None):
        """Mark download as completed or failed."""
        try:
            status = 'completed' if success else 'failed'
            with self.get_connection() as conn:
                conn.execute('''
                    UPDATE downloads SET 
                        status = ?, completed_at = ?, error_message = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat(), error_message, download_id))
                conn.commit()
        except Exception as e:
            print(f"Error completing download: {e}")
    
    def get_active_download(self, model_id: str) -> Optional[Dict]:
        """Get active download for a model."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT * FROM downloads 
                    WHERE model_id = ? AND status IN ('downloading', 'paused')
                    ORDER BY started_at DESC LIMIT 1
                ''', (model_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting active download: {e}")
            return None
    
    def get_download_stats(self) -> Dict:
        """Get download statistics."""
        try:
            with self.get_connection() as conn:
                # Count models
                cursor = conn.execute('SELECT COUNT(*) FROM models')
                total_models = cursor.fetchone()[0]
                
                # Count active downloads  
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM downloads WHERE status IN ('downloading', 'paused')"
                )
                active_downloads = cursor.fetchone()[0]
                
                # Calculate total size
                cursor = conn.execute('SELECT SUM(size_bytes) FROM models')
                total_size_bytes = cursor.fetchone()[0] or 0
                
                return {
                    'total_models': total_models,
                    'active_downloads': active_downloads,
                    'total_size_bytes': total_size_bytes,
                    'total_size_gb': total_size_bytes / (1024**3) if total_size_bytes else 0
                }
        except Exception as e:
            print(f"Error getting download stats: {e}")
            return {'total_models': 0, 'active_downloads': 0, 'total_size_bytes': 0, 'total_size_gb': 0}

# Global database instance
_db_instance = None

def get_db() -> ModelsDatabase:
    """Get the global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = ModelsDatabase()
    return _db_instance