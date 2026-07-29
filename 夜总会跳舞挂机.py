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

    print("[信息] 虚拟 DS4 手柄已就绪，开始自动点击 X 键。")
    print("[提示] 按 Ctrl+C 可安全退出程序。")

    count = 0
    status_interval = 10

    try:
        while running:
            # ---- 按下 X 并保持 0.3 秒 ----
            gamepad.press_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
            gamepad.update()
            time.sleep(0.3)                     # 按下保持 300ms

            # ---- 释放 X ----
            gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_CROSS)
            gamepad.update()

            count += 1

            if count % status_interval == 0:
                print(f"[运行] 已发送 {count} 次按键")

            # ---- 等待剩余时间（总共 480ms 减去已过的 300ms） ----
            time.sleep(0.18)                    # 释放后等待 180ms

    except KeyboardInterrupt:
        pass
    finally:
        if gamepad:
            gamepad.reset()
            gamepad.update()
        print("[信息] 程序已安全退出。")

if __name__ == "__main__":
    main()