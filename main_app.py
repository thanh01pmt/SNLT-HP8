# -------------------------------------------------------------------
# File: main_app.py
# Dự án: SNLT-HP8-B2-ProjectBasic (Tích hợp từ 8.1)
# -------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys
import random

### CODE BÀI 2 ###
import requests # Thư viện để gọi API
import html     # Thư viện để giải mã các ký tự đặc biệt từ API
### KẾT THÚC CODE BÀI 2 ###

# --- PHẦN 1: HÀM HỖ TRỢ VÀ CÁC HẰNG SỐ ---

def resource_path(relative_path):
    """
    Lấy đường dẫn tuyệt đối đến tài nguyên.
    Cần thiết để ứng dụng hoạt động sau khi được đóng gói bằng PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("brain_quest.db")

### CODE BÀI 2 ###
OPENTDB_API_URL = "https://opentdb.com/api.php" # URL cơ sở của API
### KẾT THÚC CODE BÀI 2 ###


# --- PHẦN 2: LỚP ỨNG DỤNG CHÍNH ---

class QuizAppWithAPI(tk.Tk): # Đổi tên lớp để phản ánh chức năng mới
    def __init__(self):
        super().__init__()
        
        self.title("SNLT-HP8-B2-ProjectBasic (API & DB)")
        self.geometry("650x500") # Tăng kích thước
        self.resizable(False, False)

        ### CODE BÀI 2 ###
        # self.current_question_data giờ sẽ là dictionary để thống nhất dữ liệu
        # Format: {"question": str, "options": list, "correct_answer_text": str}
        self.current_question_data = None
        self.current_score = 0
        self.current_question_is_from_api = False # Cờ để biết nguồn câu hỏi cho "Next"
        ### KẾT THÚC CODE BÀI 2 ###

        self._setup_ui()
        self._load_and_display_question_from_db() # Bắt đầu bằng câu hỏi từ DB

    def _connect_db(self):
        # (Hàm này giữ nguyên như Bài 8.1)
        if not os.path.exists(DB_PATH):
            messagebox.showerror("Lỗi CSDL", f"Không tìm thấy file CSDL tại: {DB_PATH}\nVui lòng tạo file và thêm dữ liệu.")
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
        """
        Tải một câu hỏi ngẫu nhiên từ CSDL và trả về dưới dạng DICTIONARY.
        """
        conn, cursor = self._connect_db()
        if not conn: return None
        try:
            cursor.execute("SELECT question_text, options_text, correct_answer_text FROM questions ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            if row:
                ### CODE BÀI 2: Thay đổi để trả về dictionary ###
                q_text, opts_text, correct_ans = row
                return {
                    "question": q_text,
                    "options": opts_text.split(';'),
                    "correct_answer_text": correct_ans
                }
                ### KẾT THÚC CODE BÀI 2 ###
            return None
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi Truy vấn DB", f"Không thể tải câu hỏi từ DB: {e}")
            return None
        finally:
            if conn:
                conn.close()

    ### CODE BÀI 2: THÊM HÀM MỚI ĐỂ LẤY DỮ LIỆU TỪ API ###
    def _fetch_question_from_api(self):
        """Tải MỘT câu hỏi ngẫu nhiên từ Open Trivia Database API."""
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
                return {
                    "question": question_text,
                    "options": options,
                    "correct_answer_text": correct_answer
                }
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
    ### KẾT THÚC CODE BÀI 2 ###

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ### CODE BÀI 2: THÊM CÁC NÚT CHỌN NGUỒN CÂU HỎI ###
        source_frame = ttk.Frame(main_frame)
        source_frame.pack(pady=(0, 15), fill=tk.X)
        ttk.Label(source_frame, text="Nguồn Câu Hỏi:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(source_frame, text="Từ CSDL Local", command=self._load_and_display_question_from_db).pack(side=tk.LEFT, padx=5)
        ttk.Button(source_frame, text="Từ Internet (API)", command=self._load_and_display_question_from_api).pack(side=tk.LEFT, padx=5)
        ### KẾT THÚC CODE BÀI 2 ###

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
        
        ### CODE BÀI 2: THÊM LABEL PHẢN HỒI THAY CHO MESSAGEBOX ###
        self.result_feedback_label = ttk.Label(main_frame, text="", font=("Arial", 12, "italic"))
        self.result_feedback_label.pack(pady=5)
        ### KẾT THÚC CODE BÀI 2 ###

        self.next_button = ttk.Button(main_frame, text="Câu Tiếp Theo", command=self._handle_next_question_logic, state=tk.DISABLED)
        self.next_button.pack(pady=15)
        
    ### CODE BÀI 2: TÁCH LOGIC TẢI VÀ HIỂN THỊ ###
    def _load_and_display_question_from_db(self):
        self.current_question_is_from_api = False
        db_question_data = self._load_question_from_db()
        self.current_question_data = db_question_data
        self._update_ui_with_current_question()
    
    def _load_and_display_question_from_api(self):
        self.question_label.config(text="Đang tải câu hỏi từ Internet...")
        self.update_idletasks()
        api_question_data = self._fetch_question_from_api()
        if api_question_data:
            self.current_question_is_from_api = True
            self.current_question_data = api_question_data
            self._update_ui_with_current_question()
        else:
            self.question_label.config(text="Lỗi tải câu hỏi từ API. Vui lòng thử lại.")

    def _update_ui_with_current_question(self):
        """Hàm chung để cập nhật UI sau khi có self.current_question_data."""
        if not self.current_question_data:
            self.question_label.config(text="Không có câu hỏi để hiển thị.")
            for btn in self.option_buttons: btn.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            return

        q_data = self.current_question_data
        self.question_label.config(text=q_data["question"])
        self.result_feedback_label.config(text="") # Xóa feedback của câu trước
        self.next_button.config(state=tk.DISABLED)

        for i, btn in enumerate(self.option_buttons):
            if i < len(q_data["options"]):
                btn.config(text=q_data["options"][i], state=tk.NORMAL)
            else:
                btn.config(text="", state=tk.DISABLED)
    ### KẾT THÚC CODE BÀI 2 ###

    def _option_selected(self, index):
        if not self.current_question_data: return

        q_data = self.current_question_data
        options = q_data["options"]
        correct_answer_text = q_data["correct_answer_text"]

        if 0 <= index < len(options):
            selected_answer_text = options[index]
            
            ### CODE BÀI 2: CẬP NHẬT LOGIC PHẢN HỒI VÀ VÔ HIỆU HÓA NÚT ###
            for btn in self.option_buttons:
                btn.config(state=tk.DISABLED)

            if selected_answer_text == correct_answer_text:
                self.current_score += 10
                self.result_feedback_label.config(text="Chính xác!", foreground="green")
            else:
                self.result_feedback_label.config(text=f"Sai rồi! Đáp án đúng là: {correct_answer_text}", foreground="red")
            
            self.score_label.config(text=f"Điểm: {self.current_score}")
            self.next_button.config(state=tk.NORMAL) # Cho phép nhấn "Câu Tiếp Theo"
            ### KẾT THÚC CODE BÀI 2 ###
    
    ### CODE BÀI 2: THÊM HÀM MỚI CHO NÚT NEXT ###
    def _handle_next_question_logic(self):
        """Xử lý logic khi nhấn nút "Câu Tiếp Theo"."""
        if self.current_question_is_from_api:
            self._load_and_display_question_from_api()
        else:
            self._load_and_display_question_from_db()
    ### KẾT THÚC CODE BÀI 2 ###

if __name__ == "__main__":
    app = QuizAppWithAPI()
    app.mainloop()