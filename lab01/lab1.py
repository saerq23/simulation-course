import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox


def simulate_single(m, Cd, rho, S, v0, angle_deg, dt):
    g = 9.81
    k = Cd * rho * S / 2
    angle = np.radians(angle_deg)

    vx = v0 * np.cos(angle)
    vy = v0 * np.sin(angle)

    x, y = 0, 0
    xs, ys = [x], [y]
    max_height = 0

    while y >= 0:
        v = np.sqrt(vx**2 + vy**2)

        ax = -k/m * vx * v
        ay = -g - k/m * vy * v

        vx += ax * dt
        vy += ay * dt

        x += vx * dt
        y += vy * dt

        xs.append(x)
        ys.append(y)

        if y > max_height:
            max_height = y

    final_speed = np.sqrt(vx**2 + vy**2)

    return xs, ys, x, max_height, final_speed


def simulate():
    try:
        m = float(entry_m.get())
        Cd = float(entry_Cd.get())
        rho = float(entry_rho.get())
        S = float(entry_S.get())
        v0 = float(entry_v0.get())
        angle_deg = float(entry_angle.get())

        dt_values = entry_dt.get().split(",")
        dt_values = [float(dt.strip()) for dt in dt_values]

        plt.figure()

        results_text = ""

        for dt in dt_values:
            xs, ys, distance, height, speed = simulate_single(
                m, Cd, rho, S, v0, angle_deg, dt
            )

            plt.plot(xs, ys, label=f"dt={dt}")

            results_text += (
                f"dt={dt} → "
                f"Дальность: {round(distance,2)} м, "
                f"Высота: {round(height,2)} м, "
                f"Скорость: {round(speed,2)} м/с\n"
            )

        plt.xlabel("x (м)")
        plt.ylabel("y (м)")
        plt.title("Сравнение траекторий при разных шагах")
        plt.legend()
        plt.grid()
        plt.show()

        result_label.config(text=results_text)

    except:
        messagebox.showerror(
            "Ошибка",
            "Введите корректные числовые значения!\n"
            "Несколько dt вводите через запятую."
        )


root = tk.Tk()
root.title("Сравнение шагов метода Эйлера")

tk.Label(root, text="Масса (кг)").grid(row=0, column=0)
entry_m = tk.Entry(root)
entry_m.insert(0, "1.0")
entry_m.grid(row=0, column=1)

tk.Label(root, text="Cd").grid(row=1, column=0)
entry_Cd = tk.Entry(root)
entry_Cd.insert(0, "0.47")
entry_Cd.grid(row=1, column=1)

tk.Label(root, text="Плотность воздуха (кг/м³)").grid(row=2, column=0)
entry_rho = tk.Entry(root)
entry_rho.insert(0, "1.225")
entry_rho.grid(row=2, column=1)

tk.Label(root, text="Площадь S (м²)").grid(row=3, column=0)
entry_S = tk.Entry(root)
entry_S.insert(0, "0.01")
entry_S.grid(row=3, column=1)

tk.Label(root, text="Начальная скорость (м/с)").grid(row=4, column=0)
entry_v0 = tk.Entry(root)
entry_v0.insert(0, "100")
entry_v0.grid(row=4, column=1)

tk.Label(root, text="Угол (градусы)").grid(row=5, column=0)
entry_angle = tk.Entry(root)
entry_angle.insert(0, "45")
entry_angle.grid(row=5, column=1)

tk.Label(root, text="Шаги dt (через запятую)").grid(row=6, column=0)
entry_dt = tk.Entry(root)
entry_dt.insert(0, "1, 0.1, 0.01, 0.001")
entry_dt.grid(row=6, column=1)

tk.Button(root, text="Моделировать", command=simulate).grid(row=7, column=0, columnspan=2)

result_label = tk.Label(root, text="", justify="left")
result_label.grid(row=8, column=0, columnspan=2)

root.mainloop()
