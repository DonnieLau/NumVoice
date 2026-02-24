import pygame
import keyboard
import threading
import time
import os
import sys
import pystray
from PIL import Image
import winreg as reg

MIN_INTERVAL = 0.12  # 播报间隔（100~150ms 体验最好）
SOUND_DIR = "sounds"
ICON_PATH = "icon.ico"


# 资源路径处理
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# 初始化音频
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
sounds = {}
for i in range(10):
    sounds[str(i)] = pygame.mixer.Sound(resource_path(os.path.join("sounds", f"{i}.wav")))

# 播放状态
last_play_time = 0.0
pending_digit = None
lock = threading.Lock()


# 播放线程（节奏采样）
def player_loop():
    global last_play_time, pending_digit

    while True:
        time.sleep(0.005)
        with lock:
            if pending_digit is None:
                continue
            now = time.monotonic()
            if now - last_play_time < MIN_INTERVAL:
                continue
            digit = pending_digit
            pending_digit = None
            last_play_time = now

        sounds[digit].play()


# 键盘监听
def on_key_event(event):
    global pending_digit

    if event.event_type != "down":
        return
    if not event.name.isdigit():
        return
    # 永远只保留最新输入
    with lock:
        pending_digit = event.name


# 系统托盘
def quit_app(icon, item):
    icon.stop()
    os._exit(0)


def tray_icon():
    image = Image.open(resource_path(ICON_PATH))
    menu = pystray.Menu(pystray.MenuItem("退出", quit_app))
    icon = pystray.Icon("digit_speaker", image, "数字播报", menu)
    icon.run()

def add_to_startup():
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_WRITE)
    reg.SetValueEx(reg_key, "MyApp", 0, reg.REG_SZ, sys.executable)
    reg.CloseKey(reg_key)

# 启动
threading.Thread(target=player_loop, daemon=True).start()
threading.Thread(target=tray_icon, daemon=True).start()
add_to_startup()
keyboard.hook(on_key_event)
keyboard.wait()
