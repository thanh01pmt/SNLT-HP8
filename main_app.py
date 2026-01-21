# -------------------------------------------------------------------
# File: main_app.py
# Dự án: SNLT-HP8-B3-ProjectBasic (Tích hợp từ Bài 2)
# -------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import random
import requests
import html

### CODE BÀI 3: THÊM IMPORT MỚI ###
from sound_manager import SoundManager # Import lớp quản lý âm thanh
### KẾT THÚC CODE BÀI 3 ###

# --- PHẦN 1: HÀM HỖ TRỢ VÀ CÁC HẰNG SỐ ---
# (Giữ nguyên từ các bài trước)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("brain_quest.db")
OPENTDB_API_URL = "https://opentdb.com/api.php"

# --- PHẦN 2: LỚP ỨNG DỤNG CHÍNH ---

class QuizAppWithSound(tk.Tk): # Đổi tên lớp
    def __init__(self):
        super().__init__()
        
        self.title("SNLT-HP8-B3-ProjectBasic (Âm thanh)")
        self.geometry("650x500")
        self.resizable(False, False)

        self.current_question_data = None
        self.current_score = 0
        self.current_question_is_from_api = False

        ### CODE BÀI 3: KHỞI TẠO SOUND MANAGER ###
        self.sound_manager = SoundManager()
        ### KẾT THÚC CODE BÀI 3 ###

        self._setup_ui()
        self._load_and_display_question_from_db()

    # --- Các hàm làm việc với DB và API (Giữ nguyên từ Bài 2) ---
    def _connect_db(self):
        # ... (code giữ nguyên) ...
        if not os.path.exists(DB_PATH):
            messagebox.showerror("Lỗi CSDL", f"Không tìm thấy file CSDL tại: {DB_PATH}")
            self.quit()
            return None, None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            return conn, cursor
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi CSDL", f"Không thể kết nối đến CSDL: {e}")
            self.quit()
            return None, None
            
    def _load_question_from_db(self):
        # ... (code giữ nguyên) ...
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
            if conn:
                conn.close()

    def _fetch_question_from_api(self):
        # ... (code giữ nguyên) ...
        params = {'amount': 1, 'type': 'multiple'}
        try:
            response = requests.get(OPENTDB_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("response_code") == 0 and data.get("results"):
                item = data["results"][0]
                question_text = html.unescape(item.get("question", ""))
                correct_answer = html.unescape(item.get("correct_answer", ""))
                incorrect_answers = [html.unescape(ans) for ans in item.get("incorrect_answers", [])]
                options = incorrect_answers + [correct_answer]
                random.shuffle(options)
                return { "question": question_text, "options": options, "correct_answer_text": correct_answer }
            else:
                messagebox.showerror("Lỗi API", f"API không trả về kết quả hợp lệ. Code: {data.get('response_code')}")
                return None
        except requests.exceptions.Timeout:
            messagebox.showerror("Lỗi Kết Nối", "Hết thời gian chờ khi kết nối API.")
            return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Lỗi Kết Nối", f"Lỗi khi gọi API: {e}")
            return None
        except Exception as e:
            messagebox.showerror("Lỗi Xử Lý", f"Lỗi không xác định: {e}")
            return None

    def _setup_ui(self):
        # (Hàm này giữ nguyên cấu trúc từ Bài 2)
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        source_frame = ttk.Frame(main_frame)
        source_frame.pack(pady=(0, 15), fill=tk.X)
        ttk.Label(source_frame, text="Nguồn Câu Hỏi:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(source_frame, text="Từ CSDL Local", command=self._load_and_display_question_from_db).pack(side=tk.LEFT, padx=5)
        ttk.Button(source_frame, text="Từ Internet (API)", command=self._load_and_display_question_from_api).pack(side=tk.LEFT, padx=5)

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
        ### CODE BÀI 3: THÊM ÂM THANH CLICK ###
        self.sound_manager.play_click()
        ### KẾT THÚC CODE BÀI 3 ###
        self.current_question_is_from_api = False
        db_question_data = self._load_question_from_db()
        self.current_question_data = db_question_data
        self._update_ui_with_current_question()

    def _load_and_display_question_from_api(self):
        ### CODE BÀI 3: THÊM ÂM THANH CLICK ###
        self.sound_manager.play_click()
        ### KẾT THÚC CODE BÀI 3 ###
        self.question_label.config(text="Đang tải từ API...")
        self.update_idletasks()

        api_questions = self._fetch_question_from_api() # Sửa lại tên biến cho rõ
        
        if api_questions:
            self.current_question_is_from_api = True
            self.current_question_data = api_questions # Sửa lại tên biến
            self._update_ui_with_current_question()
        else:
            self.question_label.config(text="Lỗi tải câu hỏi từ API. Chọn nguồn khác.")
            if self.current_question_data is None:
                 for btn in self.option_buttons: btn.config(state=tk.DISABLED)
                 self.next_button.config(state=tk.DISABLED)

    def _update_ui_with_current_question(self):
        # (Hàm này giữ nguyên từ Bài 8.2)
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
        
        ### CODE BÀI 3: THÊM ÂM THANH CLICK ###
        self.sound_manager.play_click()
        ### KẾT THÚC CODE BÀI 3 ###

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
                ### CODE BÀI 3: PHÁT ÂM THANH ĐÚNG ###
                self.sound_manager.play_correct()
                ### KẾT THÚC CODE BÀI 3 ###
            else:
                self.result_feedback_label.config(text=f"Sai rồi! Đáp án đúng là: {correct_answer_text}", foreground="red")
                ### CODE BÀI 3: PHÁT ÂM THANH SAI ###
                self.sound_manager.play_wrong()
                ### KẾT THÚC CODE BÀI 3 ###
            
            self.score_label.config(text=f"Điểm: {self.current_score}")
            self.next_button.config(state=tk.NORMAL)

    def _handle_next_question_logic(self):
        ### CODE BÀI 3: THÊM ÂM THANH CLICK ###
        self.sound_manager.play_click()
        ### KẾT THÚC CODE BÀI 3 ###
        
        if self.current_question_is_from_api:
            self._load_and_display_question_from_api()
        else:
            self._load_and_display_question_from_db()

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        try:
            print(f"Đang tạo file CSDL '{DB_PATH}'...")
            conn_init = sqlite3.connect(DB_PATH)
            cursor_init = conn_init.cursor()
            cursor_init.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    options_text TEXT NOT NULL, 
                    correct_answer_text TEXT NOT NULL ) ''')
            conn_init.commit()
            conn_init.close()
            print(f"Đã tạo CSDL và bảng 'questions'. Vui lòng thêm dữ liệu mẫu.")
        except sqlite3.Error as e:
            print(f"LỖI khi cố gắng tạo CSDL: {e}")
    
    app = QuizAppWithSound()
    app.mainloop()