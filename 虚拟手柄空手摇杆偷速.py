import sys
import json
import os
import ctypes
from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap, QImage
import vgamepad as vg
from pynput import keyboard
from PIL import Image  # 需要安装 Pillow


# ==================== 图标加载（使用 Pillow 保证成功率） ====================
def load_icon_with_pillow(filepath):
    """
    使用 Pillow 读取 ICO/PNG，生成多尺寸图标，确保 Windows 任何位置都能显示。
    """
    if not os.path.exists(filepath):
        print(f"❌ 图标文件不存在: {filepath}")
        return QIcon()

    try:
        img = Image.open(filepath)
        # 转换为 RGBA（支持透明）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        icon = QIcon()
        # 生成多个常用尺寸（Windows 需要小尺寸）
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
    """获取图标路径，兼容开发环境和打包"""
    icon_filename = "running-512.ico"
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # 先找 exe 同目录
        path = os.path.join(exe_dir, icon_filename)
        if os.path.exists(path):
            return path
        # 再找临时解压目录
        if hasattr(sys, '_MEIPASS'):
            path = os.path.join(sys._MEIPASS, icon_filename)
            if os.path.exists(path):
                return path
        return path
    else:
        # 开发环境：当前脚本所在目录
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_filename)


# ==================== 主窗口 ====================
class RunnerApp(QMainWindow):
    hotkey_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("虚拟手柄空手偷速跑")
        self.setFixedSize(350, 200)

        # ---------- 窗口不再单独设置图标，由全局图标统一 ----------
        # 注意：Qt 的窗口会继承全局图标，所以无需重复设置

        self.is_enabled = False
        self.is_triggering = False
        self.hotkey = "F1"
        self.ds4 = None
        self.listener = None
        self._is_listener_running = False

        self.init_controller()
        self.load_config()
        self.init_ui()
        self.register_hotkey()
        self.hotkey_signal.connect(self.on_hotkey_triggered)

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
        self.hotkey_combo.setToolTip("选择 F1 ~ F10 作为切换热键")
        for i in range(1, 11):
            self.hotkey_combo.addItem(f"F{i}")
        self.hotkey_combo.setCurrentText(self.hotkey)
        self.hotkey_combo.currentTextChanged.connect(self.on_hotkey_changed)
        h_layout.addWidget(self.hotkey_combo)
        layout.addLayout(h_layout)

        self.status_label = QLabel("状态: 摇杆回中 (0%)")
        layout.addWidget(self.status_label)

        self.info_label = QLabel("按热键切换摇杆前推/回中")
        layout.addWidget(self.info_label)

    # ---------- 热键管理 ----------
    def get_pynput_hotkey(self, display_name: str) -> str:
        if display_name.upper().startswith("F") and display_name[1:].isdigit():
            return f"<{display_name.lower()}>"
        return display_name.lower()

    def register_hotkey(self):
        self.stop_listener()
        hotkey_str = self.get_pynput_hotkey(self.hotkey)
        try:
            self.listener = keyboard.GlobalHotKeys({
                hotkey_str: self._hotkey_callback
            })
            self.listener.start()
            self._is_listener_running = True
            print(f"✅ 热键注册成功: {self.hotkey} -> {hotkey_str}")
            self.status_label.setText(f"热键: {self.hotkey}")
        except Exception as e:
            QMessageBox.critical(self, "热键注册失败", f"无法注册热键 {self.hotkey}:\n{e}")
            self._is_listener_running = False

    def stop_listener(self):
        if self.listener and self._is_listener_running:
            try:
                self.listener.stop()
                self._is_listener_running = False
                print("⏹ 热键监听已停止")
            except:
                pass
        self.listener = None

    def _hotkey_callback(self):
        self.hotkey_signal.emit()

    def on_hotkey_triggered(self):
        self.toggle_trigger()

    def on_hotkey_changed(self, text):
        self.hotkey = text.strip()
        self.register_hotkey()
        self.save_config()

    # ---------- 核心功能 ----------
    def toggle_trigger(self):
        if not self.is_enabled:
            return
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
        data = {"hotkey": self.hotkey, "enabled": self.is_enabled}
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
                    self.hotkey = data.get("hotkey", "F1")
                    self.is_enabled = data.get("enabled", False)
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
    # 可选：强制管理员权限（如需启用，取消注释）
    # if not ctypes.windll.shell32.IsUserAnAdmin():
    #     ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    #     sys.exit(0)

    app = QApplication(sys.argv)

    # ---------- 设置 Windows 任务栏标识（确保任务栏图标关联） ----------
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "GordoFakeController.AutoRun.88"
            )
            print("✅ AppUserModelID 已设置")
        except Exception as e:
            print(f"⚠️ 设置 AppUserModelID 失败: {e}")

    # ---------- 加载并设置全局图标 ----------
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        icon = load_icon_with_pillow(icon_path)
        if not icon.isNull():
            app.setWindowIcon(icon)
            print("✅ 全局图标已设置")
        else:
            print("⚠️ 图标加载失败，窗口将没有图标")
    else:
        print(f"⚠️ 图标文件未找到: {icon_path}")

    window = RunnerApp()
    # 同步配置
    window.hotkey_combo.setCurrentText(window.hotkey)
    window.enable_check.setChecked(window.is_enabled)
    window.show()
    sys.exit(app.exec())