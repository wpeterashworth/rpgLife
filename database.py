import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rpglife.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER PRIMARY KEY,
            total_xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            available_points INTEGER NOT NULL DEFAULT 0,
            current_streak INTEGER NOT NULL DEFAULT 0,
            longest_streak INTEGER NOT NULL DEFAULT 0,
            last_completion_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '📋',
            color TEXT NOT NULL DEFAULT '#4A90D9',
            is_default INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            difficulty INTEGER NOT NULL DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 5),
            is_recurring INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS task_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            points_earned INTEGER NOT NULL,
            completed_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            value INTEGER NOT NULL DEFAULT 1 CHECK(value BETWEEN 1 AND 5),
            point_cost INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS reward_redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            points_spent INTEGER NOT NULL,
            redeemed_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (reward_id) REFERENCES rewards(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '🏆',
            requirement_type TEXT NOT NULL,
            requirement_value INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL,
            unlocked_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (achievement_id) REFERENCES achievements(id),
            UNIQUE(user_id, achievement_id)
        );

        CREATE TABLE IF NOT EXISTS point_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            reference_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    _seed_defaults(c)
    conn.commit()
    conn.close()


def _seed_defaults(cursor):
    # Seed default categories
    cursor.execute("SELECT COUNT(*) FROM categories WHERE is_default = 1")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("Health & Fitness", "💪", "#E74C3C"),
            ("Learning", "📚", "#3498DB"),
            ("Work", "💼", "#2ECC71"),
            ("Chores", "🏠", "#F39C12"),
            ("Creative", "🎨", "#9B59B6"),
            ("Social", "👥", "#1ABC9C"),
        ]
        for name, icon, color in defaults:
            cursor.execute(
                "INSERT INTO categories (user_id, name, icon, color, is_default) VALUES (NULL, ?, ?, ?, 1)",
                (name, icon, color),
            )

    # Seed achievements
    cursor.execute("SELECT COUNT(*) FROM achievements")
    if cursor.fetchone()[0] == 0:
        achievements = [
            # Consistency
            ("Week Warrior", "Maintain a 7-day streak", "consistency", "🔥", "streak", 7),
            ("Monthly Master", "Maintain a 30-day streak", "consistency", "🔥", "streak", 30),
            ("Centurion", "Maintain a 100-day streak", "consistency", "🔥", "streak", 100),
            # Intensity
            ("Getting Started", "Complete 10 tasks", "intensity", "⚡", "tasks_completed", 10),
            ("Productive", "Complete 50 tasks", "intensity", "⚡", "tasks_completed", 50),
            ("Task Machine", "Complete 100 tasks", "intensity", "⚡", "tasks_completed", 100),
            ("Unstoppable", "Complete 500 tasks", "intensity", "⚡", "tasks_completed", 500),
            # Specialization
            ("Specialist", "Complete 25 tasks in one category", "specialization", "🎯", "category_tasks", 25),
            # Leveling
            ("Apprentice", "Reach level 5", "leveling", "⭐", "level", 5),
            ("Journeyman", "Reach level 10", "leveling", "⭐", "level", 10),
            ("Expert", "Reach level 25", "leveling", "⭐", "level", 25),
            ("Grand Master", "Reach level 50", "leveling", "⭐", "level", 50),
            # Economy
            ("First Purchase", "Redeem your first reward", "economy", "🛒", "rewards_redeemed", 1),
            ("Saver", "Have 1000+ points saved", "economy", "💰", "points_saved", 1000),
        ]
        for name, desc, cat, icon, req_type, req_val in achievements:
            cursor.execute(
                "INSERT INTO achievements (name, description, category, icon, requirement_type, requirement_value) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (name, desc, cat, icon, req_type, req_val),
            )


# --- User functions ---

