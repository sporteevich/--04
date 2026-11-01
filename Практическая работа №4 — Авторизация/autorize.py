# ИМПОРТ БИБЛИОТЕК
import tkinter as tk                    # Основная библиотека для GUI
from tkinter import messagebox          # Модуль для всплывающих окон
import hashlib                          # Для хеширования паролей

# "БАЗА ДАННЫХ" ПОЛЬЗОВАТЕЛЕЙ

# здесь будет PostgreSQL (потом)
# Пароли храним в виде SHA-256 хеша — так безопаснее.
def hash_password(password: str) -> str:
    """Превращает пароль в хеш SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# Словарь: логин -> хеш пароля
# Пароли для демонстрации: admin/1234, user/qwerty
USERS = {
    "admin": hash_password("1234"),
    "user": hash_password("qwerty"),
}

# Счётчик оставшихся попыток входа
MAX_ATTEMPTS = 3
attempts_left = MAX_ATTEMPTS

# ФУНКЦИИ ЛОГИКИ

def toggle_password_visibility():
    """Показывает/скрывает пароль по нажатию на чекбокс."""
    if show_password_var.get():
        # Если галочка стоит — показываем символы
        entry_password.config(show="")
    else:
        # Иначе — маскируем звёздочками
        entry_password.config(show="*")


def check_login(event=None):
    """
    Проверяет введённые логин и пароль.
    event=None нужен, чтобы функцию можно было вызывать
    и по кнопке, и по нажатию Enter.
    """
    global attempts_left  # Изменяем глобальную переменную

    # --- 1. Получаем данные из полей ---
    login = entry_login.get().strip()          # .strip() убирает пробелы по краям
    password = entry_password.get()

    # --- 2. Проверка на пустые поля ---
    if not login or not password:
        messagebox.showwarning("Внимание", "Заполните все поля!")
        return  # Выходим из функции, ничего дальше не делаем

    # --- 3. Проверка логина и пароля ---
    # Хешируем введённый пароль и сравниваем с тем, что в "базе"
    password_hash = hash_password(password)

    if login in USERS and USERS[login] == password_hash:
        # ✅ Успешный вход
        messagebox.showinfo("Успех", f"Добро пожаловать, {login}!")
        # Здесь обычно открывают главное окно приложения:
        # root.destroy()
        # open_main_window()
    else:
        # ❌ Неверные данные
        attempts_left -= 1  # Уменьшаем счётчик попыток

        if attempts_left > 0:
            messagebox.showerror(
                "Ошибка",
                f"Неверный логин или пароль.\n"
                f"Осталось попыток: {attempts_left}"
            )
        else:
            messagebox.showerror(
                "Блокировка",
                "Превышено число попыток. Приложение будет закрыто."
            )
            root.destroy()  # Закрываем окно
            return

        # Очищаем поле пароля и ставим туда курсор
        entry_password.delete(0, tk.END)
        entry_password.focus()


# СОЗДАНИЕ ГЛАВНОГО ОКНА

root = tk.Tk()                             # Создаём окно
root.title("Авторизация")                  # Заголовок окна
root.geometry("360x320")                   # Размер: ширина x высота
root.resizable(False, False)               # Запрещаем менять размер

# ЗАГОЛОВОК

label_title = tk.Label(
    root,
    text="Вход в систему",
    font=("Arial", 16, "bold")            # Шрифт: Arial 16, жирный
)
label_title.pack(pady=15)                  # pady — отступ сверху и снизу

# ПОЛЕ "ЛОГИН"

label_login = tk.Label(root, text="Логин:")
label_login.pack(anchor="w", padx=40)      # anchor="w" — прижат влево

entry_login = tk.Entry(root, width=30)     # Поле ввода шириной 30 символов
entry_login.pack(padx=40, pady=5)
entry_login.focus()                        # Курсор сразу в этом поле

# ПОЛЕ "ПАРОЛЬ"

label_password = tk.Label(root, text="Пароль:")
label_password.pack(anchor="w", padx=40)

entry_password = tk.Entry(
    root,
    width=30,
    show="*"                              # Скрываем символы звёздочками
)
entry_password.pack(padx=40, pady=5)

# ЧЕКБОКС "ПОКАЗАТЬ ПАРОЛЬ"

show_password_var = tk.BooleanVar(value=False)   # Переменная для галочки

check_show = tk.Checkbutton(
    root,
    text="Показать пароль",
    variable=show_password_var,
    command=toggle_password_visibility       # Вызов при клике
)
check_show.pack(anchor="w", padx=40)

# КНОПКА "ВОЙТИ"

btn_login = tk.Button(
    root,
    text="Войти",
    width=15,
    command=check_login,                     # Функция, вызываемая при клике
    bg="#4CAF50",                            # Цвет фона (зелёный)
    fg="white",                              # Цвет текста
    activebackground="#45a049",              # Цвет при нажатии
    cursor="hand2"                           # Курсор-рука при наведении
)
btn_login.pack(pady=20)

# ПРИВЯЗКА КЛАВИШИ ENTER

# Нажатие Enter в любом месте окна = нажатие кнопки "Войти"
root.bind("<Return>", check_login)

# ЗАПУСК ГЛАВНОГО ЦИКЛА ПРИЛОЖЕНИЯ

# mainloop() держит окно открытым и обрабатывает события
# (клики, нажатия клавиш и т. д.)
root.mainloop()
