import tkinter as tk
from tkinter import ttk, messagebox

# 1. Собственный LCG генератор 
class CustomRNG:
    def __init__(self, seed: int):
        self.mod = 2147483647
        self.mult = 16807
        self.state = seed % self.mod
        if self.state == 0:
            self.state = 1

    def next(self) -> float:
        self.state = (self.mult * self.state) % self.mod
        return self.state / self.mod

rng = CustomRNG(12345)

def get_random() -> float:
    return rng.next()

def reset_rng(seed: int):
    global rng
    rng = CustomRNG(seed)

# 2. Список ответов 
answer_texts = [
    "Бесспорно", "Предрешено", "Никаких сомнений", "Определённо да",
    "Можешь быть уверен в этом", "Вероятнее всего", "Хорошие перспективы",
    "Знаки говорят — да", "Да", "Пока не ясно, попробуй снова", "Спроси позже",
    "Лучше не рассказывать", "Сейчас нельзя предсказать", "Сконцентрируйся и спроси опять",
    "Не рассчитывай на это", "Мой ответ — нет", "Весьма сомнительно",
    "Перспективы не очень хорошие"
]
answer_types = [
    "positive", "positive", "positive", "positive", "positive", "positive",
    "positive", "positive", "positive", "neutral", "neutral", "neutral",
    "neutral", "neutral", "negative", "negative", "negative", "negative"
]
answers = [{"text": txt, "type": tp} for txt, tp in zip(answer_texts, answer_types)]

# 3. Главное окно с прокруткой 
root = tk.Tk()
root.title("Моделирование случайных событий (собственный ГСЧ)")
root.geometry("950x700")   # Можно менять размер, появится скролл
root.minsize(800, 600)

# Создаём Canvas и вертикальную полосу прокрутки для всего окна
main_canvas = tk.Canvas(root, highlightthickness=0)
scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
main_canvas.configure(yscrollcommand=scrollbar.set)

# Упаковываем canvas и scrollbar
main_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Фрейм, который будет прокручиваться (все виджеты размещаем внутри него)
scrollable_frame = ttk.Frame(main_canvas)
scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

# Помещаем фрейм в canvas
canvas_window = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=main_canvas.winfo_width())

# При изменении размера canvas подстраиваем ширину фрейма
def configure_frame_width(event):
    main_canvas.itemconfig(canvas_window, width=event.width)

main_canvas.bind("<Configure>", configure_frame_width)

# Прокрутка колесиком мыши
def _on_mousewheel(event):
    main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

main_canvas.bind("<MouseWheel>", _on_mousewheel)

# 4. ВСЁ ОСТАЛЬНОЕ СОДЕРЖИМОЕ помещаем в scrollable_frame 
main_frame = scrollable_frame  
parent = main_frame

# Добавим отступы для всего содержимого
container = ttk.Frame(parent, padding="10")
container.pack(fill=tk.BOTH, expand=True)

# 5. Настройка ГСЧ 
settings_frame = ttk.LabelFrame(container, text="Настройка генератора (LCG)", padding="10")
settings_frame.pack(fill=tk.X, pady=(0, 15))

ttk.Label(settings_frame, text="Зерно (seed):").grid(row=0, column=0, sticky="w", padx=(0, 10))
seed_var = tk.StringVar(value="12345")
seed_entry = ttk.Entry(settings_frame, textvariable=seed_var, width=15)
seed_entry.grid(row=0, column=1, sticky="w", padx=(0, 15))
# seed
def on_reset_seed():
    try:
        new_seed = int(seed_var.get())
        if new_seed <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Зерно должно быть положительным целым числом")
        return
    reset_rng(new_seed)
    yes_no_result_var.set("—")
    magic_result_var.set("Нажмите «Спросить»")
    magic_result_color("black")
    messagebox.showinfo("ГСЧ сброшен", f"Генератор сброшен с зерном {new_seed}")

reset_seed_btn = ttk.Button(settings_frame, text="Сбросить ГСЧ", command=on_reset_seed)
reset_seed_btn.grid(row=0, column=2, sticky="w")

# 6. Часть 1: Скажи "да" или "нет" 
part1_frame = ttk.LabelFrame(container, text="🎲 Скажи «да» или «нет»", padding="10")
part1_frame.pack(fill=tk.X, pady=(0, 20))

