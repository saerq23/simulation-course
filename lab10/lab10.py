import tkinter as tk
from tkinter import ttk, messagebox
import heapq
import math
import random
from collections import deque

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# --------------------- Классы предметной области (ООП) ---------------------
class Request:
    """Заявка"""
    def __init__(self, req_id, arrival_time, max_wait_time):
        self.id = req_id
        self.arrival_time = arrival_time
        self.max_wait_time = max_wait_time          # экспоненциально распределённое время терпения
        self.abandon_time = arrival_time + max_wait_time  # момент, когда заявка уходит необслуженной
        self.status = "NEW"                         # NEW, IN_QUEUE, SERVING, SERVED, REJECTED, ABANDONED
        self.service_start_time = None
        self.finish_time = None


class Server:
    """Обслуживающий прибор (канал)"""
    def __init__(self, server_id):
        self.id = server_id
        self.is_busy = False
        self.current_request = None

    def start_service(self, req, current_time, mu):
        """Начать обслуживание заявки, вернуть время окончания"""
        self.is_busy = True
        self.current_request = req
        req.status = "SERVING"
        req.service_start_time = current_time
        service_duration = exp_random(mu)
        return current_time + service_duration

    def finish_service(self, current_time):
        """Завершить обслуживание, вернуть обслуженную заявку"""
        if not self.current_request:
            return None
        req = self.current_request
        req.status = "SERVED"
        req.finish_time = current_time
        self.is_busy = False
        self.current_request = None
        return req


class EventQueue:
    """Очередь событий с приоритетом по времени"""
    def __init__(self):
        self._heap = []

    def push(self, event_type, event_time, request, server=None):
        """Добавить событие"""
        heapq.heappush(self._heap, (event_time, event_type, request, server))

    def pop(self):
        """Извлечь ближайшее событие"""
        return heapq.heappop(self._heap) if self._heap else None

    def is_empty(self):
        return len(self._heap) == 0


# --------------------- Вспомогательные функции ---------------------
def exp_random(rate):
    """Экспоненциальная случайная величина с интенсивностью rate"""
    if rate <= 0:
        return float('inf')
    return -math.log(1.0 - random.random()) / rate


# --------------------- Ядро имитационного моделирования ---------------------
class Simulation:
    """Основной класс симуляции"""
    def __init__(self, lambda_, mu, c, K, gamma, T):
        self.lambda_ = lambda_
        self.mu = mu
        self.c = c
        self.K = K          # максимальный размер очереди
        self.gamma = gamma  # интенсивность ухода (нетерпеливость)
        self.T = T          # длительность симуляции

        self.servers = [Server(i+1) for i in range(c)]
        self.queue = deque()
        self.all_requests = []
        self.event_log = []         # для таблицы (первые 30 событий)
        self.stats = {
            "total": 0,
            "served": 0,
            "rejected": 0,
            "abandoned": 0,
            "Q": 0.0,
            "Wq": 0.0
        }

    def _log_event(self, time, event_type, req, state_str):
        """Запись события, но не более 30"""
        if len(self.event_log) < 30:
            self.event_log.append((time, event_type, req.id, state_str))

    def run(self):
        eq = EventQueue()
        time = 0
        req_counter = 0

        # Генерация всех прибытий до T
        arrival_time = exp_random(self.lambda_)
        while arrival_time <= self.T:
            req_counter += 1
            max_wait = exp_random(self.gamma) if self.gamma > 0 else float('inf')
            req = Request(req_counter, arrival_time, max_wait)
            self.all_requests.append(req)
            eq.push("ARRIVAL", arrival_time, req)
            arrival_time += exp_random(self.lambda_)

        served_count = 0
        rejected_count = 0
        abandoned_count = 0

        # Основной цикл обработки событий
        while not eq.is_empty():
            ev = eq.pop()
            if ev[0] > self.T:      # событие после окончания симуляции
                break

            time = ev[0]
            event_type = ev[1]
            req = ev[2]
            server = ev[3]

            busy = sum(1 for s in self.servers if s.is_busy)
            q_len = len(self.queue)
            state_str = f"{busy}/{self.c} | Оч: {q_len}/{self.K}"

            if event_type == "ARRIVAL":
                free_server = next((s for s in self.servers if not s.is_busy), None)
                if free_server:
                    dep_time = free_server.start_service(req, time, self.mu)
                    eq.push("DEPARTURE", dep_time, req, free_server)
                    self._log_event(time, "Прибытие", req, f"{state_str} -> Начат приб.{free_server.id}")
                else:
                    if q_len < self.K:
                        req.status = "IN_QUEUE"
                        self.queue.append(req)
                        self._log_event(time, "В очередь", req, state_str)
                        if req.abandon_time < float('inf'):
                            eq.push("ABANDON", req.abandon_time, req)
                    else:
                        req.status = "REJECTED"
                        rejected_count += 1
                        self._log_event(time, "ОТКАЗ (Мест нет)", req, state_str)

            elif event_type == "DEPARTURE":
                server.finish_service(time)
                served_count += 1
                self._log_event(time, "Обслужена", req, f"{state_str} -> Осв. приб.{server.id}")

                if self.queue:
                    next_req = self.queue.popleft()
                    dep_time = server.start_service(next_req, time, self.mu)
                    eq.push("DEPARTURE", dep_time, next_req, server)
                    self._log_event(time, "Из очереди на обслуж.", next_req, f"Приб.{server.id}")

            elif event_type == "ABANDON":
                if req.status == "IN_QUEUE":
                    try:
                        self.queue.remove(req)
                        req.status = "ABANDONED"
                        abandoned_count += 1
                        self._log_event(time, "УШЕЛ (Не дождался)", req, f"Оч: {len(self.queue)}/{self.K}")
                    except ValueError:
                        pass  # уже не в очереди

        # Сохранение статистики
        total = len(self.all_requests)
        self.stats["total"] = total
        self.stats["served"] = served_count
        self.stats["rejected"] = rejected_count
        self.stats["abandoned"] = abandoned_count

        # Относительная пропускная способность
        self.stats["Q"] = served_count / total if total > 0 else 0.0

        # Среднее время в очереди (учитываем обслуженных и ушедших)
        total_wait = 0.0
        wait_count = 0
        for r in self.all_requests:
            if r.status == "SERVED":
                total_wait += (r.service_start_time - r.arrival_time)
                wait_count += 1
            elif r.status == "ABANDONED":
                total_wait += r.max_wait_time
                wait_count += 1
        self.stats["Wq"] = total_wait / wait_count if wait_count > 0 else 0.0


