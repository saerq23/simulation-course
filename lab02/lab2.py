import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# Метод прогонки (TDMA)
def thomas_algorithm(a, b, c, d):
    n = len(d)
    alpha = np.zeros(n)
    beta = np.zeros(n)
    x = np.zeros(n)

    alpha[0] = -c[0] / b[0]  # Первый коэффициент (начало прогонки)
    beta[0] = d[0] / b[0]

 # Прямая прогонка (движение слева направо)

    for i in range(1, n):
        denom = b[i] + a[i] * alpha[i - 1]
        alpha[i] = -c[i] / denom if i < n - 1 else 0
        beta[i] = (d[i] - a[i] * beta[i - 1]) / denom

    x[-1] = beta[-1]

    for i in reversed(range(n - 1)):
        x[i] = alpha[i] * x[i + 1] + beta[i]

    return x


# Решение уравнения
def solve_heat(rho, c, lam, L, T_left, T_right, T0, dt, dx, t_end):
    nx = int(L / dx) + 1
    nt = int(t_end / dt)

    x_vals = np.linspace(0, L, nx)

    T = np.ones(nx) * T0   # Начальное распределение температуры
    T[0] = T_left
    T[-1] = T_right

    r = lam * dt / (rho * c * dx**2)  # Безразмерный коэффициент схемы

    for _ in range(nt):
        a = np.zeros(nx)
        b = np.zeros(nx) # главная диагональ
        c_ = np.zeros(nx)
        d = np.zeros(nx) # правая чаасть

        for i in range(1, nx - 1):
            a[i] = -r
            b[i] = 1 + 2 * r
            c_[i] = -r
            d[i] = T[i]

        b[0] = 1
        d[0] = T_left

        b[-1] = 1
        d[-1] = T_right

        T = thomas_algorithm(a, b, c_, d)

    return x_vals, T, T[nx // 2]


# Запуск одного расчёта (график)
def run_single():
    try:
        rho = float(entry_rho.get())
        c = float(entry_c.get())
        lam = float(entry_lam.get())
        L = float(entry_L.get())

        T_left = float(entry_T_left.get())
        T_right = float(entry_T_right.get())
        T0 = float(entry_T0.get())

        dt = float(entry_dt.get())
        dx = float(entry_dx.get())
        t_end = float(entry_tend.get())
    except:
        result_label.config(text="Ошибка ввода параметров")
        return

    x_vals, T, T_center = solve_heat(
        rho, c, lam, L, T_left, T_right, T0, dt, dx, t_end
    )

    result_label.config(text=f"Температура в центре: {T_center:.6f} °C")

    ax.clear()
    ax.plot(x_vals, T)
    ax.set_xlabel("Координата x (м)")
    ax.set_ylabel("Температура (°C)")
    ax.set_title("Распределение температуры")
    ax.grid(True)
    canvas.draw()


# Автоматический перебор шагов
def run_table():
    try:
        rho = float(entry_rho.get())
        c = float(entry_c.get())
        lam = float(entry_lam.get())
        L = float(entry_L.get())

        T_left = float(entry_T_left.get())
        T_right = float(entry_T_right.get())
        T0 = float(entry_T0.get())

        t_end = float(entry_tend.get())
    except:
        print("Ошибка ввода параметров")
        return

    steps = [0.1, 0.01, 0.001, 0.0001]

    print("\nТаблица температур в центре (t = 2 сек)")
    print("dt \\ dx | 0.1 | 0.01 | 0.001 | 0.0001")
    print("-" * 50)

    for dt in steps:
        row = f"{dt:<7} | "
        for dx in steps:
            try:
                _, _, T_center = solve_heat(
                    rho, c, lam, L,
                    T_left, T_right, T0,
                    dt, dx, t_end
                )
                row += f"{T_center:8.4f} | "
            except:
                row += "  error  | "
        print(row)


# GUI
root = tk.Tk()
root.title("Моделирование теплопроводности (МКР)")


frame_inputs = ttk.Frame(root)
frame_inputs.pack(side=tk.LEFT, padx=10, pady=10)


def add_input(label_text, default_value):
    ttk.Label(frame_inputs, text=label_text).pack()
    entry = ttk.Entry(frame_inputs)
    entry.insert(0, default_value)
    entry.pack()
    return entry


entry_rho = add_input("Плотность ρ", "7800")
entry_c = add_input("Теплоемкость c", "460")
entry_lam = add_input("Теплопроводность λ", "46")
entry_L = add_input("Длина L (м)", "0.1")

entry_T_left = add_input("Температура слева", "100")
entry_T_right = add_input("Температура справа", "50")
entry_T0 = add_input("Начальная температура", "20")

entry_dt = add_input("Шаг по времени dt", "0.01")
entry_dx = add_input("Шаг по пространству dx", "0.001")
entry_tend = add_input("Время моделирования", "2.0")

ttk.Button(frame_inputs, text="Построить график", command=run_single).pack(pady=5)
ttk.Button(frame_inputs, text="Вывести таблицу в консоль", command=run_table).pack(pady=5)

result_label = ttk.Label(frame_inputs, text="")
result_label.pack()


frame_plot = ttk.Frame(root)
frame_plot.pack(side=tk.RIGHT, padx=10, pady=10)

fig = Figure(figsize=(6, 4), dpi=100)
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=frame_plot)
canvas.get_tk_widget().pack()

root.mainloop()