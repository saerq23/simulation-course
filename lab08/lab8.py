import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PoissonSimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа: Пуассоновский поток (события на сервере)")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        # Параметры по умолчанию
        self.lambda_var = tk.DoubleVar(value=2.0)
        self.t_var = tk.DoubleVar(value=5.0)
        self.duration_var = tk.DoubleVar(value=60.0)

        # Данные последней симуляции
        self.counts = None
        self.interval_t = None
        self.sim_duration = None

        # Создаём интерфейс
        self.create_widgets()
        self.reset_ui()

    # -----------------------------------------------------------------
    def create_widgets(self):
        # Главный контейнер (сетка с двумя колонками: левая (вес 1) и правая (вес 2))
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Настроим сетку
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # Левая панель - параметры
        left_frame = ttk.Frame(main_frame, padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)

        # Правая панель - результаты
        right_frame = ttk.Frame(main_frame, padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

        # ---- Левая панель: параметры и кнопки ----
        param_frame = ttk.LabelFrame(left_frame, text="Параметры моделирования", padding=10)
        param_frame.pack(fill=tk.X, pady=(0,10))

        # λ
        ttk.Label(param_frame, text="Интенсивность λ (заявок/сек)").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.entry_lambda = ttk.Entry(param_frame, textvariable=self.lambda_var, width=10)
        self.entry_lambda.grid(row=0, column=1, sticky=tk.W, padx=5)

        # T
        ttk.Label(param_frame, text="Интервал T (сек)").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.entry_t = ttk.Entry(param_frame, textvariable=self.t_var, width=10)
        self.entry_t.grid(row=1, column=1, sticky=tk.W, padx=5)

        # Длительность симуляции
        ttk.Label(param_frame, text="Длительность симуляции (сек)").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.entry_duration = ttk.Entry(param_frame, textvariable=self.duration_var, width=10)
        self.entry_duration.grid(row=2, column=1, sticky=tk.W, padx=5)

        # Кнопки
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        self.btn_simulate = ttk.Button(btn_frame, text="Запустить симуляцию", command=self.run_simulation)
        self.btn_simulate.pack(side=tk.LEFT, padx=(0,5))
        self.btn_reset = ttk.Button(btn_frame, text="Сброс", command=self.reset_ui)
        self.btn_reset.pack(side=tk.LEFT)

        # Теоретическое значение
        self.theory_label = ttk.Label(left_frame, text="Теоретическое значение: μ = λT = -", font=("Arial", 10, "italic"))
        self.theory_label.pack(anchor=tk.W, pady=(10,0))

        # ---- Правая панель: результаты ----
        # Сводка
        summary_frame = ttk.LabelFrame(right_frame, text="Результаты", padding=8)
        summary_frame.pack(fill=tk.X, pady=(0,10))

        self.var_intervals = tk.StringVar(value="-")
        self.var_last_interval = tk.StringVar(value="-")
        self.var_mean = tk.StringVar(value="-")
        self.var_variance = tk.StringVar(value="-")

        grid_frame = ttk.Frame(summary_frame)
        grid_frame.pack()
        labels = [
            ("Интервалов:", self.var_intervals),
            ("Заявок в последнем интервале T:", self.var_last_interval),
            ("Среднее:", self.var_mean),
            ("Дисперсия:", self.var_variance)
        ]
        for i, (text, var) in enumerate(labels):
            ttk.Label(grid_frame, text=text).grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)
            ttk.Label(grid_frame, textvariable=var, font=("Arial", 9, "bold")).grid(row=i, column=1, sticky=tk.E, pady=2, padx=5)

        # Таблица интервалов
        table_frame = ttk.LabelFrame(right_frame, text="Число заявок по интервалам", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        columns = ("#", "Диапазон времени", "Заявок")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        self.tree.heading("#", text="Интервал")
        self.tree.heading("Диапазон времени", text="Диапазон времени")
        self.tree.heading("Заявок", text="Заявок")
        self.tree.column("#", width=70, anchor=tk.CENTER)
        self.tree.column("Диапазон времени", width=150, anchor=tk.CENTER)
        self.tree.column("Заявок", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # График распределения
        chart_frame = ttk.LabelFrame(right_frame, text="Распределение числа заявок", padding=5)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0,10))

        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Вывод
        conclusion_frame = ttk.LabelFrame(right_frame, text="Вывод", padding=5)
        conclusion_frame.pack(fill=tk.X)
        self.conclusion_text = tk.Text(conclusion_frame, height=4, wrap=tk.WORD, state=tk.DISABLED, bg="#f0f0f0")
        self.conclusion_text.pack(fill=tk.X)

    # Вычисляем количество полных интервалов (округляем вверх)
    def simulate_poisson(self, lambda_val, total_time, interval_len):
        intervals = max(1, math.ceil(total_time / interval_len)) # Массив счётчиков для каждого интервала
        counts = [0] * intervals
        current_time = 0.0
        while True:
            u = random.random()
            inter_arrival = -math.log(1.0 - u) / lambda_val  # Вычисление интервала до следующего события по формуле: tau = -ln(1-U)/lambda
            current_time += inter_arrival
            if current_time > total_time:
                break
            idx = int(current_time / interval_len)
            if idx >= intervals:
                idx = intervals - 1
            counts[idx] += 1
        return counts

    def run_simulation(self):
        # Проверка ввода
        try:
            lam = self.lambda_var.get()
            T = self.t_var.get()
            dur = self.duration_var.get()
        except tk.TclError: # Если введены не числа
            messagebox.showerror("Ошибка ввода", "Введите числовые значения.")
            return

        if lam <= 0 or T <= 0 or dur <= 0:  # Проверка положительности значений
            messagebox.showerror("Ошибка ввода", "λ, T и длительность должны быть положительными.")
            return

        self.interval_t = T
        self.sim_duration = dur
        self.counts = self.simulate_poisson(lam, dur, T)

        intervals = len(self.counts)
        total_requests = sum(self.counts)
        mean_val = total_requests / intervals # среднее
        variance_val = sum((c - mean_val) ** 2 for c in self.counts) / intervals # дисперсия
        theory = lam * T

        # Обновляем сводку
        self.var_intervals.set(str(intervals))
        self.var_last_interval.set(str(self.counts[-1]))
        self.var_mean.set(f"{mean_val:.4f}")
        self.var_variance.set(f"{variance_val:.4f}")
        self.theory_label.config(text=f"Теоретическое значение: μ = λT = {theory:.4f}")

        # Таблица
        self.tree.delete(*self.tree.get_children())
        for i, cnt in enumerate(self.counts):
            start = i * T
            end = min((i + 1) * T, dur)
            self.tree.insert("", tk.END, values=(i+1, f"{start:.2f} - {end:.2f}", cnt))

        # График
        self.draw_distribution_chart()

        # Вывод
        self.update_conclusion(mean_val, variance_val, theory)

    def draw_distribution_chart(self):
        self.ax.clear()
        if not self.counts:
            self.canvas.draw()
            return

        max_c = max(self.counts)
        freq = [0] * (max_c + 1)
        for c in self.counts:
            freq[c] += 1

        self.ax.bar(range(len(freq)), freq, color='#36a2eb', alpha=0.7)
        self.ax.set_xlabel("Число заявок в интервале T")
        self.ax.set_ylabel("Число интервалов")
        self.ax.set_title("Распределение числа заявок")
        self.ax.set_xticks(range(len(freq)))
        self.ax.grid(axis='y', linestyle='--', alpha=0.7)
        self.fig.tight_layout()
        self.canvas.draw()

    def update_conclusion(self, mean_val, variance_val, theory):
        if theory == 0:
            msg = "Теоретическое значение равно нулю, проверьте параметры."
        else:
            rel_mean = abs(mean_val - theory) / theory
            rel_var = abs(variance_val - theory) / theory
            tol = 0.15
            if rel_mean <= tol and rel_var <= tol:
                msg = (f"Среднее и дисперсия близки к теоретическому μ = λT = {theory:.3f}. "
                       "Результаты согласуются с пуассоновским характером потока.")
            else:
                msg = (f"Наблюдаются отклонения от теоретического μ = λT = {theory:.3f}. "
                       "Увеличьте длительность моделирования, чтобы оценки стабилизировались.")

        self.conclusion_text.config(state=tk.NORMAL)
        self.conclusion_text.delete("1.0", tk.END)
        self.conclusion_text.insert("1.0", msg)
        self.conclusion_text.config(state=tk.DISABLED)

    def reset_ui(self):
        """Сбрасывает интерфейс до начального состояния."""
        self.var_intervals.set("-")
        self.var_last_interval.set("-")
        self.var_mean.set("-")
        self.var_variance.set("-")
        self.theory_label.config(text="Теоретическое значение: μ = λT = -")
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.canvas.draw()
        self.conclusion_text.config(state=tk.NORMAL)
        self.conclusion_text.delete("1.0", tk.END)
        self.conclusion_text.insert("1.0", "Запустите симуляцию, чтобы получить результаты.")
        self.conclusion_text.config(state=tk.DISABLED)
        self.counts = None

# -----------------------------------------------------------------

if __name__ == "__main__":
    root = tk.Tk()
    app = PoissonSimulationApp(root)
    root.mainloop()