# --------------------- Графический интерфейс (Tkinter) ---------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Многомодульная СМО с очередью и нетерпеливыми заявками (ООП)")
        root.geometry("1300x850")
        root.configure(bg="#f0f2f5")

        self.sim = None
        self.setup_ui()

    def setup_ui(self):
        # Левая панель параметров
        control_frame = tk.Frame(self.root, bg="#f8f9fa", relief=tk.RIDGE, bd=2)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(control_frame, text="Параметры моделирования", font=("Segoe UI", 12, "bold"),
                 bg="#f8f9fa").pack(pady=(10, 15))

        params = [
            ("Интенсивность поступления λ", "lambda", 5.0, 0.5, 0.1),
            ("Интенсивность обслуживания μ", "mu", 3.0, 0.5, 0.1),
            ("Количество приборов c", "channels", 2, 1, 1),
            ("Макс. длина очереди K", "queueCap", 10, 1, 0),
            ("Интенсивность ухода γ", "gamma", 1.0, 0.1, 0.0),
            ("Длительность симуляции T", "simDuration", 200, 10, 10)
        ]

        self.entries = {}
        for label_text, key, default, step, min_val in params:
            frame = tk.Frame(control_frame, bg="#f8f9fa")
            frame.pack(fill=tk.X, pady=3)
            tk.Label(frame, text=label_text, font=("Segoe UI", 9), bg="#f8f9fa").pack(anchor=tk.W)
            spinbox = tk.Spinbox(frame, from_=min_val, to=10000, increment=step,
                                 width=12, font=("Segoe UI", 10))
            spinbox.delete(0, tk.END)
            spinbox.insert(0, str(default))
            spinbox.pack(fill=tk.X)
            self.entries[key] = spinbox

        btn_frame = tk.Frame(control_frame, bg="#f8f9fa")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Запустить симуляцию", bg="#007bff", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.run_simulation).pack(fill=tk.X, pady=3)
        tk.Button(btn_frame, text="Сброс", bg="#6c757d", fg="white",
                  font=("Segoe UI", 10, "bold"), command=self.reset_ui).pack(fill=tk.X)

        theory = ("Правила (усложнения):\n"
                  "1. Ограниченная очередь (K мест).\n"
                  "2. Нетерпеливые заявки (γ).\n"
                  "При γ = 0 заявки ждут до победного.")
        tk.Message(control_frame, text=theory, bg="#e9ecef", font=("Segoe UI", 9),
                   width=260).pack(pady=15)

        # Правая часть – результаты
        result_frame = tk.Frame(self.root, bg="white")
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Сводка
        summary_frame = tk.LabelFrame(result_frame, text="Результаты", font=("Segoe UI", 11, "bold"),
                                      bg="white", padx=10, pady=5)
        summary_frame.pack(fill=tk.X, pady=5)

        self.summary_vars = {}
        labels = [
            ("Всего заявок:", "resTotal"),
            ("Обслужено:", "resServed"),
            ("Отказов (нет мест):", "resRejected"),
            ("Ушло (не дождались):", "resAbandoned"),
            ("Отн. пропускная способность:", "resQ"),
            ("Среднее время в очереди:", "resWq")
        ]
        for i, (text, key) in enumerate(labels):
            tk.Label(summary_frame, text=text, font=("Segoe UI", 10), bg="white").grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5, pady=2)
            var = tk.StringVar(value="-")
            self.summary_vars[key] = var
            tk.Label(summary_frame, textvariable=var, font=("Segoe UI", 10, "bold"),
                     bg="white").grid(row=i//3, column=(i%3)*2+1, sticky=tk.W, padx=5, pady=2)

        # Таблица событий
        table_frame = tk.LabelFrame(result_frame, text="Динамика состояний (первые 30 событий)",
                                    font=("Segoe UI", 11, "bold"), bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("time", "type", "req", "state")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree.heading("time", text="Время")
        self.tree.heading("type", text="Тип события")
        self.tree.heading("req", text="Заявка")
        self.tree.heading("state", text="Состояние (Приборы / Очередь)")
        self.tree.column("time", width=80, anchor=tk.CENTER)
        self.tree.column("type", width=160, anchor=tk.CENTER)
        self.tree.column("req", width=70, anchor=tk.CENTER)
        self.tree.column("state", width=300, anchor=tk.W)
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # График
        chart_frame = tk.LabelFrame(result_frame, text="Итоги по заявкам", font=("Segoe UI", 11, "bold"),
                                    bg="white")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Вывод (заключение)
        conclusion_frame = tk.LabelFrame(result_frame, text="Вывод", font=("Segoe UI", 11, "bold"), bg="white")
        conclusion_frame.pack(fill=tk.X, pady=5)
        self.conclusion_text = tk.StringVar(value="Запустите симуляцию, чтобы получить результаты.")
        tk.Label(conclusion_frame, textvariable=self.conclusion_text, font=("Segoe UI", 10),
                 bg="#d4edda", wraplength=700, justify=tk.LEFT, padx=10, pady=5).pack(fill=tk.X)

    def read_params(self):
        try:
            p = {}
            p["lambda"] = float(self.entries["lambda"].get())
            p["mu"] = float(self.entries["mu"].get())
            p["channels"] = int(self.entries["channels"].get())
            p["queueCap"] = int(self.entries["queueCap"].get())
            p["gamma"] = float(self.entries["gamma"].get())
            p["simDuration"] = float(self.entries["simDuration"].get())
            if p["lambda"] <= 0 or p["mu"] <= 0 or p["channels"] <= 0 or p["queueCap"] < 0 or p["gamma"] < 0 or p["simDuration"] <= 0:
                raise ValueError("Все параметры должны быть положительными (очередь >= 0).")
            return p
        except Exception as e:
            messagebox.showerror("Ошибка ввода", f"Некорректные параметры:\n{e}")
            return None

    def run_simulation(self):
        params = self.read_params()
        if params is None:
            return

        # Создаём объект симуляции и запускаем
        self.sim = Simulation(
            lambda_=params["lambda"],
            mu=params["mu"],
            c=params["channels"],
            K=params["queueCap"],
            gamma=params["gamma"],
            T=params["simDuration"]
        )
        self.sim.run()

        # Обновляем UI
        self.update_results()

    def update_results(self):
        s = self.sim.stats
        self.summary_vars["resTotal"].set(str(s["total"]))
        self.summary_vars["resServed"].set(str(s["served"]))
        self.summary_vars["resRejected"].set(str(s["rejected"]))
        self.summary_vars["resAbandoned"].set(str(s["abandoned"]))
        self.summary_vars["resQ"].set(f"{s['Q']:.4f}")
        self.summary_vars["resWq"].set(f"{s['Wq']:.4f}")

        # Таблица событий
        self.tree.delete(*self.tree.get_children())
        for ev in self.sim.event_log:
            self.tree.insert("", tk.END, values=(f"{ev[0]:.4f}", ev[1], f"№{ev[2]}", ev[3]))
        if len(self.sim.event_log) == 30:
            self.tree.insert("", tk.END, values=("...", "...", "...", "(остальные скрыты)"))

        # Круговая диаграмма
        remaining = s["total"] - s["served"] - s["rejected"] - s["abandoned"]
        self.ax.clear()
        labels = ['Обслужены', 'Отклонены (нет мест)', 'Ушли (не дождались)', 'Зависли (в конце)']
        sizes = [s["served"], s["rejected"], s["abandoned"], max(0, remaining)]
        colors = ['#28a745', '#dc3545', '#ffc107', '#6c757d']
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        self.ax.axis('equal')
        self.figure.tight_layout()
        self.canvas.draw()

        # Вывод
        pct_served = (s["served"] / max(1, s["total"]) * 100)
        pct_abandon = (s["abandoned"] / max(1, s["total"]) * 100)
        text = (f"Моделирование M/M/{self.sim.c}/{self.sim.K} успешно завершено.\n"
                f"При данных параметрах успешно обслужено {pct_served:.1f}% заявок.\n"
                f"Доля ушедших от нетерпеливости: {pct_abandon:.1f}%.")
        self.conclusion_text.set(text)

    def reset_ui(self):
        for var in self.summary_vars.values():
            var.set("-")
        self.tree.delete(*self.tree.get_children())
        self.ax.clear()
        self.canvas.draw()
        self.conclusion_text.set("Запустите симуляцию, чтобы получить результаты.")


# --------------------- Точка входа ---------------------
if __name__ == "__main__":
    random.seed()  # можно задать random.seed(42) для воспроизводимости
    root = tk.Tk()
    app = App(root)
    root.mainloop()