import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import List, Dict, Optional
from models import User, Project, Vote

DATABASE_FILE = "votes.db"


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Foydalanuvchilar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            username TEXT,
            phone TEXT,
            balance INTEGER DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Loyihalar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Ovozlar jadvali
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            photo_id TEXT NOT NULL,
            phone TEXT NOT NULL,
            card_number TEXT,
            is_confirmed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        """)

        conn.commit()


# ===================== FOYDALANUVCHILAR =====================

def add_user(user_id: int, full_name: str, username: str = None) -> User:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (id, full_name, username) VALUES (?, ?, ?)",
            (user_id, full_name, username)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return User(**cursor.fetchone())


def update_user_phone(user_id: int, phone: str) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET phone = ? WHERE id = ?",
            (phone, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_user(user_id: int) -> Optional[User]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return User(**result) if result else None


# ===================== LOYIHALAR =====================

def add_project(title: str, link: str, is_active: bool = False) -> Project:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if is_active:
            # Faqat bitta loyiha aktiv bo'lishi uchun
            cursor.execute("UPDATE projects SET is_active = 0")
        cursor.execute(
            "INSERT INTO projects (title, link, is_active) VALUES (?, ?, ?)",
            (title, link, is_active)
        )
        project_id = cursor.lastrowid
        conn.commit()
        return get_project(project_id)


def get_project(project_id: int) -> Optional[Project]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        result = cursor.fetchone()
        return Project(**result) if result else None


def get_active_project() -> Optional[Project]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE is_active = 1 LIMIT 1")
        result = cursor.fetchone()
        return Project(**result) if result else None


def get_all_projects() -> List[Project]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
        return [Project(**row) for row in cursor.fetchall()]


def set_active_project(project_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Barcha loyihalarni noaktiv qilamiz
        cursor.execute("UPDATE projects SET is_active = 0")
        # Tanlangan loyihani aktiv qilamiz
        cursor.execute(
            "UPDATE projects SET is_active = 1 WHERE id = ?",
            (project_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


# ===================== OVOZLAR =====================

def add_vote(user_id: int, project_id: int, photo_id: str, phone: str) -> Vote:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO votes (user_id, project_id, photo_id, phone)
               VALUES (?, ?, ?, ?)""",
            (user_id, project_id, photo_id, phone)
        )
        vote_id = cursor.lastrowid
        conn.commit()
        return get_vote(vote_id)


def get_vote(vote_id: int) -> Optional[Vote]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM votes WHERE id = ?", (vote_id,))
        result = cursor.fetchone()
        return Vote(**result) if result else None


def get_user_votes(user_id: int) -> List[Vote]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM votes WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return [Vote(**row) for row in cursor.fetchall()]


def get_pending_votes() -> List[Vote]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.* FROM votes v
            WHERE v.is_confirmed = 0
            ORDER BY v.created_at DESC
        """)
        return [Vote(**row) for row in cursor.fetchall()]


def confirm_vote(vote_id: int, card_number: str = None) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Ovozni tasdiqlaymiz
        cursor.execute(
            """UPDATE votes SET is_confirmed = 1, card_number = ?
               WHERE id = ? AND is_confirmed = 0""",
            (card_number, vote_id)
        )
        if cursor.rowcount > 0:
            # Balansga mukofot qo'shamiz
            cursor.execute(
                """UPDATE users SET balance = balance + ?
                   WHERE id = (SELECT user_id FROM votes WHERE id = ?)""",
                (VOTE_REWARD, vote_id)
            )
        conn.commit()
        return cursor.rowcount > 0


def reject_vote(vote_id: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM votes WHERE id = ? AND is_confirmed = 0",
            (vote_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


# ===================== STATISTIKA =====================

def get_user_balance(user_id: int) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        return result["balance"] if result else 0


def get_vote_stats() -> Dict[str, int]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM votes")
        total_votes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM votes WHERE is_confirmed = 1")
        confirmed_votes = cursor.fetchone()[0]
        return {
            "total_votes": total_votes,
            "confirmed_votes": confirmed_votes,
            "pending_votes": total_votes - confirmed_votes
        }