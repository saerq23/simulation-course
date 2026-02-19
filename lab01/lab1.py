import numpy as np                      # Библиотека для математических вычислений
import matplotlib.pyplot as plt         # Библиотека для построения графиков
import tkinter as tk                    # Библиотека для создания графического интерфейса
from tkinter import messagebox          # Модуль для вывода окон с ошибками

# ================= ФУНКЦИЯ МОДЕЛИРОВАНИЯ =================
def simulate():                         # Функция вызывается при нажатии кнопки

    try:                                # Блок перехвата ошибок (если введены не числа)

        # ===== Получение параметров из интерфейса =====
        m = float(entry_m.get())        # Получаем массу из поля ввода и преобразуем в float
        Cd = float(entry_Cd.get())      # Получаем коэффициент сопротивления
        rho = float(entry_rho.get())    # Получаем плотность воздуха
        S = float(entry_S.get())        # Получаем площадь поперечного сечения
        v0 = float(entry_v0.get())      # Получаем начальную скорость
        angle_deg = float(entry_angle.get())  # Получаем угол в градусах
        dt = float(entry_dt.get())      # Получаем шаг интегрирования

        g = 9.81                        # Ускорение свободного падения
        k = Cd * rho * S / 2            # Коэффициент сопротивления среды

        angle = np.radians(angle_deg)   # Перевод угла из градусов в радианы

        # ===== Разложение начальной скорости на компоненты =====
        vx = v0 * np.cos(angle)         # Горизонтальная составляющая скорости
        vy = v0 * np.sin(angle)         # Вертикальная составляющая скорости

        x, y = 0, 0                     # Начальные координаты
        xs, ys = [x], [y]               # Списки для хранения траектории
        max_height = 0                  # Переменная для максимальной высоты

        # ===== Метод Эйлера =====
        while y >= 0:                   # Пока тело не упало на землю

            v = np.sqrt(vx**2 + vy**2)  # Модуль полной скорости

            ax = -k/m * vx * v          # Ускорение по X (сопротивление)
            ay = -g - k/m * vy * v      # Ускорение по Y (гравитация + сопротивление)

            vx += ax * dt               # Обновление скорости по X
            vy += ay * dt               # Обновление скорости по Y

            x += vx * dt                # Обновление координаты X
            y += vy * dt                # Обновление координаты Y

            xs.append(x)                # Сохраняем точку X
            ys.append(y)                # Сохраняем точку Y

            if y > max_height:          # Проверяем максимальную высоту
                max_height = y          # Обновляем максимум

        final_speed = np.sqrt(vx**2 + vy**2)  # Скорость в момент падения

        # ===== Вывод результатов в интерфейс =====
        result_label.config(            # Обновляем текст метки
            text=f"Дальность: {round(x,2)} м\n"
                 f"Макс высота: {round(max_height,2)} м\n"
                 f"Конечная скорость: {round(final_speed,2)} м/с"
        )

        
        plt.figure()                    # Создание нового окна графика
        plt.plot(xs, ys)                # Построение траектории
        plt.xlabel("x (м)")             # Подпись оси X
        plt.ylabel("y (м)")             # Подпись оси Y
        plt.title("Траектория полёта")  # Заголовок графика
        plt.grid()                      # Включаем сетку
        plt.show()                      # Отображаем график

    except:                             # Если произошла ошибка
        messagebox.showerror(           # Показываем окно ошибки
            "Ошибка",
            "Введите корректные числовые значения!"
        )


root = tk.Tk()                         
root.title("Моделирование полета тела")  



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

tk.Label(root, text="Шаг dt").grid(row=6, column=0)
entry_dt = tk.Entry(root)
entry_dt.insert(0, "0.01")
entry_dt.grid(row=6, column=1)


tk.Button(
    root,
    text="Моделировать",
    command=simulate           
).grid(row=7, column=0, columnspan=2)


result_label = tk.Label(root, text="")   
result_label.grid(row=8, column=0, columnspan=2)


root.mainloop()   
