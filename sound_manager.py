### CODE BÀI 3: TOÀN BỘ FILE NÀY LÀ MỚI ###
# -------------------------------------------------------------------
# File: sound_manager.py
# Dự án: SNLT-HP8-B3-ProjectBasic
# -------------------------------------------------------------------

from playsound import playsound, PlaysoundException
import os
import sys
import threading

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối đến tài nguyên. """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SoundManager:
    def __init__(self):
        # Xây dựng đường dẫn đến các file âm thanh trong thư mục assets/sounds
        self.correct_sound_path = resource_path("assets/sounds/correct.mp3")
        self.wrong_sound_path = resource_path("assets/sounds/wrong.mp3")
        self.click_sound_path = resource_path("assets/sounds/click.mp3")
        
        # Tùy chọn: Kiểm tra sự tồn tại của file khi khởi tạo để debug
        self._check_files()

    def _check_files(self):
        """Kiểm tra xem các file âm thanh có tồn tại không và in cảnh báo nếu không."""
        if not os.path.exists(self.correct_sound_path):
            print(f"CẢNH BÁO: Không tìm thấy file âm thanh: {self.correct_sound_path}")
        if not os.path.exists(self.wrong_sound_path):
            print(f"CẢNH BÁO: Không tìm thấy file âm thanh: {self.wrong_sound_path}")
        if not os.path.exists(self.click_sound_path):
            print(f"CẢNH BÁO: Không tìm thấy file âm thanh: {self.click_sound_path}")

    def _play_sound_async(self, sound_path):
        """Phát âm thanh trong một thread riêng để không block GUI."""
        if not os.path.exists(sound_path):
            return # Không làm gì nếu file không tồn tại
        
        def target_play():
            try:
                playsound(sound_path)
            except Exception as e:
                print(f"Lỗi khi phát âm thanh '{os.path.basename(sound_path)}': {e}")

        # daemon=True để thread tự động kết thúc khi chương trình chính thoát
        sound_thread = threading.Thread(target=target_play, daemon=True)
        sound_thread.start()

    def play_correct(self):
        """Phát âm thanh khi trả lời đúng."""
        self._play_sound_async(self.correct_sound_path)

    def play_wrong(self):
        """Phát âm thanh khi trả lời sai."""
        self._play_sound_async(self.wrong_sound_path)

    def play_click(self):
        """Phát âm thanh khi nhấn nút."""
        self._play_sound_async(self.click_sound_path)

### KẾT THÚC CODE BÀI 3 ###