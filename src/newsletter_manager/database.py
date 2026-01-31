"""Database management for newsletter tracking."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


class Database:
    """Manages SQLite database for newsletter tracking."""
    
    def __init__(self, db_path: Path):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self) -> None:
        """Connect to database and create tables if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self) -> None:
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Newsletters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_email TEXT NOT NULL UNIQUE,
                sender_name TEXT,
                category TEXT,
                subcategory TEXT,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                total_count INTEGER DEFAULT 1,
                unread_count INTEGER DEFAULT 0,
                read_count INTEGER DEFAULT 0,
                platform TEXT,
                frequency_estimate REAL,
                auto_categorized BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Messages table (for tracking individual messages)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                newsletter_id INTEGER NOT NULL,
                subject TEXT,
                received_date TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                is_archived BOOLEAN DEFAULT 0,
                has_unsubscribe_link BOOLEAN DEFAULT 0,
                labels TEXT,
                FOREIGN KEY (newsletter_id) REFERENCES newsletters (id)
            )
        """)
        
        # Scan history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date TEXT NOT NULL,
                days_scanned INTEGER,
                messages_processed INTEGER,
                newsletters_found INTEGER,
                duration_seconds REAL
            )
        """)
        
        # Operations log table (for undo support)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                operation_date TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                details TEXT,
                reversible BOOLEAN DEFAULT 0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_newsletters_sender ON newsletters(sender_email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_newsletters_category ON newsletters(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_newsletter ON messages(newsletter_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(received_date)")
        
        self.conn.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def upsert_newsletter(self, sender_email: str, sender_name: Optional[str] = None,
                         category: Optional[str] = None, subcategory: Optional[str] = None,
                         platform: Optional[str] = None, first_seen: Optional[str] = None,
                         last_seen: Optional[str] = None, auto_categorized: bool = False) -> int:
        """Insert or update newsletter record."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # Check if exists
        cursor.execute("SELECT id, total_count FROM newsletters WHERE sender_email = ?", (sender_email,))
        row = cursor.fetchone()
        
        if row:
            # Update existing
            newsletter_id = row['id']
            total_count = row['total_count'] + 1
            
            update_fields = ["total_count = ?", "updated_at = ?"]
            params = [total_count, now]
            
            if last_seen:
                update_fields.append("last_seen = ?")
                params.append(last_seen)
            if sender_name:
                update_fields.append("sender_name = ?")
                params.append(sender_name)
            if category:
                update_fields.append("category = ?")
                params.append(category)
            if subcategory:
                update_fields.append("subcategory = ?")
                params.append(subcategory)
            if platform:
                update_fields.append("platform = ?")
                params.append(platform)
            if auto_categorized:
                update_fields.append("auto_categorized = ?")
                params.append(1)
            
            params.append(sender_email)
            
            cursor.execute(f"""
                UPDATE newsletters 
                SET {', '.join(update_fields)}
                WHERE sender_email = ?
            """, params)
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO newsletters 
                (sender_email, sender_name, category, subcategory, platform, 
                 first_seen, last_seen, auto_categorized, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sender_email, sender_name, category, subcategory, platform,
                  first_seen or now, last_seen or now, auto_categorized, now, now))
            newsletter_id = cursor.lastrowid
        
        self.conn.commit()
        return newsletter_id
    
    def get_newsletter_by_email(self, sender_email: str) -> Optional[Dict]:
        """Get newsletter by sender email."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM newsletters WHERE sender_email = ?", (sender_email,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_newsletters(self, category: Optional[str] = None) -> List[Dict]:
        """Get all newsletters, optionally filtered by category."""
        cursor = self.conn.cursor()
        if category:
            cursor.execute("SELECT * FROM newsletters WHERE category = ? ORDER BY last_seen DESC", (category,))
        else:
            cursor.execute("SELECT * FROM newsletters ORDER BY last_seen DESC")
        return [dict(row) for row in cursor.fetchall()]
    
    def add_message(self, message_id: str, newsletter_id: int, subject: str,
                   received_date: str, is_read: bool = False, labels: Optional[List[str]] = None) -> None:
        """Add or update message record."""
        cursor = self.conn.cursor()
        labels_json = json.dumps(labels) if labels else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO messages 
            (id, newsletter_id, subject, received_date, is_read, labels)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, newsletter_id, subject, received_date, is_read, labels_json))
        
        self.conn.commit()
    
    def get_messages_by_newsletter(self, newsletter_id: int) -> List[Dict]:
        """Get all messages for a specific newsletter."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE newsletter_id = ?", (newsletter_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def record_scan(self, days_scanned: int, messages_processed: int, 
                   newsletters_found: int, duration_seconds: float) -> None:
        """Record scan history."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scan_history (scan_date, days_scanned, messages_processed, 
                                     newsletters_found, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), days_scanned, messages_processed, 
              newsletters_found, duration_seconds))
        self.conn.commit()
    
    def get_last_scan(self) -> Optional[Dict]:
        """Get last scan information."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM scan_history ORDER BY scan_date DESC LIMIT 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def log_operation(self, operation_type: str, target_type: Optional[str] = None,
                     target_id: Optional[str] = None, details: Optional[Dict] = None,
                     reversible: bool = False) -> None:
        """Log an operation for potential undo."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO operations_log (operation_type, operation_date, target_type, 
                                       target_id, details, reversible)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (operation_type, datetime.now().isoformat(), target_type, 
              target_id, json.dumps(details) if details else None, reversible))
        self.conn.commit()
