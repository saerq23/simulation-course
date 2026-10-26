import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
from collections import deque

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def exp_random(rate: float) -> float:
    """Экспоненциальная случайная величина с интенсивностью rate."""
    return -math.log(1.0 - random.random()) / rate


class MM1Simulator:
    """Одноканальная СМО M/M/1 (бесконечная очередь, без отказов)."""

    def __init__(self, lam: float, mu: float, duration: float):
        if lam <= 0 or mu <= 0 or duration <= 0:
            raise ValueError("Все параметры должны быть положительными.")
        self.lam = lam
        self.mu = mu
        self.T = duration
        self.rho = lam / mu

    def theoretical(self):
        """Теоретические показатели M/M/1 (только при ρ < 1)."""
        rho = self.rho
        if rho >= 1.0:
            return None
        return {
            "P0":   1 - rho,
            "Pbusy": rho,
            "L":    rho / (1 - rho),
            "Lq":   rho * rho / (1 - rho),
            "W":    1 / (self.mu - self.lam),
            "Wq":   rho / (self.mu - self.lam),
        }

    def run(self) -> dict:
        """Одна реализация M/M/1 длительностью T."""
        time = 0.0
        n_in_system = 0
        n_in_queue = 0

        arrivals = 0
        served = 0
        wait_times = []      # Wq_i по обслуженным
        system_times = []    # W_i  по обслуженным

        # Интегралы для time-weighted средних
        L_integral = 0.0
        Lq_integral = 0.0
        P0_time = 0.0

        last_time = 0.0
        next_arrival = exp_random(self.lam)
        next_departure = float("inf")

        queue = deque()                # моменты прибытия ожидающих
        service_arrival_time = None    # прибытие текущего обслуживаемого

        while True:
            next_event = min(next_arrival, next_departure)

            if next_event > self.T:
                # Симуляция завершается — накопим остаток
                dt = self.T - last_time
                L_integral += n_in_system * dt
                Lq_integral += n_in_queue * dt
                if n_in_system == 0:
                    P0_time += dt
                break

            dt = next_event - last_time
            L_integral += n_in_system * dt
            Lq_integral += n_in_queue * dt
            if n_in_system == 0:
                P0_time += dt

            last_time = next_event
            time = next_event

            if next_arrival < next_departure:
                # ---------- ПРИБЫТИЕ ----------
                arrivals += 1
                if n_in_system == 0:
                    # Сервер свободен — обслуживаем сразу
                    wait_times.append(0.0)
                    n_in_system = 1
                    service_arrival_time = time
                    next_departure = time + exp_random(self.mu)
                else:
                    # Сервер занят — в очередь
                    queue.append(time)
                    n_in_system += 1
                    n_in_queue += 1
                next_arrival = time + exp_random(self.lam)
            else:
                # ---------- УХОД ОБСЛУЖЕННОЙ ----------
                served += 1
                system_times.append(time - service_arrival_time)
                n_in_system -= 1

                if queue:
                    arr_t = queue.popleft()
                    n_in_queue -= 1
                    wait_times.append(time - arr_t)
                    service_arrival_time = arr_t
                    next_departure = time + exp_random(self.mu)
                else:
                    next_departure = float("inf")
                    service_arrival_time = None

        T = self.T
        return {
            "arrivals": arrivals,
            "served":   served,
            "P0":       P0_time / T,
            "Pbusy":    1.0 - P0_time / T,
            "L":        L_integral / T,
            "Lq":       Lq_integral / T,
            "W":        sum(system_times) / len(system_times) if system_times else 0.0,
            "Wq":       sum(wait_times)   / len(wait_times)   if wait_times   else 0.0,
        }


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Лабораторная работа №9: СМО M/M/1")
        self.root.geometry("900x720")
        self.root.minsize(800, 600)

        main = ttk.Frame(root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(
            main,
            text="Система массового обслуживания M/M/1 (одноканальная, с очередью)",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        # Параметры (как в JS-примере: λ, μ, T)
        params = ttk.LabelFrame(main, text="Параметры моделирования", padding=10)
        params.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(params)
        row.pack(fill=tk.X)

        ttk.Label(row, text="λ (заявок/ед.вр):").pack(side=tk.LEFT, padx=(0, 3))
        self.lambda_var = tk.StringVar(value="3")
        ttk.Entry(row, textvariable=self.lambda_var, width=8).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row, text="μ (заявок/ед.вр):").pack(side=tk.LEFT, padx=(0, 3))
        self.mu_var = tk.StringVar(value="4")
        ttk.Entry(row, textvariable=self.mu_var, width=8).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(row, text="T (длительность):").pack(side=tk.LEFT, padx=(0, 3))
        self.T_var = tk.StringVar(value="1000")
        ttk.Entry(row, textvariable=self.T_var, width=8).pack(side=tk.LEFT, padx=(0, 15))

        # Кнопки (те же названия, что в JS-примере)
        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_row, text="Запустить симуляцию",
                   command=self.run_simulation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_row, text="Сброс",
                   command=self.reset).pack(side=tk.LEFT)

        # Строка про ρ
        self.rho_label = ttk.Label(main, text="", font=("Segoe UI", 10, "italic"))
        self.rho_label.pack(anchor="w", pady=(0, 8))

        # Таблица результатов
        results_frame = ttk.LabelFrame(main, text="Результаты: эмпирика vs теория",
                                       padding=8)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        cols = ("metric", "emp", "theory", "err")
        self.tree = ttk.Treeview(results_frame, columns=cols, show="headings", height=7)
        self.tree.heading("metric", text="Показатель")
        self.tree.heading("emp",    text="Эмпирическое")
        self.tree.heading("theory", text="Теоретическое")
        self.tree.heading("err",    text="Отн. погрешность, %")
        self.tree.column("metric", width=260, anchor="w")
        self.tree.column("emp",    width=130, anchor="center")
        self.tree.column("theory", width=130, anchor="center")
        self.tree.column("err",    width=140, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Дополнительная строка
        self.extra_label = ttk.Label(main, text="", font=("Segoe UI", 10))
        self.extra_label.pack(anchor="w", pady=(5, 8))

        # График (два подграфика: «Вероятности и длины» + «Времена»)
        chart_frame = ttk.LabelFrame(main, text="Сравнение эмпирических и теоретических показателей",
                                     padding=8)
        chart_frame.pack(fill=tk.BOTH, expand=True)

        self.figure = Figure(figsize=(8, 3.2), dpi=90)
        self.ax1 = self.figure.add_subplot(121)
        self.ax2 = self.figure.add_subplot(122)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ----------------------- Логика -----------------------
    def run_simulation(self):
        try:
            lam = float(self.lambda_var.get())
            mu = float(self.mu_var.get())
            T = float(self.T_var.get())
        except ValueError:
            messagebox.showerror("Ошибка", "Все параметры должны быть числами.")
            return

        if lam <= 0 or mu <= 0 or T <= 0:
            messagebox.showerror("Ошибка", "Все параметры должны быть больше нуля.")
            return

        sim = MM1Simulator(lam, mu, T)
        self.rho_label.config(text=f"Загрузка ρ = λ/μ = {sim.rho:.4f}")

        if sim.rho >= 1.0:
            messagebox.showwarning(
                "Внимание",
                f"ρ = {sim.rho:.4f} ≥ 1.\n"
                "Стационарного режима нет: очередь будет расти неограниченно.\n"
                "Теоретические формулы M/M/1 неприменимы.\n"
                "Для корректного сравнения задайте λ < μ."
            )

        res = sim.run()
        theory = sim.theoretical()

        # Таблица
        self.tree.delete(*self.tree.get_children())
        metrics = [
            ("Вероятность простоя P₀",   "P0"),
            ("Вероятность занятости (ρ)", "Pbusy"),
            ("Среднее число в системе L", "L"),
            ("Средняя длина очереди Lq",  "Lq"),
            ("Среднее время в системе W", "W"),
            ("Среднее время в очереди Wq","Wq"),
        ]
        for name, key in metrics:
            emp = res[key]
            if theory is not None:
                theor = theory[key]
                if theor > 1e-12:
                    err_str = f"{abs(emp - theor) / theor * 100:.2f}"
                else:
                    err_str = "н/д"
                theory_str = f"{theor:.4f}"
            else:
                theory_str = "—"
                err_str = "н/д"
            self.tree.insert("", tk.END,
                             values=(name, f"{emp:.4f}", theory_str, err_str))

        self.extra_label.config(
            text=f"Всего прибытий: {res['arrivals']}   |   Обслужено: {res['served']}"
        )

        self.draw_chart(res, theory)

    def draw_chart(self, res, theory):
        self.ax1.clear()
        self.ax2.clear()

        if theory is None:
            self.ax1.text(0.5, 0.5, "ρ ≥ 1\nнет стационарного режима",
                          ha="center", va="center",
                          transform=self.ax1.transAxes, fontsize=11)
            self.ax2.text(0.5, 0.5, "—",
                          ha="center", va="center",
                          transform=self.ax2.transAxes, fontsize=11)
            self.ax1.set_xticks([]); self.ax1.set_yticks([])
            self.ax2.set_xticks([]); self.ax2.set_yticks([])
            self.canvas.draw()
            return

        w = 0.35

        # Левая панель: P0, ρ, L, Lq
        keys1   = ["P0", "Pbusy", "L", "Lq"]
        labels1 = ["P0", "ρ", "L", "Lq"]
        emp1 = [res[k] for k in keys1]
        th1  = [theory[k] for k in keys1]
        x1 = list(range(len(keys1)))
        self.ax1.bar([i - w/2 for i in x1], emp1, w,
                     label="Эмпирическое", color="#36a2eb", alpha=0.85)
        self.ax1.bar([i + w/2 for i in x1], th1,  w,
                     label="Теоретическое", color="#ff6384", alpha=0.85)
        self.ax1.set_xticks(x1)
        self.ax1.set_xticklabels(labels1)
        self.ax1.set_title("Вероятности и длины")
        self.ax1.legend(fontsize=8)
        self.ax1.grid(axis="y", linestyle="--", alpha=0.5)

        # Правая панель: W, Wq
        keys2   = ["W", "Wq"]
        labels2 = ["W", "Wq"]
        emp2 = [res[k] for k in keys2]
        th2  = [theory[k] for k in keys2]
        x2 = list(range(len(keys2)))
        self.ax2.bar([i - w/2 for i in x2], emp2, w,
                     label="Эмпирическое", color="#36a2eb", alpha=0.85)
        self.ax2.bar([i + w/2 for i in x2], th2,  w,
                     label="Теоретическое", color="#ff6384", alpha=0.85)
        self.ax2.set_xticks(x2)
        self.ax2.set_xticklabels(labels2)
        self.ax2.set_title("Времена")
        self.ax2.legend(fontsize=8)
        self.ax2.grid(axis="y", linestyle="--", alpha=0.5)

        self.figure.tight_layout()
        self.canvas.draw()

    def reset(self):
        self.lambda_var.set("3")
        self.mu_var.set("4")
        self.T_var.set("1000")
        self.rho_label.config(text="")
        self.extra_label.config(text="")
        self.tree.delete(*self.tree.get_children())
        self.ax1.clear()
        self.ax2.clear()
        self.canvas.draw()


if __name__ == "__main__":
    random.seed()
    root = tk.Tk()
    App(root)
    root.mainloop()