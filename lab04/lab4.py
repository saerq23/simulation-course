import tkinter as tk
from tkinter import messagebox, ttk
import random

# Базовый датчик (LCG)
class LCG:
    """Линейный конгруэнтный генератор."""
    def __init__(self, a, c, m, seed):
        self.a = a
        self.c = c
        self.m = m
        self.state = seed

    def next(self):
        """Возвращает следующее псевдослучайное целое число в [0, m-1]."""
        self.state = (self.a * self.state + self.c) % self.m
        return self.state

    def random(self):
        """Возвращает псевдослучайное число в [0, 1)."""
        return self.next() / self.m

# Ручное вычисление статистик
def mean(data):
    return sum(data) / len(data)

def variance_population(data):
    avg = mean(data)
    return sum((x - avg) ** 2 for x in data) / len(data)

def variance_sample(data):
    avg = mean(data)
    return sum((x - avg) ** 2 for x in data) / (len(data) - 1)

def compute_statistics(sample):
    """Возвращает (выборочное среднее, генеральную дисперсию, выборочную дисперсию)."""
    avg = mean(sample)
    var_pop = variance_population(sample)
    var_sample = variance_sample(sample)
    return avg, var_pop, var_sample

# Теоретические значения для равномерного распределения [0,1)
THEORETICAL_MEAN = 0.5
THEORETICAL_VARIANCE = 1 / 12  # ≈ 0.08333333333333333

def format_number(x):
    """Форматирует число для отображения."""
    return f"{x:.8f}"

def generate():
    """Обработчик кнопки генерации."""
    # Считываем параметры
    try:
        n = int(entry_n.get())
        if n <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Размер выборки должен быть положительным целым числом.")
        return

    try:
        seed = int(entry_seed.get()) if entry_seed.get().strip() else 42
    except ValueError:
        messagebox.showerror("Ошибка", "Seed должен быть целым числом.")
        return

    try:
        a = int(entry_a.get())
        c = int(entry_c.get())
        m = int(entry_m.get())
        if m <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Параметры LCG (a, c, m) должны быть целыми числами, m > 0.")
        return

    # Генерация выборки с помощью LCG
    lcg = LCG(a, c, m, seed)
    sample_lcg = [lcg.random() for _ in range(n)]

    # Генерация выборки с помощью встроенного генератора(воспроизводимость)
    random.seed(seed)
    sample_builtin = [random.random() for _ in range(n)]

    # Вычисление статистик
    mean_lcg, var_pop_lcg, var_sample_lcg = compute_statistics(sample_lcg)
    mean_builtin, var_pop_builtin, var_sample_builtin = compute_statistics(sample_builtin)

    # Вывод в текстовые поля
    # LCG
    var_mean_lcg_var.set(f"{format_number(mean_lcg)} / {format_number(var_pop_lcg)} / {format_number(var_sample_lcg)}")
    # Встроенный
    var_mean_builtin_var.set(f"{format_number(mean_builtin)} / {format_number(var_pop_builtin)} / {format_number(var_sample_builtin)}")
    # Теоретические
    var_theoretical.set(f"{format_number(THEORETICAL_MEAN)} / {format_number(THEORETICAL_VARIANCE)}")

    # Дополнительно можно показать разницу
    diff_mean_lcg = abs(mean_lcg - THEORETICAL_MEAN)
    diff_var_lcg = abs(var_pop_lcg - THEORETICAL_VARIANCE)
    diff_mean_builtin = abs(mean_builtin - THEORETICAL_MEAN)
    diff_var_builtin = abs(var_pop_builtin - THEORETICAL_VARIANCE)

    var_diff_lcg.set(f"{format_number(diff_mean_lcg)} / {format_number(diff_var_lcg)}")
    var_diff_builtin.set(f"{format_number(diff_mean_builtin)} / {format_number(diff_var_builtin)}")

# Создание главного окна
root = tk.Tk()
root.title("Сравнение генераторов случайных чисел")
root.geometry("1000x500")
root.resizable(True, True)

# Стиль
style = ttk.Style()
style.configure("TLabel", font=("Arial", 10))
style.configure("TButton", font=("Arial", 10))
style.configure("TEntry", font=("Arial", 10))

# Основные рамки
frame_inputs = ttk.LabelFrame(root, text="Параметры генерации", padding=(10, 5))
frame_inputs.pack(fill="x", padx=10, pady=5)

