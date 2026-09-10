import sys
import json
import os
import ctypes
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QImage
import vgamepad as vg
from pynput import keyboard
from PIL import Image


# ==================== 图标加载 ====================
def load_icon_with_pillow(filepath):
    if not os.path.exists(filepath):
        print(f"❌ 图标文件不存在: {filepath}")
        return QIcon()
    try:
        img = Image.open(filepath)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        icon = QIcon()
        sizes = [16, 24, 32, 48, 64, 128, 256]
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            data = resized.tobytes("raw", "BGRA")
            qimage = QImage(data, size, size, QImage.Format.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            if not pixmap.isNull():
                icon.addPixmap(pixmap)
        print(f"✅ 图标加载成功（Pillow），共生成 {len(sizes)} 个尺寸")
        return icon
    except Exception as e:
        print(f"❌ Pillow 加载失败: {e}")
        return QIcon()


def get_icon_path():
    icon_filename = "running-512.ico"
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        path = os.path.join(exe_dir, icon_filename)
        if os.path.exists(path):
            return path
        if hasattr(sys, '_MEIPASS'):
            path = os.path.join(sys._MEIPASS, icon_filename)
            if os.path.exists(path):
                return path
        return path
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_filename)


# ==================== 主窗口 ====================
class RunnerApp(QMainWindow):
    press_signal = pyqtSignal()
    release_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("虚拟手柄空手偷速跑")
        self.setFixedSize(380, 220)

        self.is_enabled = False
        self.is_triggering = False
        self.hotkey = "Shift"  # 默认热键改为 Shift
        self.trigger_mode = "toggle"
        self._is_key_down = False

        self.ds4 = None
        self.listener = None
        self._is_listener_running = False

        self.init_controller()
        self.load_config()
        self.init_ui()
        self.register_hotkey()

        self.press_signal.connect(self.on_key_press_ui)
        self.release_signal.connect(self.on_key_release_ui)

    def init_controller(self):
        try:
            self.ds4 = vg.VDS4Gamepad()
            self.ds4.update()
            print("✅ DS4 虚拟手柄已创建")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法创建 DS4 手柄: {e}\n请确保 ViGEm 驱动已安装。")
            sys.exit(1)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.enable_check = QCheckBox("启用自动前推摇杆")
        self.enable_check.toggled.connect(self.on_enable_toggled)
        layout.addWidget(self.enable_check)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("切换热键:"))
        self.hotkey_combo = QComboBox()
        self.hotkey_combo.setToolTip("选择 Shift、` (反引号键) 或 F1~F12 作为切换热键")

        # 修改点：将 ~ 改为 `
        self.hotkey_combo.addItem("Shift")
        self.hotkey_combo.addItem("`")
        for i in range(1, 13):
            self.hotkey_combo.addItem(f"F{i}")

        self.hotkey_combo.setCurrentText(self.hotkey)
        self.hotkey_combo.currentTextChanged.connect(self.on_hotkey_changed)
        h_layout.addWidget(self.hotkey_combo)
        layout.addLayout(h_layout)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("触发方式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("切换模式 (按一下开/关)")
        self.mode_combo.addItem("按住模式 (按住触发)")
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)

        self.status_label = QLabel("状态: 摇杆回中 (0%)")
        layout.addWidget(self.status_label)

        self.info_label = QLabel("按热键切换摇杆前推/回中")
        layout.addWidget(self.info_label)

    # ---------- 热键管理 ----------
    def get_pynput_key_obj(self, display_name: str):
        if display_name == "Shift":
            return keyboard.Key.shift
        elif display_name == "`":
            # 修改点：匹配不按Shift的纯反引号按键
            return keyboard.KeyCode.from_char('`')
        elif display_name.upper().startswith("F") and display_name[1:].isdigit():
            return getattr(keyboard.Key, display_name.lower())
        return None

    def register_hotkey(self):
        self.stop_listener()
        self.target_key = self.get_pynput_key_obj(self.hotkey)
        self._is_key_down = False

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self.listener.start()
            self._is_listener_running = True
            print(f"✅ 热键注册成功: {self.hotkey}")
            self.status_label.setText(f"热键: {self.hotkey}")
        except Exception as e:
            QMessageBox.critical(self, "热键注册失败", f"无法注册热键 {self.hotkey}:\n{e}")
            self._is_listener_running = False

    def _on_key_press(self, key):
        if key == self.target_key and not self._is_key_down:
            self._is_key_down = True
            self.press_signal.emit()

    def _on_key_release(self, key):
        if key == self.target_key and self._is_key_down:
            self._is_key_down = False
            self.release_signal.emit()

    def stop_listener(self):
        if self.listener and self._is_listener_running:
            try:
                self.listener.stop()
                self._is_listener_running = False
                print("⏹ 热键监听已停止")
            except:
                pass
        self.listener = None

    def on_hotkey_changed(self, text):
        self.hotkey = text.strip()
        self.register_hotkey()
        self.save_config()

    def on_mode_changed(self, text):
        if "按住模式" in text:
            self.trigger_mode = "hold"
        else:
            self.trigger_mode = "toggle"
        self._is_key_down = False
        if self.is_triggering:
            self.stop_trigger()
        self.save_config()

    def on_key_press_ui(self):
        if not self.is_enabled:
            return
        if self.trigger_mode == "toggle":
            self.toggle_trigger()
        elif self.trigger_mode == "hold":
            self.start_trigger()

    def on_key_release_ui(self):
        if not self.is_enabled:
            return
        if self.trigger_mode == "hold":
            self.stop_trigger()

    def toggle_trigger(self):
        if self.is_triggering:
            self.stop_trigger()
        else:
            self.start_trigger()

    def start_trigger(self):
        if not self.ds4:
            return
        try:
            self.is_triggering = True
            self.ds4.left_joystick_float(0.0, -0.88)
            self.ds4.update()
            self.status_label.setText("状态: 摇杆前推 88% (跑步中)")
            print("🏃 摇杆前推 88%")
        except Exception as e:
            print(f"启动异常: {e}")

    def stop_trigger(self):
        if not self.ds4:
            return
        try:
            self.is_triggering = False
            self.ds4.left_joystick_float(0.0, 0.0)
            self.ds4.update()
            self.status_label.setText("状态: 摇杆回中 (停止)")
            print("⏹ 摇杆回中")
        except Exception as e:
            print(f"停止异常: {e}")

    def on_enable_toggled(self, checked):
        self.is_enabled = checked
        if not checked and self.is_triggering:
            self.stop_trigger()
        self.save_config()

    # ---------- 配置持久化 ----------
    def save_config(self):
        data = {
            "hotkey": self.hotkey,
            "enabled": self.is_enabled,
            "trigger_mode": self.trigger_mode
        }
        try:
            with open("config.json", "w") as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def load_config(self):
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r") as f:
                    data = json.load(f)
                    loaded_hotkey = data.get("hotkey", "Shift")

                    # 兼容旧配置：如果之前存的是 ~，自动替换为 `
                    if loaded_hotkey == "~":
                        loaded_hotkey = "`"

                    if loaded_hotkey not in ["Shift", "`"] + [f"F{i}" for i in range(1, 13)]:
                        loaded_hotkey = "Shift"
                    self.hotkey = loaded_hotkey
                    self.is_enabled = data.get("enabled", False)
                    self.trigger_mode = data.get("trigger_mode", "toggle")
                    if self.trigger_mode not in ["toggle", "hold"]:
                        self.trigger_mode = "toggle"
            except:
                pass

    # ---------- 退出清理 ----------
    def closeEvent(self, event):
        self.stop_listener()
        if self.ds4:
            self.stop_trigger()
            self.ds4 = None
        event.accept()


# ==================== 程序入口 ====================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "GordoFakeController.AutoRun.88"
            )
        except Exception as e:
            print(f"⚠️ 设置 AppUserModelID 失败: {e}")

    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        icon = load_icon_with_pillow(icon_path)
        if not icon.isNull():
            app.setWindowIcon(icon)

    window = RunnerApp()
    window.hotkey_combo.setCurrentText(window.hotkey)
    window.mode_combo.setCurrentIndex(0 if window.trigger_mode == "toggle" else 1)
    window.enable_check.setChecked(window.is_enabled)
    window.show()
    sys.exit(app.exec())