def create_user(username, password_hash, salt):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
            (username, password_hash, salt),
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO user_stats (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


def get_user_stats(user_id):
    conn = get_connection()
    stats = conn.execute("SELECT * FROM user_stats WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return stats


def update_user_stats(user_id, **kwargs):
    conn = get_connection()
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id]
    conn.execute(f"UPDATE user_stats SET {sets} WHERE user_id = ?", vals)
    conn.commit()
    conn.close()


# --- Category functions ---

def get_categories(user_id):
    conn = get_connection()
    cats = conn.execute(
        "SELECT * FROM categories WHERE is_default = 1 OR user_id = ? ORDER BY is_default DESC, name",
        (user_id,),
    ).fetchall()
    conn.close()
    return cats


def create_category(user_id, name, icon, color):
    conn = get_connection()
    conn.execute(
        "INSERT INTO categories (user_id, name, icon, color) VALUES (?, ?, ?, ?)",
        (user_id, name, icon, color),
    )
    conn.commit()
    conn.close()


def update_category(cat_id, name, icon, color):
    conn = get_connection()
    conn.execute(
        "UPDATE categories SET name = ?, icon = ?, color = ? WHERE id = ?",
        (name, icon, color, cat_id),
    )
    conn.commit()
    conn.close()


def delete_category(cat_id):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ? AND is_default = 0", (cat_id,))
    conn.commit()
    conn.close()


# --- Task functions ---

def create_task(user_id, category_id, name, description, difficulty, is_recurring=False):
    conn = get_connection()
    conn.execute(
        "INSERT INTO tasks (user_id, category_id, name, description, difficulty, is_recurring) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, category_id, name, description, difficulty, int(is_recurring)),
    )
    conn.commit()
    conn.close()


def get_active_tasks(user_id):
    conn = get_connection()
    tasks = conn.execute(
        "SELECT t.*, c.name as category_name, c.icon as category_icon, c.color as category_color "
        "FROM tasks t JOIN categories c ON t.category_id = c.id "
        "WHERE t.user_id = ? AND t.is_active = 1 ORDER BY t.created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return tasks


def complete_task(task_id, user_id, points_earned):
    conn = get_connection()
    conn.execute(
        "INSERT INTO task_completions (task_id, user_id, points_earned) VALUES (?, ?, ?)",
        (task_id, user_id, points_earned),
    )
    # Deactivate non-recurring tasks
    conn.execute(
        "UPDATE tasks SET is_active = 0 WHERE id = ? AND is_recurring = 0",
        (task_id,),
    )
    conn.execute(
        "INSERT INTO point_transactions (user_id, amount, transaction_type, reference_id) "
        "VALUES (?, ?, 'earned', ?)",
        (user_id, points_earned, task_id),
    )
    conn.commit()
    conn.close()


def get_task_completions(user_id, limit=50):
    conn = get_connection()
    completions = conn.execute(
        "SELECT tc.*, t.name as task_name, t.difficulty, c.icon as category_icon "
        "FROM task_completions tc "
        "JOIN tasks t ON tc.task_id = t.id "
        "JOIN categories c ON t.category_id = c.id "
        "WHERE tc.user_id = ? ORDER BY tc.completed_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return completions


def get_total_completions(user_id):
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM task_completions WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def get_category_completion_counts(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT c.name, c.icon, c.color, COUNT(tc.id) as count "
        "FROM task_completions tc "
        "JOIN tasks t ON tc.task_id = t.id "
        "JOIN categories c ON t.category_id = c.id "
        "WHERE tc.user_id = ? GROUP BY c.id ORDER BY count DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_max_category_completions(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(cnt) FROM ("
        "  SELECT COUNT(tc.id) as cnt FROM task_completions tc "
        "  JOIN tasks t ON tc.task_id = t.id "
        "  WHERE tc.user_id = ? GROUP BY t.category_id"
        ")",
        (user_id,),
    ).fetchone()
    conn.close()
    return row[0] if row[0] else 0


def get_weekly_completions(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT DATE(completed_at) as day, COUNT(*) as count "
        "FROM task_completions WHERE user_id = ? "
        "AND completed_at >= datetime('now', '-7 days') "
        "GROUP BY DATE(completed_at) ORDER BY day",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_xp_over_time(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT DATE(created_at) as day, SUM(amount) as total "
        "FROM point_transactions WHERE user_id = ? AND transaction_type = 'spent_xp' "
        "GROUP BY DATE(created_at) ORDER BY day",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def delete_task(task_id, user_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET is_active = 0 WHERE id = ? AND user_id = ?", (task_id, user_id))
    conn.commit()
    conn.close()


# --- Reward functions ---

def create_reward(user_id, name, description, value, point_cost):
    conn = get_connection()
    conn.execute(
        "INSERT INTO rewards (user_id, name, description, value, point_cost) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, description, value, point_cost),
    )
    conn.commit()
    conn.close()


def get_rewards(user_id):
    conn = get_connection()
    rewards = conn.execute(
        "SELECT * FROM rewards WHERE user_id = ? ORDER BY point_cost ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rewards


def redeem_reward(reward_id, user_id, points_spent):
    conn = get_connection()
    conn.execute(
        "INSERT INTO reward_redemptions (reward_id, user_id, points_spent) VALUES (?, ?, ?)",
        (reward_id, user_id, points_spent),
    )
    conn.execute(
        "INSERT INTO point_transactions (user_id, amount, transaction_type, reference_id) "
        "VALUES (?, ?, 'spent_reward', ?)",
        (user_id, -points_spent, reward_id),
    )
    conn.commit()
    conn.close()


def get_redemption_count(user_id):
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM reward_redemptions WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def get_redemption_history(user_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT rr.*, r.name as reward_name, r.value "
        "FROM reward_redemptions rr JOIN rewards r ON rr.reward_id = r.id "
        "WHERE rr.user_id = ? ORDER BY rr.redeemed_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return rows


def delete_reward(reward_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM rewards WHERE id = ? AND user_id = ?", (reward_id, user_id))
    conn.commit()
    conn.close()


# --- Achievement functions ---

def get_all_achievements():
    conn = get_connection()
    achievements = conn.execute("SELECT * FROM achievements ORDER BY category, requirement_value").fetchall()
    conn.close()
    return achievements


def get_user_achievements(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT achievement_id, unlocked_at FROM user_achievements WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return {row["achievement_id"]: row["unlocked_at"] for row in rows}


def unlock_achievement(user_id, achievement_id):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)",
            (user_id, achievement_id),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# --- Point transaction functions ---

def spend_points_on_xp(user_id, amount):
    conn = get_connection()
    conn.execute(
        "INSERT INTO point_transactions (user_id, amount, transaction_type) VALUES (?, ?, 'spent_xp')",
        (user_id, -amount),
    )
    conn.commit()
    conn.close()


def get_point_transactions(user_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM point_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return rows