frame_lcg_params = ttk.LabelFrame(root, text="Параметры LCG (базового датчика)", padding=(10, 5))
frame_lcg_params.pack(fill="x", padx=10, pady=5)

frame_results = ttk.LabelFrame(root, text="Результаты (среднее / генеральная дисперсия / выборочная дисперсия)", padding=(10, 5))
frame_results.pack(fill="both", expand=True, padx=10, pady=5)

frame_results.columnconfigure(0, weight=1)   # название генератора
frame_results.columnconfigure(1, weight=2)   # значения
frame_results.columnconfigure(2, weight=2)   # отклонения

# Поля ввода общих параметров
row = 0
ttk.Label(frame_inputs, text="Размер выборки (n):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
entry_n = ttk.Entry(frame_inputs, width=15)
entry_n.grid(row=row, column=1, sticky="w", padx=5, pady=2)
entry_n.insert(0, "100000")
row += 1

ttk.Label(frame_inputs, text="Seed (общий):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
entry_seed = ttk.Entry(frame_inputs, width=15)
entry_seed.grid(row=row, column=1, sticky="w", padx=5, pady=2)
entry_seed.insert(0, "42")
row += 1

# Поля ввода параметров LCG
row = 0
ttk.Label(frame_lcg_params, text="a (множитель):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
entry_a = ttk.Entry(frame_lcg_params, width=15)
entry_a.grid(row=row, column=1, sticky="w", padx=5, pady=2)
entry_a.insert(0, "1664525")
row += 1

ttk.Label(frame_lcg_params, text="c (приращение):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
entry_c = ttk.Entry(frame_lcg_params, width=15)
entry_c.grid(row=row, column=1, sticky="w", padx=5, pady=2)
entry_c.insert(0, "1013904223")
row += 1

ttk.Label(frame_lcg_params, text="m (модуль):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
entry_m = ttk.Entry(frame_lcg_params, width=15)
entry_m.grid(row=row, column=1, sticky="w", padx=5, pady=2)
entry_m.insert(0, "4294967296")  # 2^32
row += 1

# Кнопка генерации
btn_generate = ttk.Button(root, text="Сгенерировать и вычислить", command=generate)
btn_generate.pack(pady=10)

# Таблица результатов
# Заголовки
ttk.Label(frame_results, text="Генератор", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
ttk.Label(frame_results, text="Среднее / Ген. дисп. / Выб. дисп.", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
ttk.Label(frame_results, text="Отклонение от теории (среднее / дисперсия)", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=5, pady=5, sticky="w")

# Строка LCG
ttk.Label(frame_results, text="Базовый датчик (LCG)").grid(row=1, column=0, sticky="w", padx=5, pady=2)
var_mean_lcg_var = tk.StringVar()
ttk.Label(frame_results, textvariable=var_mean_lcg_var, anchor="w").grid(row=1, column=1, sticky="w", padx=5, pady=2)
var_diff_lcg = tk.StringVar()
ttk.Label(frame_results, textvariable=var_diff_lcg, anchor="w").grid(row=1, column=2, sticky="w", padx=5, pady=2)

# Строка встроенного генератора
ttk.Label(frame_results, text="Встроенный (random.random)").grid(row=2, column=0, sticky="w", padx=5, pady=2)
var_mean_builtin_var = tk.StringVar()
ttk.Label(frame_results, textvariable=var_mean_builtin_var, anchor="w").grid(row=2, column=1, sticky="w", padx=5, pady=2)
var_diff_builtin = tk.StringVar()
ttk.Label(frame_results, textvariable=var_diff_builtin, anchor="w").grid(row=2, column=2, sticky="w", padx=5, pady=2)

# Строка теоретических значений
ttk.Label(frame_results, text="Теоретические значения").grid(row=3, column=0, sticky="w", padx=5, pady=5)
var_theoretical = tk.StringVar()
ttk.Label(frame_results, textvariable=var_theoretical, anchor="w").grid(row=3, column=1, sticky="w", padx=5, pady=5)
ttk.Label(frame_results, text="---", anchor="w").grid(row=3, column=2, sticky="w", padx=5, pady=5)

# Инициализация пустыми строками
var_mean_lcg_var.set("---")
var_mean_builtin_var.set("---")
var_theoretical.set(f"{format_number(THEORETICAL_MEAN)} / {format_number(THEORETICAL_VARIANCE)}")
var_diff_lcg.set("---")
var_diff_builtin.set("---")

# Запуск приложения
root.mainloop()