ttk.Label(part1_frame, text="Вероятность «Да» (0..1):").grid(row=0, column=0, sticky="w", padx=(0, 10))
prob_yes_var = tk.DoubleVar(value=0.5)
prob_yes_spin = ttk.Spinbox(part1_frame, from_=0.0, to=1.0, increment=0.01,
                            textvariable=prob_yes_var, width=10)
prob_yes_spin.grid(row=0, column=1, sticky="w")

yes_no_result_var = tk.StringVar(value="—")
result_label1 = ttk.Label(part1_frame, textvariable=yes_no_result_var,
                          font=("Segoe UI", 20, "bold"), foreground="green")
result_label1.grid(row=2, column=0, columnspan=2, pady=(10, 0))
# probability
def on_yes_no():
    prob = prob_yes_var.get()
    if not (0 <= prob <= 1):
        messagebox.showerror("Ошибка", "Вероятность должна быть в диапазоне [0, 1]")
        return
    rand = get_random()
    answer = "Да" if rand < prob else "Нет"
    yes_no_result_var.set(answer)

yes_no_btn = ttk.Button(part1_frame, text="Получить ответ", command=on_yes_no)
yes_no_btn.grid(row=1, column=0, columnspan=2, pady=5)

# 7. Часть 2: Шар предсказаний 
part2_frame = ttk.LabelFrame(container, text="🔮 Шар предсказаний (Magic 8‑Ball) – индивидуальные вероятности", padding="10")
part2_frame.pack(fill=tk.BOTH, expand=True)

top_q_frame = ttk.Frame(part2_frame)
top_q_frame.pack(fill=tk.X, pady=(0, 10))

ttk.Label(top_q_frame, text="Ваш вопрос:").pack(anchor="w")
question_var = tk.StringVar()
question_entry = ttk.Entry(top_q_frame, textvariable=question_var, width=80)
question_entry.pack(fill=tk.X, pady=(0, 5))

ask_btn = ttk.Button(top_q_frame, text="Спросить")
ask_btn.pack(pady=5)

# Таблица вероятностей с прокруткой (внутренняя)
prob_table_frame = ttk.LabelFrame(part2_frame, text="Вероятности (веса) ответов", padding="5")
prob_table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

canvas_inner = tk.Canvas(prob_table_frame, highlightthickness=0)
scrollbar_inner = ttk.Scrollbar(prob_table_frame, orient="vertical", command=canvas_inner.yview)
scrollable_frame_inner = ttk.Frame(canvas_inner)

scrollable_frame_inner.bind("<Configure>", lambda e: canvas_inner.configure(scrollregion=canvas_inner.bbox("all")))
canvas_inner.create_window((0, 0), window=scrollable_frame_inner, anchor="nw")
canvas_inner.configure(yscrollcommand=scrollbar_inner.set)

canvas_inner.pack(side="left", fill="both", expand=True)
scrollbar_inner.pack(side="right", fill="y")

# Заголовки внутренней таблицы
ttk.Label(scrollable_frame_inner, text="Ответ", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
ttk.Label(scrollable_frame_inner, text="Вес (вероятность)", font=("Segoe UI", 10, "bold")).grid(row=0, column=1, padx=5, pady=5)

weight_vars = []
for i, ans in enumerate(answers):
    row = i + 1
    type_symbol = "🟢" if ans["type"] == "positive" else "🟠" if ans["type"] == "neutral" else "🔴"
    label_text = f"{type_symbol} {ans['text']}"
    ttk.Label(scrollable_frame_inner, text=label_text).grid(row=row, column=0, padx=5, pady=2, sticky="w")
    var = tk.DoubleVar(value=1.0)
    entry = ttk.Entry(scrollable_frame_inner, textvariable=var, width=12)
    entry.grid(row=row, column=1, padx=5, pady=2)
    weight_vars.append(var)

# Кнопки управления весами
btn_frame = ttk.Frame(part2_frame)
btn_frame.pack(fill=tk.X, pady=(0, 10))
# распределение весов
def normalize_weights():
    weights = [v.get() for v in weight_vars]
    total = sum(weights)
    if total == 0:
        for v in weight_vars:
            v.set(1.0)
        weights = [1.0] * len(weight_vars)
        total = len(weight_vars)
    for v, w in zip(weight_vars, weights):
        v.set(w / total)
    messagebox.showinfo("Нормализация", "Вероятности нормализованы (сумма = 1).")

def reset_weights_to_equal():
    for v in weight_vars:
        v.set(1.0)
    normalize_weights()

ttk.Button(btn_frame, text="Нормализовать вероятности", command=normalize_weights).pack(side=tk.LEFT, padx=5)
ttk.Button(btn_frame, text="Сбросить (равные вероятности)", command=reset_weights_to_equal).pack(side=tk.LEFT, padx=5)

# Блок уравнивания остальных
equalize_frame = ttk.Frame(part2_frame)
equalize_frame.pack(fill=tk.X, pady=(0, 10))

ttk.Label(equalize_frame, text="Установить вероятность для одного ответа, остальные сделать равными:").grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))

