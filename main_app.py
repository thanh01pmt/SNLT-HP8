# -------------------------------------------------------------------
# File: main_app.py
# Dự án: SNLT-HP8-B6-ProjectBasic
# -------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import random
import requests
import html
import time # Cần cho việc giả lập mạng chậm để test threading
import threading

# Giả sử file sound_manager.py đã có
from sound_manager import SoundManager

# --- PHẦN 1: HÀM HỖ TRỢ VÀ CÁC HẰNG SỐ ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("brain_quest.db")
OPENTDB_API_URL = "https://opentdb.com/api.php"

# --- PHẦN 2: LỚP ỨNG DỤNG CHÍNH ---

class QuizAppWithThreading(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("SNLT-HP8-B6-ProjectBasic (Threading)")
        self.geometry("650x500")
        self.resizable(False, False)

        self.current_question_data = None
        self.current_score = 0
        self.current_question_is_from_api = False

        self.sound_manager = SoundManager()

        self.api_questions_result = None
        self.api_thread_running = False

        self._setup_ui()
        self._load_and_display_question_from_db()

    # --- Các hàm làm việc với DB và API (Giữ nguyên) ---
    def _connect_db(self):
        if not os.path.exists(DB_PATH):
            messagebox.showerror("Lỗi CSDL", f"Không tìm thấy file CSDL tại: {DB_PATH}")
            self.quit(); return None, None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            return conn, cursor
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi CSDL", f"Không thể kết nối đến CSDL: {e}")
            self.quit(); return None, None

    def _load_question_from_db(self):
        conn, cursor = self._connect_db()
        if not conn: return None
        try:
            cursor.execute("SELECT question_text, options_text, correct_answer_text FROM questions ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                q_text, opts_text, correct_ans = row
                return { "question": q_text, "options": opts_text.split(';'), "correct_answer_text": correct_ans }
            return None
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi Truy vấn DB", f"Không thể tải câu hỏi từ DB: {e}")
            return None
        finally:
            if conn: conn.close()
    
    def _fetch_questions_from_api(self, amount=1):
        params = {'amount': amount, 'type': 'multiple'}
        api_questions_list = []
        try:
            # time.sleep(5)
            response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("response_code") == 0 and data.get("results"):
                for item in data.get("results", []):
                    question_text = html.unescape(item.get("question", ""))
                    correct_answer = html.unescape(item.get("correct_answer", ""))
                    incorrect_answers = [html.unescape(ans) for ans in item.get("incorrect_answers", [])]
                    options = incorrect_answers + [correct_answer]
                    random.shuffle(options)
                    api_questions_list.append({
                        "question": question_text, "options": options, "correct_answer_text": correct_answer
                    })
            else:
                print(f"API Error Code: {data.get('response_code')}")
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi gọi API: {e}")
        return api_questions_list


    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        source_frame = ttk.Frame(main_frame)
        source_frame.pack(pady=(0, 15), fill=tk.X)
        ttk.Label(source_frame, text="Nguồn Câu Hỏi:").pack(side=tk.LEFT, padx=(0, 10))
        self.load_db_button = ttk.Button(source_frame, text="Từ CSDL Local", command=self._load_and_display_question_from_db)
        self.load_db_button.pack(side=tk.LEFT, padx=5)
        self.load_api_button = ttk.Button(source_frame, text="Từ Internet (API)", command=lambda: self._load_and_display_question_from_api(amount=1))
        self.load_api_button.pack(side=tk.LEFT, padx=5)

        self.question_label = ttk.Label(main_frame, text="Chọn nguồn để bắt đầu!", font=("Arial", 16, "bold"), wraplength=600, justify="center")
        self.question_label.pack(pady=20)

        self.options_frame = ttk.Frame(main_frame)
        self.options_frame.pack(pady=10)
        self.option_buttons = []
        style = ttk.Style()
        style.configure("Option.TButton", font=("Arial", 11), padding=5)
        for i in range(4):
            btn = ttk.Button(self.options_frame, text="", command=lambda idx=i: self._option_selected(idx), width=30, style="Option.TButton", state=tk.DISABLED)
            btn.grid(row=i//2, column=i%2, padx=10, pady=5, sticky="ew")
            self.option_buttons.append(btn)

        self.score_label = ttk.Label(main_frame, text=f"Điểm: {self.current_score}", font=("Arial", 13))
        self.score_label.pack(pady=10)
        
        self.result_feedback_label = ttk.Label(main_frame, text="", font=("Arial", 12, "italic"))
        self.result_feedback_label.pack(pady=5)

        self.next_button = ttk.Button(main_frame, text="Câu Tiếp Theo", command=self._handle_next_question_logic, state=tk.DISABLED)
        self.next_button.pack(pady=15)

    def _load_and_display_question_from_db(self):
        self.sound_manager.play_click()
        self.current_question_is_from_api = False
        db_question_data = self._load_question_from_db()
        self.current_question_data = db_question_data
        self._update_ui_with_current_question()

    def _load_and_display_question_from_api(self, amount=1):
        self.sound_manager.play_click()
        if self.api_thread_running:
            messagebox.showinfo("Đang xử lý", "Đang tải câu hỏi từ API, vui lòng đợi...")
            return

        self.question_label.config(text="Đang tải câu hỏi từ API, xin chờ...")
        self.load_api_button.config(state=tk.DISABLED)
        self.load_db_button.config(state=tk.DISABLED)
        for btn in self.option_buttons:
            btn.config(state=tk.DISABLED)
        self.update_idletasks()

        self.api_questions_result = None 
        self.api_thread_running = True

        api_thread = threading.Thread(
            target=self._fetch_api_questions_background_task,
            args=(amount,),
            daemon=True
        )
        api_thread.start()
        self._check_api_fetch_status()

    def _fetch_api_questions_background_task(self, amount):
        result = self._fetch_questions_from_api(amount=amount)
        self.api_questions_result = result

    def _check_api_fetch_status(self):
        if self.api_questions_result is not None:
            self.api_thread_running = False
            self.load_api_button.config(state=tk.NORMAL)
            self.load_db_button.config(state=tk.NORMAL)
            api_questions = self.api_questions_result
            
            if api_questions:
                self.current_question_is_from_api = True
                self.current_question_data = random.choice(api_questions)
                self._update_ui_with_current_question()
            else:
                self.question_label.config(text="Lỗi tải câu hỏi từ API. Vui lòng thử lại hoặc chọn nguồn DB.")
        else:
            self.after(200, self._check_api_fetch_status)

    def _update_ui_with_current_question(self):
        if not self.current_question_data:
            self.question_label.config(text="Không có câu hỏi để hiển thị.")
            for btn in self.option_buttons: btn.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return

        q_data = self.current_question_data
        self.question_label.config(text=q_data["question"])
        self.result_feedback_label.config(text="")
        self.next_button.config(state=tk.DISABLED)

        for i, btn in enumerate(self.option_buttons):
            if i < len(q_data["options"]):
                btn.config(text=q_data["options"][i], state=tk.NORMAL)
            else:
                btn.config(text="", state=tk.DISABLED)

    def _option_selected(self, index):
        if not self.current_question_data: return
        self.sound_manager.play_click()
        q_data = self.current_question_data
        options = q_data["options"]
        correct_answer_text = q_data["correct_answer_text"]

        if 0 <= index < len(options):
            selected_answer_text = options[index]
            for btn in self.option_buttons:
                btn.config(state=tk.DISABLED)
            if selected_answer_text == correct_answer_text:
                self.current_score += 10
                self.result_feedback_label.config(text="Chính xác!", foreground="green")
                self.sound_manager.play_correct()
            else:
                self.result_feedback_label.config(text=f"Sai rồi! Đáp án đúng là: {correct_answer_text}", foreground="red")
                self.sound_manager.play_wrong()
            self.score_label.config(text=f"Điểm: {self.current_score}")
            self.next_button.config(state=tk.NORMAL)

    def _handle_next_question_logic(self):
        self.sound_manager.play_click()
        if self.current_question_is_from_api:
            self._load_and_display_question_from_api(amount=1)
        else:
            self._load_and_display_question_from_db()

# --- PHẦN 3: KHỞI CHẠY ỨNG DỤNG ---
if __name__ == "__main__":
    # Kiểm tra và có thể tạo DB/bảng nếu chưa có
    if not os.path.exists(DB_PATH):
        ### SỬA LỖI CÚ PHÁP Ở ĐÂY ###
        try:
            print(f"Đang tạo file CSDL '{DB_PATH}'...")
            conn_init = sqlite3.connect(DB_PATH)
            cursor_init = conn_init.cursor()
            # Tạo bảng questions nếu chưa có
            cursor_init.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    options_text TEXT NOT NULL, 
                    correct_answer_text TEXT NOT NULL
                )
            ''')
            conn_init.commit()
            conn_init.close()
            print(f"Đã tạo CSDL và bảng 'questions'. Vui lòng thêm dữ liệu mẫu.")
        except sqlite3.Error as e: # <<< THÊM KHỐI EXCEPT ĐỂ BẮT LỖI
            print(f"LỖI nghiêm trọng khi cố gắng tạo CSDL: {e}")
        ### KẾT THÚC SỬA LỖI ###

    app = QuizAppWithThreading()
    app.mainloop()