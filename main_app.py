# -------------------------------------------------------------------
# File: main_app.py
# Dự án: SNLT-HP8-B7-ProjectBasic
# -------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import os
import sys
import random
import requests
import html
import threading
import time

from sound_manager import SoundManager
from db_manager import DatabaseManager

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DB_PATH = resource_path("brain_quest.db")
OPENTDB_API_URL = "https://opentdb.com/api.php"

class QuizAppWithLeaderboard(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("SNLT-HP8-B7-ProjectBasic (Bảng Xếp Hạng)")
        self.geometry("700x550")
        self.resizable(False, False)
        
        self.db_manager = DatabaseManager()
        self.sound_manager = SoundManager()
        
        self.player_label = None; self.score_label = None
        self.question_label = None; self.option_buttons = []
        self.result_feedback_label = None; self.next_button = None
        
        self.current_player_name = None; self.current_player_id = None
        self.current_score = 0; self.current_question_data = None
        self.current_question_is_from_api = False
        
        self.api_questions_result = None; self.api_thread_running = False
        
        self.questions_to_play = []; self.current_question_index = -1
        
        self._setup_main_menu()
        self._show_welcome_screen()

    def _setup_main_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trò Chơi", menu=game_menu)
        game_menu.add_command(label="Chơi Mới", command=self.start_new_game_flow)
        game_menu.add_separator()
        game_menu.add_command(label="Bảng Xếp Hạng", command=self.show_leaderboard_window)
        game_menu.add_separator()
        game_menu.add_command(label="Thoát", command=self.quit)

    def _clear_main_window(self):
        for widget in self.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()
        self._setup_main_menu()

    def _show_welcome_screen(self):
        self._clear_main_window()
        welcome_frame = ttk.Frame(self, padding="20")
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(welcome_frame, text="Chào mừng đến với Brain Quest Arena!", font=("Arial", 24, "bold")).pack(pady=20)
        ttk.Button(welcome_frame, text="Chơi Mới", command=self.start_new_game_flow, width=30).pack(pady=10)
        ttk.Button(welcome_frame, text="Xem Bảng Xếp Hạng", command=self.show_leaderboard_window, width=30).pack(pady=10)
        ttk.Button(welcome_frame, text="Thoát", command=self.quit, width=30).pack(pady=10)

    def start_new_game_flow(self):
        self.sound_manager.play_click()
        player_name_input = simpledialog.askstring("Tên Người Chơi", "Nhập tên của bạn:", parent=self)
        if player_name_input and player_name_input.strip():
            self.current_player_name = player_name_input.strip()
            self.current_player_id = self.db_manager.add_or_get_user(self.current_player_name)
            if self.current_player_id is None:
                messagebox.showerror("Lỗi User", "Không thể tạo hoặc lấy thông tin người chơi.")
                return
            self._show_source_selection_screen()

    def _show_source_selection_screen(self):
        self._clear_main_window()
        source_frame = ttk.Frame(self, padding="20")
        source_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(source_frame, text=f"Chào {self.current_player_name}, hãy chọn nguồn câu hỏi:", font=("Arial", 18, "bold")).pack(pady=20)
        ttk.Button(source_frame, text="Chơi với câu hỏi Local (DB)", command=self.initiate_game_screen_from_db, width=30).pack(pady=10)
        ttk.Button(source_frame, text="Chơi với câu hỏi từ Internet (API)", command=self.initiate_game_screen_from_api, width=30).pack(pady=10)
        ttk.Button(source_frame, text="Quay lại", command=self._show_welcome_screen, width=30).pack(pady=10)

    def initiate_game_screen_from_db(self, num_questions=5):
        self.current_question_is_from_api = False
        self.questions_to_play = self.db_manager.get_random_questions(limit=num_questions)
        if not self.questions_to_play:
            messagebox.showinfo("Thông báo", "Không có đủ câu hỏi trong CSDL.", parent=self)
            self._show_welcome_screen()
            return
        self.current_question_index = -1
        self.initiate_game_screen()
        self._handle_next_question_logic()
    
    def initiate_game_screen_from_api(self, num_questions=5):
        self.current_question_is_from_api = True
        self.initiate_game_screen()
        self._load_and_display_question_from_api_set(amount=num_questions)

    def initiate_game_screen(self):
        self._clear_main_window()
        self.current_score = 0
        game_frame = ttk.Frame(self, padding="15"); game_frame.pack(fill=tk.BOTH, expand=True)
        player_info_frame = ttk.Frame(game_frame); player_info_frame.pack(fill=tk.X, pady=(0, 10))
        self.player_label = ttk.Label(player_info_frame, text=f"Người chơi: {self.current_player_name}", font=("Arial", 12))
        self.player_label.pack(side=tk.LEFT)
        self.score_label = ttk.Label(player_info_frame, text=f"Điểm: {self.current_score}", font=("Arial", 12))
        self.score_label.pack(side=tk.RIGHT)
        self.question_label = ttk.Label(game_frame, text="...", font=("Arial", 16, "bold"), wraplength=680, justify="center")
        self.question_label.pack(pady=15)
        self.options_frame = ttk.Frame(game_frame); self.options_frame.pack(pady=10)
        self.option_buttons = []
        style = ttk.Style(); style.configure("Option.TButton", font=("Arial", 11), padding=5)
        for i in range(4):
            btn = ttk.Button(self.options_frame, text="", command=lambda idx=i: self._option_selected(idx), width=30, style="Option.TButton", state=tk.DISABLED)
            btn.grid(row=i//2, column=i%2, padx=10, pady=5, sticky="ew")
            self.option_buttons.append(btn)
        self.result_feedback_label = ttk.Label(game_frame, text="", font=("Arial", 12, "italic"))
        self.result_feedback_label.pack(pady=5)
        controls_frame = ttk.Frame(game_frame); controls_frame.pack(pady=15, side=tk.BOTTOM)
        self.next_button = ttk.Button(controls_frame, text="Câu Tiếp Theo", command=self._handle_next_question_logic, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=10)
        ttk.Button(controls_frame, text="Kết thúc Lượt", command=self.end_current_game_session).pack(side=tk.LEFT, padx=10)

    def end_current_game_session(self, message="Kết thúc lượt chơi!"):
        self.sound_manager.play_click()
        if self.current_player_id is not None:
            self.db_manager.add_score(self.current_player_id, self.current_score)
        messagebox.showinfo("Kết thúc", f"{message}\nĐiểm của bạn: {self.current_score}", parent=self)
        self._show_welcome_screen()

    def show_leaderboard_window(self):
        self.sound_manager.play_click()
        leaderboard_win = tk.Toplevel(self)
        leaderboard_win.title("Bảng Xếp Hạng")
        leaderboard_win.geometry("550x400")
        leaderboard_win.resizable(False, False)
        leaderboard_win.transient(self); leaderboard_win.grab_set()
        main_frame = ttk.Frame(leaderboard_win, padding="10"); main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="TOP 10 NGƯỜI CHƠI", font=("Arial", 16, "bold")).pack(pady=10)
        columns = ("rank", "username", "score", "timestamp")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=10)
        tree.heading("rank", text="Hạng"); tree.column("rank", width=50, anchor="center", stretch=tk.NO)
        tree.heading("username", text="Người chơi"); tree.column("username", width=200)
        tree.heading("score", text="Điểm"); tree.column("score", width=80, anchor="center")
        tree.heading("timestamp", text="Thời gian"); tree.column("timestamp", width=150, anchor="center")
        top_scores = self.db_manager.get_top_scores(limit=10)
        if top_scores:
            for i, (username, score, ts) in enumerate(top_scores):
                tree.insert("", tk.END, values=(i + 1, username, score, ts))
        else:
            tree.insert("", tk.END, values=("", "Chưa có dữ liệu", "", ""))
        tree.pack(fill=tk.BOTH, expand=True, pady=5)
        ttk.Button(main_frame, text="Đóng", command=leaderboard_win.destroy).pack(pady=10)

    def _fetch_questions_from_api(self, amount=5):
        params = {'amount': amount, 'type': 'multiple'}
        api_questions_list = []
        try:
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
                        "question": question_text, "options": options, "correct_answer_text": correct_answer, "explanation": ""
                    })
            else:
                print(f"API Error Code: {data.get('response_code')}")
        except requests.exceptions.RequestException as e:
            print(f"Lỗi khi gọi API: {e}")
        return api_questions_list

    def _load_and_display_question_from_api_set(self, amount=5):
        self.sound_manager.play_click()
        if self.api_thread_running:
            messagebox.showinfo("Đang xử lý", "Đang tải câu hỏi..."); return
        self.question_label.config(text="Đang tải bộ câu hỏi từ API, xin chờ...")
        self.update_idletasks()
        self.api_questions_result = None; self.api_thread_running = True
        api_thread = threading.Thread(target=self._fetch_api_questions_background_task, args=(amount,), daemon=True)
        api_thread.start()
        self._check_api_fetch_status_for_set()

    def _fetch_api_questions_background_task(self, amount):
        result = self._fetch_questions_from_api(amount=amount)
        self.api_questions_result = result

    def _check_api_fetch_status_for_set(self):
        if self.api_questions_result is not None:
            self.api_thread_running = False
            self.questions_to_play = self.api_questions_result
            if not self.questions_to_play:
                messagebox.showerror("Lỗi API", "Không thể tải bộ câu hỏi. Vui lòng thử lại.")
                self._show_source_selection_screen(); return
            self.current_question_index = -1
            self._handle_next_question_logic()
        else:
            self.after(200, self._check_api_fetch_status_for_set)

    def _handle_next_question_logic(self):
        self.sound_manager.play_click()
        self.current_question_index += 1
        if self.current_question_index < len(self.questions_to_play):
            self.current_question_data = self.questions_to_play[self.current_question_index]
            self._update_ui_with_current_question()
        else:
            self.end_current_game_session(message="Bạn đã hoàn thành lượt chơi!")

    def _update_ui_with_current_question(self):
        if not self.current_question_data:
            self.question_label.config(text="Không có câu hỏi để hiển thị."); return
        q_data = self.current_question_data
        self.question_label.config(text=q_data["question"])
        self.result_feedback_label.config(text="")
        if hasattr(self, 'game_explanation_label') and self.game_explanation_label.winfo_exists():
            self.game_explanation_label.config(text="")
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
            for btn in self.option_buttons: btn.config(state=tk.DISABLED)
            if selected_answer_text == correct_answer_text:
                self.current_score += 10
                self.result_feedback_label.config(text="Chính xác!", foreground="green")
                self.sound_manager.play_correct()
            else:
                self.result_feedback_label.config(text=f"Sai rồi! Đáp án đúng là: {correct_answer_text}", foreground="red")
                self.sound_manager.play_wrong()
            self.score_label.config(text=f"Điểm: {self.current_score}")
            self.next_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    db_initializer = DatabaseManager()
    app = QuizAppWithLeaderboard()
    app.mainloop()