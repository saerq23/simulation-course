import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import csv

# ------------------------------
# Константы состояний
# ------------------------------
STATE_NAMES = ["Ясно", "Облачно", "Пасмурно"]
STATE_CLASSES = ["clear-weather", "cloudy-weather", "overcast-weather"]
COLORS = {"clear-weather": "#f1c40f", "cloudy-weather": "#95a5a6", "overcast-weather": "#34495e"}
FG_COLORS = {"clear-weather": "#333", "cloudy-weather": "#fff", "overcast-weather": "#fff"}

class WeatherSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Марковская модель погоды")
        self.root.geometry("1100x750")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # обязательно для корректного завершения
        
        # Данные симуляции
        self.Q = None
        self.simulation_data = []  # для CSV
        self.time_in_state = [0, 0, 0]
        self.current_state = 0     # индекс: 0-Ясно, 1-Облачно, 2-Пасмурно
        self.current_time = 0.0
        self.animation_id = None
        self.sim_running = False
        
        self.setup_ui()
    
    def on_closing(self):
        """Гарантирует остановку всех фоновых процессов при закрытии окна."""
        self.stop_animation()
        self.sim_running = False
        self.root.destroy()
    
    # ---------- интерфейс ----------
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель параметров
        left_frame = ttk.LabelFrame(main_frame, text="Параметры модели", padding="10")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        
        # Матрица интенсивностей
        ttk.Label(left_frame, text="Интенсивности переходов (1/день):", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,10))
        
        self.q_entries = {}
        row_idx = 1
        for from_state, to_states in [("Ясно (1)", [("в Облачно", "q12", 0.4), ("в Пасмурно", "q13", 0.1)]),
                                      ("Облачно (2)", [("в Ясно", "q21", 0.3), ("в Пасмурно", "q23", 0.5)]),
                                      ("Пасмурно (3)", [("в Ясно", "q31", 0.1), ("в Облачно", "q32", 0.4)])]:
            ttk.Label(left_frame, text=f"Из {from_state}", font=("Arial", 9, "italic")).grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(5,0))
            row_idx += 1
            for label, key, default in to_states:
                ttk.Label(left_frame, text=label).grid(row=row_idx, column=0, sticky="e", padx=5)
                entry = ttk.Entry(left_frame, width=8)
                entry.insert(0, str(default))
                entry.grid(row=row_idx, column=1, sticky="w")
                self.q_entries[key] = entry
                row_idx += 1
        
        # Параметры симуляции
        ttk.Separator(left_frame, orient='horizontal').grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=10)
        row_idx += 1
        
        ttk.Label(left_frame, text="Время симуляции (дней):").grid(row=row_idx, column=0, sticky="e", padx=5)
        self.sim_time_var = tk.IntVar(value=1000)
        ttk.Spinbox(left_frame, from_=10, to=10000, textvariable=self.sim_time_var, width=8).grid(row=row_idx, column=1, sticky="w")
        row_idx += 1
        
        ttk.Label(left_frame, text="Начальное состояние:").grid(row=row_idx, column=0, sticky="e", padx=5)
        self.start_state_var = tk.StringVar(value=STATE_NAMES[0])
        ttk.Combobox(left_frame, textvariable=self.start_state_var, values=STATE_NAMES, state="readonly", width=10).grid(row=row_idx, column=1, sticky="w")
        row_idx += 1
        
        # Кнопки
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Запустить мгновенно", command=self.run_instant).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Анимация (1 день = 1с)", command=self.run_animation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сброс", command=self.reset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Скачать CSV", command=self.save_csv).pack(side=tk.LEFT, padx=5)
        
        # Правая панель отображения
        right_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,0))
        
        # Текущее состояние погоды
        self.weather_label = tk.Label(right_frame, text="Ясно", font=("Arial", 20, "bold"), bg=COLORS["clear-weather"], fg=FG_COLORS["clear-weather"], padx=20, pady=20)
        self.weather_label.pack(fill=tk.X, pady=(0,10))
        
        # Текущее время
        self.time_label = ttk.Label(right_frame, text="0 дней, 0 ч.")
        self.time_label.pack(anchor="w")
        
        # Таблица статистики
        columns = ("Состояние", "Время (дни)", "Эмп. вер.", "Теор. вер.", "Погрешность")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=3)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.pack(fill=tk.X, pady=10)
        
        # Место для графика
        self.fig, self.ax = plt.subplots(figsize=(5, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Настройка весов колонок
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
    
    # ---------- вспомогательные методы ----------
    def get_Q_matrix(self):
        """Считывает интенсивности из полей ввода и строит Q-матрицу."""
        try:
            q12 = float(self.q_entries["q12"].get())
            q13 = float(self.q_entries["q13"].get())
            q21 = float(self.q_entries["q21"].get())
            q23 = float(self.q_entries["q23"].get())
            q31 = float(self.q_entries["q31"].get())
            q32 = float(self.q_entries["q32"].get())
        except ValueError:
            messagebox.showerror("Ошибка", "Все интенсивности должны быть числами.")
            return None
        
        if any(x < 0 for x in [q12, q13, q21, q23, q31, q32]):
            messagebox.showerror("Ошибка", "Интенсивности не могут быть отрицательными.")
            return None
        
        l1 = q12 + q13
        l2 = q21 + q23
        l3 = q31 + q32
        
        Q = np.array([
            [-l1, q12, q13],
            [q21, -l2, q23],
            [q31, q32, -l3]
        ])
        return Q
    
    def solve_theoretical(self, Q):
        """Находит стационарное распределение π из системы π·Q = 0, Σπ = 1."""
        n = Q.shape[0]
        A = np.vstack([Q.T[:-1], np.ones(n)])  # заменяем последнюю строку на сумму=1
        b = np.zeros(n)
        b[-1] = 1.0
        try:
            pi = np.linalg.solve(A, b)
            return pi
        except np.linalg.LinAlgError:
            return None
    
    def get_next_state(self, Q, current):
        """Выбирает следующее состояние на основе интенсивностей переходов."""
        lambda_out = -Q[current, current]
        probs = Q[current].copy()
        probs[current] = 0  # обнуляем диагональ (она отрицательная)
        probs = probs / lambda_out
        return np.random.choice(len(Q), p=probs)
    
    def update_weather_display(self, state_index):
        """Обновляет цветную панель с погодой."""
        class_name = STATE_CLASSES[state_index]
        self.weather_label.config(text=STATE_NAMES[state_index], bg=COLORS[class_name], fg=FG_COLORS[class_name])
    
    def update_time_display(self, total_time):
        days = int(total_time)
        hours = int((total_time % 1) * 24)
        self.time_label.config(text=f"{days} дней, {hours} ч.")
    
    def update_stats_table(self, theor=None):
        """Заполняет таблицу текущими значениями статистики."""
        self.tree.delete(*self.tree.get_children())
        for i in range(3):
            emp = self.time_in_state[i] / self.current_time if self.current_time > 0 else 0.0
            theo_val = theor[i] if theor is not None else 0.0
            err = abs(emp - theo_val)
            self.tree.insert("", tk.END, values=(
                STATE_NAMES[i],
                f"{self.time_in_state[i]:.2f}",
                f"{emp:.4f}",
                f"{theo_val:.4f}",
                f"{err:.4f}"
            ))
    
    def draw_chart(self, theor):
        """Рисует столбчатую диаграмму эмпирических и теоретических вероятностей."""
        self.ax.clear()
        emp = [t / self.current_time if self.current_time > 0 else 0 for t in self.time_in_state]
        x = np.arange(3)
        width = 0.35
        self.ax.bar(x - width/2, emp, width, label='Эмпирические', color='skyblue')
        self.ax.bar(x + width/2, theor, width, label='Теоретические', color='salmon')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(STATE_NAMES)
        self.ax.set_ylim(0, 1)
        self.ax.legend()
        self.canvas.draw()
    
    # ---------- логика симуляции ----------
    def simulate_step(self, Q, max_time, is_animation=False):
        """
        Выполняет один интервал пребывания в текущем состоянии и планирует следующий переход.
        Если is_animation=True, ожидает dt секунд перед переходом; иначе мгновенно.
        """
        if not self.sim_running or self.current_time >= max_time:
            return
        
        lambda_out = -Q[self.current_state, self.current_state]
        if lambda_out == 0:
            dt = max_time - self.current_time
        else:
            dt = np.random.exponential(1.0 / lambda_out)
        dt = min(dt, max_time - self.current_time)
        
        # Запись интервала
        self.simulation_data.append({
            "day_end": round(self.current_time + dt, 2),
            "state": STATE_NAMES[self.current_state],
            "duration": round(dt, 2)
        })
        
        # Обновление временных счётчиков
        self.time_in_state[self.current_state] += dt
        self.current_time += dt
        
        # Обновление GUI
        self.update_weather_display(self.current_state)
        self.update_time_display(self.current_time)
        theor = self.solve_theoretical(Q)
        if theor is not None:
            self.update_stats_table(theor)
            self.draw_chart(theor)
        
        # Проверка завершения
        if self.current_time >= max_time:
            self.sim_running = False
            self.animation_id = None
            return
        
        # Переход к следующему состоянию
        if is_animation:
            # Планируем вызов animate_next_step через dt секунд
            # ИСПРАВЛЕНИЕ: не используем lambda, передаём метод и аргументы напрямую
            self.animation_id = self.root.after(int(dt * 1000), self.animate_next_step, Q, max_time)
        else:
            # Мгновенный режим: сразу выбираем новое состояние и продолжаем
            # (используется только если вызвана не из _instant_simulation, а напрямую, но мы используем отдельный поток)
            next_state = self.get_next_state(Q, self.current_state)
            self.current_state = next_state
            self.simulate_step(Q, max_time, is_animation=False)
    
    def animate_next_step(self, Q, max_time):
        """Вызывается после паузы (в анимационном режиме) для переключения состояния."""
        # Проверка, что окно ещё существует и симуляция не остановлена
        if not self.sim_running or not self.root.winfo_exists():
            return
        try:
            next_state = self.get_next_state(Q, self.current_state)
            self.current_state = next_state
            # Продолжаем симуляцию
            self.simulate_step(Q, max_time, is_animation=True)
        except Exception as e:
            # На случай ошибок в вычислениях
            messagebox.showerror("Ошибка", str(e))
            self.sim_running = False
    
    def run_instant(self):
        """Мгновенная симуляция в фоновом потоке."""
        Q = self.get_Q_matrix()
        if Q is None:
            return
        
        self.stop_animation()
        self.prepare_simulation(Q)
        self.sim_running = True
        
        threading.Thread(target=self._instant_simulation, args=(Q,), daemon=True).start()
    
    def _instant_simulation(self, Q):
        """Фоновый расчёт."""
        max_time = self.sim_time_var.get()
        while self.current_time < max_time and self.sim_running:
            lambda_out = -Q[self.current_state, self.current_state]
            if lambda_out == 0:
                dt = max_time - self.current_time
            else:
                dt = np.random.exponential(1.0 / lambda_out)
            dt = min(dt, max_time - self.current_time)
            
            self.simulation_data.append({
                "day_end": round(self.current_time + dt, 2),
                "state": STATE_NAMES[self.current_state],
                "duration": round(dt, 2)
            })
            
            self.time_in_state[self.current_state] += dt
            self.current_time += dt
            
            if self.current_time < max_time:
                self.current_state = self.get_next_state(Q, self.current_state)
        
        # По окончании обновляем GUI в основном потоке
        if self.root.winfo_exists():
            self.root.after(0, self.finish_simulation, Q)
        self.sim_running = False
    
    def run_animation(self):
        """Пошаговая анимация (реальное время)."""
        Q = self.get_Q_matrix()
        if Q is None:
            return
        
        self.stop_animation()
        self.prepare_simulation(Q)
        self.sim_running = True
        # Запускаем первый шаг
        self.simulate_step(Q, self.sim_time_var.get(), is_animation=True)
    
    def prepare_simulation(self, Q):
        """Общая подготовка данных перед стартом."""
        self.simulation_data.clear()
        self.time_in_state = [0, 0, 0]
        self.current_time = 0.0
        start_state_name = self.start_state_var.get()
        self.current_state = STATE_NAMES.index(start_state_name)
        self.update_weather_display(self.current_state)
        self.update_time_display(0)
        self.update_stats_table()
        self.draw_chart(np.zeros(3))
    
    def finish_simulation(self, Q):
        """Завершающее обновление GUI (вызывается из основного потока)."""
        if not self.root.winfo_exists():
            return
        self.update_weather_display(self.current_state)
        self.update_time_display(self.current_time)
        theor = self.solve_theoretical(Q)
        if theor is not None:
            self.update_stats_table(theor)
            self.draw_chart(theor)
        self.sim_running = False
        self.animation_id = None
    
    def stop_animation(self):
        """Останавливает анимацию, отменяя запланированный вызов."""
        if self.animation_id is not None:
            try:
                self.root.after_cancel(self.animation_id)
            except Exception:
                pass
            self.animation_id = None
        self.sim_running = False
    
    def reset(self):
        """Полный сброс интерфейса и данных."""
        self.stop_animation()
        self.simulation_data.clear()
        self.time_in_state = [0, 0, 0]
        self.current_time = 0.0
        start_state_name = self.start_state_var.get()
        self.current_state = STATE_NAMES.index(start_state_name)
        self.update_weather_display(self.current_state)
        self.update_time_display(0)
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.canvas.draw()
    
    def save_csv(self):
        if not self.simulation_data:
            messagebox.showwarning("Нет данных", "Сначала запустите симуляцию.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=["day_end", "state", "duration"])
            writer.writeheader()
            writer.writerows(self.simulation_data)
        messagebox.showinfo("Готово", f"Данные сохранены в {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherSimulator(root)
    root.mainloop()