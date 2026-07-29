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

    print("[信息] 等待系统识别虚拟手柄...")
    time.sleep(1.0)

    print("[信息] 开始执行组合键序列...")
    print("[提示] 按 Ctrl+C 可中途退出。")

    try:
        # ----- 步骤1: OPTIONS + CROSS 组合 -----
        print("[操作] 按下 OPTIONS")
        gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS)
        gamepad.update()
        time.sleep(0.020)

        print("[操作] 按下 CROSS（组合保持）")
        gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        gamepad.update()
        time.sleep(0.050)

        print("[操作] 松开 CROSS")
        gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        gamepad.update()
        time.sleep(0.020)

        print("[操作] 松开 OPTIONS")
        gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS)
        gamepad.update()

        time.sleep(0.400)

        # ----- 步骤2: 右方向键 -----
        print("[操作] 按下右方向键")
        gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST)
        gamepad.update()
        time.sleep(0.050)

        print("[操作] 松开右方向键")
        gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
        gamepad.update()

        time.sleep(4.500)

        # ----- 步骤3: CROSS -----
        print("[操作] 按下 CROSS")
        gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        gamepad.update()
        time.sleep(0.050)

        print("[操作] 松开 CROSS")
        gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
        gamepad.update()

        time.sleep(0.350)

        # ----- 步骤4: 第一次 OPTIONS -----
        print("[操作] 按下 OPTIONS（第1次）")
        gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS)
        gamepad.update()
        time.sleep(0.055)

        print("[操作] 松开 OPTIONS（第1次）")
        gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS)
        gamepad.update()

        time.sleep(0.100)

        # ----- 步骤5: 第二次 OPTIONS -----
        print("[操作] 按下 OPTIONS（第2次）")
        gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS)
        gamepad.update()
        time.sleep(0.055)

        print("[操作] 松开 OPTIONS（第2次）")
        gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS)
        gamepad.update()

        print("[信息] 组合键序列执行完成。")

    except KeyboardInterrupt:
        pass
    finally:
        if gamepad:
            gamepad.reset()
            gamepad.update()
        print("[信息] 程序已安全退出。")

if __name__ == "__main__":
    main()