answer_choice_var = tk.StringVar()
answer_choice_combo = ttk.Combobox(equalize_frame, textvariable=answer_choice_var,
                                   values=[a["text"] for a in answers], state="readonly", width=40)
answer_choice_combo.grid(row=1, column=0, padx=5, pady=5)

ttk.Label(equalize_frame, text="Целевая вероятность:").grid(row=1, column=1, padx=5)
target_prob_var = tk.DoubleVar(value=0.4)
target_prob_spin = ttk.Spinbox(equalize_frame, from_=0.0, to=1.0, increment=0.01,
                               textvariable=target_prob_var, width=8)
target_prob_spin.grid(row=1, column=2, padx=5)
# уравнять остальные
def set_one_and_equalize():
    selected_text = answer_choice_var.get()
    if not selected_text:
        messagebox.showwarning("Выбор ответа", "Пожалуйста, выберите ответ из списка.")
        return
    target = target_prob_var.get()
    if target < 0 or target > 1:
        messagebox.showerror("Ошибка", "Вероятность должна быть от 0 до 1.")
        return
    idx = next(i for i, a in enumerate(answers) if a["text"] == selected_text)
    n = len(answers)
    if n == 1:
        weight_vars[idx].set(1.0)
    else:
        weight_vars[idx].set(target)
        other_weight = (1.0 - target) / (n - 1)
        for i, v in enumerate(weight_vars):
            if i != idx:
                v.set(other_weight)
    normalize_weights()
    messagebox.showinfo("Готово", f"Вероятность '{selected_text}' = {target:.3f}\nОстальные равны {(1-target)/(n-1):.4f} каждый.")

equalize_btn = ttk.Button(equalize_frame, text="Уравнять остальные", command=set_one_and_equalize)
equalize_btn.grid(row=1, column=3, padx=10)

# Область вывода ответа
result_display_frame = ttk.Frame(part2_frame)
result_display_frame.pack(fill=tk.X, pady=(5, 0))

ball_emoji = ttk.Label(result_display_frame, text="🎱", font=("Segoe UI", 32))
ball_emoji.pack(side=tk.LEFT, padx=(0, 15))

magic_result_var = tk.StringVar(value="Нажмите «Спросить»")
result_label2 = ttk.Label(result_display_frame, textvariable=magic_result_var,
                          font=("Segoe UI", 14, "bold"))
result_label2.pack(side=tk.LEFT)

def magic_result_color(color):
    result_label2.config(foreground=color)
# выбор по весам
def get_random_answer_with_weights():
    weights = [v.get() for v in weight_vars]
    total = sum(weights)
    if total == 0:
        probs = [1.0 / len(weights)] * len(weights)
    else:
        probs = [w / total for w in weights]
    rand = get_random()
    cum = 0.0
    for i, p in enumerate(probs):
        cum += p
        if rand < cum:
            return answers[i]
    return answers[-1]

def on_ask():
    question = question_var.get().strip()
    if not question:
        messagebox.showwarning("Нет вопроса", "Пожалуйста, задайте вопрос.")
        return
    if not question.endswith("?"):
        if not messagebox.askyesno("Вопрос без знака", "Ваш вопрос не заканчивается вопросительным знаком. Продолжить?"):
            return
    answer = get_random_answer_with_weights()
    magic_result_var.set(answer["text"])
    if answer["type"] == "positive":
        magic_result_color("#28a745")
    elif answer["type"] == "negative":
        magic_result_color("#dc3545")
    else:
        magic_result_color("#fd7e14")

ask_btn.config(command=on_ask)
question_entry.bind("<Return>", lambda e: on_ask())

# Инициализация равных вероятностей
reset_weights_to_equal()

# Запуск
root.mainloop()