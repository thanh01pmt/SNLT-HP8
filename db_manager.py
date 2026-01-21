# -------------------------------------------------------------------
# File: db_manager.py
# Dự án: SNLT-HP8-B8-ProjectBasic
# -------------------------------------------------------------------
import sqlite3
import os
import sys

DB_NAME = "brain_quest.db"

def resource_path_db(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DatabaseManager:
    def __init__(self, db_name=resource_path_db(DB_NAME)):
        self.db_name = db_name
        self._create_or_update_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _create_or_update_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Bảng questions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    options_text TEXT NOT NULL,
                    correct_answer_text TEXT NOT NULL,
                    explanation TEXT
                )
            ''')
            # Kiểm tra và thêm cột explanation nếu chưa có
            cursor.execute("PRAGMA table_info(questions)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'explanation' not in columns:
                cursor.execute("ALTER TABLE questions ADD COLUMN explanation TEXT")

            # Bảng users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE
                )
            ''')
            
            # Bảng scores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    score_value INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            conn.commit()
        except sqlite3.Error as e:
            print(f"Lỗi khi tạo/cập nhật bảng: {e}")
        finally:
            if conn:
                conn.close()

    def get_random_questions(self, limit=5):
        """Lấy một SỐ LƯỢNG câu hỏi ngẫu nhiên từ DB."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT question_text, options_text, correct_answer_text, explanation FROM questions ORDER BY RANDOM() LIMIT ?", (limit,))
            rows = cursor.fetchall()
            questions_list = []
            for row in rows:
                q_text, opts_text, correct_ans, explanation = row
                questions_list.append({
                    "question": q_text,
                    "options": opts_text.split(';'),
                    "correct_answer_text": correct_ans,
                    "explanation": explanation
                })
            return questions_list
        except sqlite3.Error as e:
            print(f"Lỗi khi lấy nhiều câu hỏi ngẫu nhiên DB: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_all_questions(self):
        """Lấy TẤT CẢ câu hỏi cho chế độ ôn tập."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT question_text, options_text, correct_answer_text, explanation FROM questions ORDER BY id"
            cursor.execute(sql)
            rows = cursor.fetchall()
            questions_list = []
            for row in rows:
                q_text, opts_text, correct_ans, explanation = row
                questions_list.append({
                    "question": q_text,
                    "options": opts_text.split(';'),
                    "correct_answer_text": correct_ans,
                    "explanation": explanation
                })
            return questions_list
        except sqlite3.Error as e:
            print(f"Lỗi khi lấy tất cả câu hỏi: {e}")
            return []
        finally:
            conn.close()

    def add_or_get_user(self, username):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user:
                return user[0]
            else:
                cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Lỗi khi xử lý user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def add_score(self, user_id, score_value):
        if user_id is None:
            print("Lỗi: Không thể lưu điểm vì user_id là None.")
            return False
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO scores (user_id, score_value) VALUES (?, ?)", (user_id, score_value))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Lỗi khi thêm điểm: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_top_scores(self, limit=10):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT u.username, s.score_value, STRFTIME('%d-%m-%Y %H:%M', s.timestamp)
                FROM scores s
                JOIN users u ON s.user_id = u.user_id
                ORDER BY s.score_value DESC, s.timestamp DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Lỗi khi lấy top scores: {e}")
            return []
        finally:
            if conn:
                conn.close()