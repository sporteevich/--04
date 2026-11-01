"""Скриншоты реальных состояний приложения autorize.py."""
import ctypes
import os
import time

from ctypes import wintypes
from PIL import ImageGrab

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")
os.makedirs(SHOTS, exist_ok=True)

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def grab(hwnd, name, screen=False):
    if screen:
        left, top, right, bottom = rect(hwnd)
        img = ImageGrab.grab(bbox=(left, top, right, bottom))
    else:
        try:
            img = ImageGrab.grab(window=hwnd)   # PrintWindow: не зависит от перекрытий
        except Exception:
            left, top, right, bottom = rect(hwnd)
            img = ImageGrab.grab(bbox=(left, top, right, bottom))
    img.save(os.path.join(SHOTS, name))
    print(f"SHOT {name} {img.width}x{img.height}")


def outer_app_window(title="Авторизация"):
    """Внешнее окно (с заголовком и рамкой) — для скриншота целиком."""
    found = []

    def cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        if buf.value == title and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found[0] if found else None


def grab_main(name):
    hwnd = outer_app_window()
    if not hwnd:
        print("NO MAIN WINDOW")
        return
    grab(hwnd, name, screen=True)


def dialogs():
    found = []

    def cb(hwnd, _):
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        if cls.value == "#32770" and user32.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == os.getpid():
                found.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


def load_app():
    src = open(os.path.join(HERE, "autorize.py"), encoding="utf-8").read()
    src = src.replace("root.mainloop()", "pass  # mainloop убран драйвером")
    ns = {"__name__": "autorize"}
    exec(compile(src, "autorize.py", "exec"), ns)
    ns["root"].update()
    time.sleep(1.0)
    ns["root"].update()
    return ns


def step_with_dialog(ns, name, action):
    """Выполняет action; если открылся messagebox — снимает его и закрывает."""
    root = ns["root"]

    def job():
        hwnds = dialogs()
        if hwnds:
            grab(hwnds[0], name, screen=True)
            user32.PostMessageW(hwnds[0], 0x0010, 0, 0)  # WM_CLOSE
        else:
            print(f"NO DIALOG for {name}")

    root.after(600, job)
    action()
    try:
        root.update()
    except Exception:
        pass
    field = ""
    try:
        field = ns["entry_password"].get()
    except Exception:
        field = "<окно закрыто>"
    print(f"   attempts_left={ns['attempts_left']}  password_field={field!r}")


def main():
    ns = load_app()
    root = ns["root"]
    login_in, pass_in = ns["entry_login"], ns["entry_password"]
    check_show, show_var = ns["check_show"], ns["show_password_var"]

    grab_main("01_main.png")

    # 1. Ввод данных + включение чекбокса "Показать пароль"
    login_in.insert(0, "admin")
    pass_in.insert(0, "1234")
    check_show.invoke()                 # нажатие на чекбокс
    root.update()
    print("show after invoke:", repr(pass_in.cget("show")))
    grab_main("02_show_password.png")

    # 2. Чекбокс обратно, вход по кнопке -> успех
    check_show.invoke()
    root.update()
    print("show after 2nd invoke:", repr(pass_in.cget("show")))
    grab_main("03_filled.png")
    step_with_dialog(ns, "04_success.png", ns["btn_login"].invoke)

    # 3. Неверный пароль -> ошибка с остатком попыток
    pass_in.insert(0, "wrong")
    step_with_dialog(ns, "05_error.png", ns["btn_login"].invoke)

    # 4. Ещё одна ошибка (попыток осталось 1)
    pass_in.insert(0, "wrong")
    root.after(600, lambda: user32.PostMessageW(dialogs()[0], 0x0010, 0, 0) if dialogs() else None)
    ns["btn_login"].invoke()
    root.update()
    print("   attempts_left after 2nd error:", ns["attempts_left"])

    # 5. Третья ошибка -> блокировка и закрытие приложения
    pass_in.insert(0, "wrong2")
    step_with_dialog(ns, "06_lockout.png", ns["btn_login"].invoke)

    try:
        alive = bool(root.winfo_exists())
    except Exception:
        alive = False
    print("окно существует после блокировки:", alive)
    print("DRIVER OK")


if __name__ == "__main__":
    main()
