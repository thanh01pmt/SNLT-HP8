# -------------------------------------------------------------------
# File: db_manager.py
# Dự án: SNLT-HP8-B7-ProjectBasic
# -------------------------------------------------------------------

import sqlite3
import os
import sys

# Giả sử file models.py đã được tạo ở các bài trước
# from models import Question 

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
        self._create_tables()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        ### CODE BÀI 7: BẬT HỖ TRỢ KHÓA NGOẠI ###
        conn.execute("PRAGMA foreign_keys = ON")
        ### KẾT THÚC CODE BÀI 7 ###
        return conn

    def _create_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Bảng questions giữ nguyên từ các bài trước
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    options_text TEXT NOT NULL,
                    correct_answer_text TEXT NOT NULL
                    -- Các cột khác như explanation, category có thể thêm ở đây
                )
            ''')
            
            ### CODE BÀI 7: THÊM BẢNG USERS VÀ SCORES ###
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    score_value INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')
            ### KẾT THÚC CODE BÀI 7 ###
            conn.commit()
        except sqlite3.Error as e:
            print(f"Lỗi khi tạo bảng: {e}")
        finally:
            conn.close()

    # --- Question Methods (Giữ nguyên) ---
    def get_random_question(self):
        # ... (code giữ nguyên từ các bài trước, trả về dictionary) ...
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT question_text, options_text, correct_answer_text FROM questions ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                q_text, opts_text, correct_ans = row
                return { "question": q_text, "options": opts_text.split(';'), "correct_answer_text": correct_ans }
            return None
        except sqlite3.Error as e:
            print(f"Lỗi khi lấy câu hỏi ngẫu nhiên DB: {e}")
            return None
        finally:
            if conn:
                conn.close()

    ### CODE BÀI 7: THÊM CÁC HÀM XỬ LÝ USER VÀ SCORE ###
    def add_or_get_user(self, username):
        """Thêm user mới nếu chưa có, hoặc lấy user_id nếu đã có. Trả về user_id."""
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
            conn.close()

    def add_score(self, user_id, score_value):
        """Thêm một dòng điểm mới vào bảng scores."""
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
            conn.close()

    def get_top_scores(self, limit=10):
        """Lấy top N điểm cao nhất, nối bảng để lấy username."""
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
            conn.close()
    ### KẾT THÚC CODE BÀI 7 ###