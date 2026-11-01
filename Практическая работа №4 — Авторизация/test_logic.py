"""Автотест логики autorize.py: проверяет все ветки check_login без показа окон."""
import hashlib
import os
import sys

import tkinter as tk

HERE = os.path.dirname(os.path.abspath(__file__))


def load_app():
    src = open(os.path.join(HERE, "autorize.py"), encoding="utf-8").read()
    src = src.replace("root.mainloop()", "pass  # mainloop убран тестом")
    ns = {"__name__": "autorize"}
    exec(compile(src, "autorize.py", "exec"), ns)
    return ns


class MsgRecorder:
    def __init__(self):
        self.calls = []

    def _make(self, kind):
        def rec(title, message, **kw):
            self.calls.append((kind, title, message))
        return rec

    def patch(self, messagebox):
        messagebox.showinfo = self._make("info")
        messagebox.showwarning = self._make("warning")
        messagebox.showerror = self._make("error")

    def last(self):
        return self.calls[-1] if self.calls else None

    def clear(self):
        self.calls.clear()


results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS  " if cond else "FAIL  ") + name + ("  | " + str(extra) if extra else ""))


def main():
    ns = load_app()
    root = ns["root"]
    login_in, pass_in = ns["entry_login"], ns["entry_password"]
    check_show, show_var = ns["check_show"], ns["show_password_var"]
    rec = MsgRecorder()
    rec.patch(ns["messagebox"])
    check_login = ns["check_login"]

    # 1. Хеширование
    h = ns["hash_password"]("1234")
    check("hash_password: SHA-256, 64 hex-символа", len(h) == 64 and all(c in "0123456789abcdef" for c in h), h)
    check("hash_password совпадает с hashlib", h == hashlib.sha256(b"1234").hexdigest())
    check("в USERS хранятся хеши, а не пароли",
          ns["USERS"] == {"admin": h, "user": ns["hash_password"]("qwerty")}
          and "1234" not in str(ns["USERS"]))
    check("MAX_ATTEMPTS = 3, счётчик сброшен", ns["MAX_ATTEMPTS"] == 3 and ns["attempts_left"] == 3)

    # 2. Чекбокс "Показать пароль"
    check("пароль изначально скрыт", pass_in.cget("show") == "*")
    check_show.invoke()
    check("чекбокс включён -> пароль виден", pass_in.cget("show") == "")
    check_show.invoke()
    check("чекбокс выключен -> пароль снова скрыт", pass_in.cget("show") == "*")

    # 3. Пустые поля
    rec.clear()
    check_login()
    kind, title, msg = rec.last() or (None, None, None)
    check("пустые поля -> предупреждение", kind == "warning" and title == "Внимание" and msg == "Заполните все поля!",
          f"{kind}:{title}:{msg}")
    check("пустые поля не тратят попытку", ns["attempts_left"] == 3)

    # 4. Верный вход admin/1234
    rec.clear()
    login_in.insert(0, "admin")
    pass_in.insert(0, "1234")
    check_login()
    kind, title, msg = rec.last() or (None, None, None)
    check("admin/1234 -> успех", kind == "info" and title == "Успех" and "admin" in msg, f"{kind}:{msg}")
    check("успешный вход не тратит попытку", ns["attempts_left"] == 3)

    # 5. Второй пользователь + пробелы по краям логина
    rec.clear()
    login_in.delete(0, "end")
    pass_in.delete(0, "end")
    login_in.insert(0, "  user  ")
    pass_in.insert(0, "qwerty")
    check_login()
    kind, title, msg = rec.last() or (None, None, None)
    check("' user ' / qwerty -> успех (strip работает)", kind == "info" and "user" in msg, f"{kind}:{msg}")

    # 6. Неверный пароль
    rec.clear()
    login_in.delete(0, "end")
    pass_in.delete(0, "end")
    login_in.insert(0, "admin")
    pass_in.insert(0, "wrong")
    check_login()
    kind, title, msg = rec.last() or (None, None, None)
    check("неверный пароль -> ошибка", kind == "error" and title == "Ошибка", f"{kind}:{msg}")
    check("в сообщении остаток попыток 2", "Осталось попыток: 2" in (msg or ""), msg)
    check("счётчик уменьшился до 2", ns["attempts_left"] == 2)
    check("поле пароля очищено", pass_in.get() == "")

    # 7. Неизвестный логин
    rec.clear()
    login_in.delete(0, "end")
    login_in.insert(0, "nobody")
    pass_in.insert(0, "1234")
    check_login()
    kind, title, msg = rec.last() or (None, None, None)
    check("неизвестный логин -> ошибка, остаток 1", kind == "error" and "Осталось попыток: 1" in (msg or ""), msg)
    check("счётчик уменьшился до 1", ns["attempts_left"] == 1)

    # 8. Блокировка
    real_destroy = root.destroy
    destroyed = {"flag": False}
    root.destroy = lambda: destroyed.__setitem__("flag", True)
    rec.clear()
    pass_in.delete(0, "end")
    pass_in.insert(0, "wrong")
    check_login()
    kind, title, msg = rec.last() or (None, None, None)
    check("3-я ошибка -> диалог 'Блокировка'", kind == "error" and title == "Блокировка", f"{kind}:{title}")
    check("приложение закрывается (root.destroy)", destroyed["flag"] is True)
    check("счётчик исчерпан", ns["attempts_left"] == 0)

    root.destroy = real_destroy
    try:
        real_destroy()
    except tk.TclError:
        pass

    ok = sum(1 for _, r in results if r)
    print(f"\nИТОГО: {ok}/{len(results)} проверок пройдено")
    sys.exit(0 if ok == len(results) else 1)


if __name__ == "__main__":
    main()
