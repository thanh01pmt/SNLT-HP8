# -------------------------------------------------------------------
# File: main_app.py
# Sản phẩm bài học 8.1: Giao Diện Trò Chơi Cơ Bản với Dữ liệu SQLite
# -------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys

# --- PHẦN 1: HÀM HỖ TRỢ VÀ CÁC HẰNG SỐ ---

def resource_path(relative_path):
    """
    Lấy đường dẫn tuyệt đối đến tài nguyên.
    Cần thiết để ứng dụng hoạt động sau khi được đóng gói bằng PyInstaller.
    """
    try:
        # PyInstaller tạo thư mục tạm và lưu đường dẫn ở _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("brain_quest.db")

# --- PHẦN 2: LỚP ỨNG DỤNG CHÍNH ---

class QuizAppBasic(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # --- Cấu hình cửa sổ chính ---
        self.title("Brain Quest - Giai đoạn 1 (SQLite Data)")
        self.geometry("600x400")
        self.resizable(False, False) # Không cho thay đổi kích thước

        # --- Khởi tạo các thuộc tính (biến trạng thái) ---
        self.current_question_data = None # Sẽ lưu tuple (id, q_text, opts_text, correct_ans_text)
        self.current_score = 0

        # --- Xây dựng giao diện ---
        self._setup_ui()
        
        # --- Tải câu hỏi đầu tiên khi khởi động ---
        self._load_and_display_question()

    def _connect_db(self):
        """
        Hàm helper để kết nối đến CSDL.
        Trả về đối tượng connection và cursor.
        """
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
        Tải một câu hỏi ngẫu nhiên từ CSDL và trả về dưới dạng tuple.
        """
        conn, cursor = self._connect_db()
        if not conn: return None

        try:
            # Lấy một câu hỏi ngẫu nhiên từ bảng questions
            cursor.execute("SELECT id, question_text, options_text, correct_answer_text FROM questions ORDER BY RANDOM() LIMIT 1")
            question = cursor.fetchone()
            return question
        except sqlite3.Error as e:
            messagebox.showerror("Lỗi Truy vấn", f"Không thể tải câu hỏi: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def _setup_ui(self):
        """
        Hàm này tạo và sắp xếp tất cả các widget trên giao diện.
        """
        # Frame chính để chứa tất cả các widget khác
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Label để hiển thị câu hỏi
        self.question_label = ttk.Label(
            main_frame,
            text="Đang tải câu hỏi...",
            font=("Arial", 14, "bold"),
            wraplength=550, # Tự động xuống dòng nếu text quá dài
            justify="center"
        )
        self.question_label.pack(pady=20)

        # Frame để chứa các nút lựa chọn
        self.options_frame = ttk.Frame(main_frame)
        self.options_frame.pack(pady=10)

        # Tạo 4 nút lựa chọn và thêm vào list
        self.option_buttons = []
        style = ttk.Style()
        style.configure("Option.TButton", font=("Arial", 11), padding=5)
        for i in range(4):
            btn = ttk.Button(
                self.options_frame,
                text=f"Lựa chọn {i+1}",
                command=lambda idx=i: self._option_selected(idx),
                width=25,
                style="Option.TButton"
            )
            # Sắp xếp các nút thành lưới 2x2
            btn.grid(row=i//2, column=i%2, padx=5, pady=5)
            self.option_buttons.append(btn)

        # Label để hiển thị điểm số
        self.score_label = ttk.Label(main_frame, text=f"Điểm: {self.current_score}", font=("Arial", 12))
        self.score_label.pack(pady=10)
        
        # Nút "Câu Tiếp Theo"
        self.next_button = ttk.Button(main_frame, text="Câu Tiếp Theo", command=self._load_and_display_question)
        self.next_button.pack(pady=10)

    def _load_and_display_question(self):
        """
        Hàm trung tâm: tải câu hỏi mới từ DB và cập nhật giao diện.
        """
        self.current_question_data = self._load_question_from_db()

        if self.current_question_data:
            # Dữ liệu trả về là: (id, q_text, opts_text, correct_ans_text)
            _id, q_text, opts_text, _correct_ans_text = self.current_question_data
            
            # Cập nhật Label câu hỏi
            self.question_label.config(text=q_text)
            
            # Tách chuỗi options_text thành một list các lựa chọn
            options = opts_text.split(';')
            
            # Cập nhật text cho các nút lựa chọn
            for i, btn in enumerate(self.option_buttons):
                if i < len(options):
                    btn.config(text=options[i], state=tk.NORMAL)
                else:
                    # Nếu câu hỏi có ít hơn 4 lựa chọn, vô hiệu hóa các nút thừa
                    btn.config(text="", state=tk.DISABLED)
        else:
            # Xử lý trường hợp không tải được câu hỏi (hết câu hỏi hoặc lỗi)
            self.question_label.config(text="Không còn câu hỏi hoặc lỗi tải dữ liệu.")
            for btn in self.option_buttons:
                btn.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

    def _option_selected(self, index):
        """
        Hàm được gọi khi người dùng nhấn vào một nút lựa chọn.
        Ở Buổi 8.1, nó chỉ hiển thị thông tin, chưa tính điểm.
        """
        if self.current_question_data is None:
            return

        _id, _q_text, opts_text, correct_ans_text = self.current_question_data
        options = opts_text.split(';')
        
        if 0 <= index < len(options):
            selected_answer = options[index]
            
            # Hiển thị thông báo (logic tạm thời cho 8.1)
            is_correct = (selected_answer == correct_ans_text)
            if is_correct:
                self.current_score += 10 # Tạm thời thêm logic tính điểm
                self.score_label.config(text=f"Điểm: {self.current_score}")
                messagebox.showinfo("Chính xác!", f"Bạn đã chọn đúng: {selected_answer}")
            else:
                messagebox.showerror("Sai rồi!", f"Bạn đã chọn: {selected_answer}\nĐáp án đúng là: {correct_ans_text}")

            # Sau khi trả lời, tự động chuyển sang câu tiếp theo
            self._load_and_display_question()


# --- PHẦN 3: KHỞI CHẠY ỨNG DỤNG ---

if __name__ == "__main__":
    # Dòng này sẽ là điểm bắt đầu của chương trình
    app = QuizAppBasic()
    app.mainloop()