import vgamepad as vg
import time
import signal
import sys

gamepad = None
running = True

def signal_handler(sig, frame):
    global running
    print("\n[信息] 收到退出信号，正在清理...")
    running = False
    if gamepad:
        gamepad.reset()
        gamepad.update()
    sys.exit(0)

def main():
    global gamepad, running

    signal.signal(signal.SIGINT, signal_handler)

    print("[信息] 正在创建虚拟 DS4 手柄...")
    gamepad = vg.VDS4Gamepad()

    # 激活设备
    gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
    gamepad.update()
    time.sleep(0.1)
    gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
    gamepad.update()
    time.sleep(0.1)
    # ===== 等待系统识别手柄 =====
    print("[信息] 等待系统识别虚拟手柄...")
    time.sleep(1.0)  # 1 秒稳定延迟
    print("[信息] 虚拟 DS4 手柄已就绪，开始执行 GTA 操作序列。")
    print("[信息] 按键映射: E→右方向键 | W→左摇杆前 | D→左摇杆右 | Enter→X")
    print("[提示] 按 Ctrl+C 可安全退出程序。")

    count = 0
    status_interval = 1  # 每轮都输出

    try:
        while running:
            # ===== 步骤 1: 按下并释放 E（右方向键） =====
            gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST)
            gamepad.update()
            time.sleep(0.053)

            gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
            gamepad.update()
            time.sleep(4.044)

            # ===== 步骤 2: 按下并释放 W（左摇杆前） =====
            gamepad.left_joystick(x_value=0x80, y_value=0x00)  # Y=0x00 为最前
            gamepad.update()
            time.sleep(4.702)

            gamepad.left_joystick(x_value=0x80, y_value=0x80)  # 归中
            gamepad.update()
            time.sleep(0.533)

            # ===== 步骤 3: 按下并释放 D（左摇杆右） =====
            gamepad.left_joystick(x_value=0xFF, y_value=0x80)  # X=0xFF 为最右
            gamepad.update()
            time.sleep(3.920)

            gamepad.left_joystick(x_value=0x80, y_value=0x80)  # 归中
            gamepad.update()
            time.sleep(0.144)

            # ===== 步骤 4: 按下并释放 Enter（X键） =====
            gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
            gamepad.update()
            time.sleep(0.066)

            gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
            gamepad.update()

            # ===== 一轮完成，计数并等待 =====
            count += 1
            print(f"[运行] 已执行 {count} 轮操作")

            # 等待 15 秒后开始下一轮
            time.sleep(15.000)

    except KeyboardInterrupt:
        pass
    finally:
        if gamepad:
            gamepad.reset()
            gamepad.update()
        print("[信息] 程序已安全退出。")

if __name__ == "__main__":
    main()