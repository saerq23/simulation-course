import tkinter as tk
from tkinter import ttk, messagebox
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# Таблица χ²(α=0.05, df)
CHI2_95 = {
    1: 3.841,  2: 5.991,  3: 7.815,  4: 9.488,  5: 11.070,
    6: 12.592, 7: 14.067, 8: 15.507, 9: 16.919, 10: 18.307,
    11: 19.675, 12: 21.026, 13: 22.362, 14: 23.685, 15: 24.996,
    16: 26.296, 17: 27.587, 18: 28.869, 19: 30.144, 20: 31.410,
    25: 37.652, 30: 43.773,
}


def chi2_critical(df: int) -> float:
    """Критическое значение χ²(0.05, df). Для df > 30 — приближение Вилсона–Хилферти."""
    if df <= 0:
        return float("inf")
    if df in CHI2_95:
        return CHI2_95[df]
    if df > 30:
        z = 1.959964  # z_{0.975}
        # приближение: χ²_p ≈ df * (1 - 2/(9df) + z*sqrt(2/(9df)))^3
        t = 1 - 2.0 / (9 * df) + z * math.sqrt(2.0 / (9 * df))
        return df * t ** 3
    return 100.0


# LCG
class CustomRNG:
    def __init__(self, seed=12345):
        self.mod = 2147483647
        self.mult = 16807
        self.state = seed % self.mod
        if self.state == 0:
            self.state = 1

    def next(self):
        self.state = (self.mult * self.state) % self.mod
        return self.state / self.mod


#  Дискретная СВ
def generate_discrete_sample(rng, probs, n):
    values = [1, 2, 3, 4, 5]
    cum = []
    s = 0.0
    for p in probs:
        s += p
        cum.append(s)
    if cum[-1] <= 0:
        return [1] * n
    cum = [c / cum[-1] for c in cum]        # нормировка
    sample = []
    for _ in range(n):
        u = rng.next()
        idx = 0
        while idx < len(cum) and u > cum[idx]:
            idx += 1
        if idx >= len(values):
            idx = len(values) - 1
        sample.append(values[idx])
    return sample


def compute_discrete_stats(sample, probs, n):
    freq = [0] * 5
    for v in sample:
        freq[v - 1] += 1
    emp_probs = [f / n for f in freq]

    theor_mean = sum((i + 1) * probs[i] for i in range(5))
    theor_var = sum(((i + 1) - theor_mean) ** 2 * probs[i] for i in range(5))

    emp_mean = sum(sample) / n
    emp_var = sum((x - emp_mean) ** 2 for x in sample) / n

    def rel_err(emp, theor):
        if abs(theor) < 1e-12:
            return None
        return abs(emp - theor) / abs(theor) * 100

    mean_err = rel_err(emp_mean, theor_mean)
    var_err = rel_err(emp_var, theor_var)

    # объединение редких категорий
    merged_freq, merged_prob = [], []
    acc_f, acc_p = 0, 0.0
    for i in range(5):
        acc_f += freq[i]
        acc_p += probs[i]
        if n * acc_p >= 5:
            merged_freq.append(acc_f)
            merged_prob.append(acc_p)
            acc_f, acc_p = 0, 0.0
    if acc_f > 0:
        if merged_freq:
            merged_freq[-1] += acc_f
            merged_prob[-1] += acc_p
        else:
            merged_freq.append(acc_f)
            merged_prob.append(acc_p)

    valid = len(merged_freq) >= 2
    chi2 = 0.0
    if valid:
        for f, p in zip(merged_freq, merged_prob):
            expected = n * p
            if expected < 1e-12:
                valid = False
                break
            chi2 += (f - expected) ** 2 / expected
    if valid:
        df = max(1, len(merged_freq) - 1)
        critical = chi2_critical(df)
        hypothesis = "принимается" if chi2 <= critical else "отвергается"
    else:
        df = 0
        critical = None
        hypothesis = "критерий неприменим"

    return {
        "freq": freq, "emp_probs": emp_probs,
        "emp_mean": emp_mean, "emp_var": emp_var,
        "theor_mean": theor_mean, "theor_var": theor_var,
        "mean_err": mean_err, "var_err": var_err,
        "chi2": chi2, "df": df, "critical": critical,
        "hypothesis": hypothesis, "valid": valid,
        "merged_freq": merged_freq, "merged_prob": merged_prob,
    }


#  Нормальная СВ (Бокс–Мюллер)
def box_muller(rng):
    u1 = rng.next()
    u2 = rng.next()
    while u1 == 0:
        u1 = rng.next()
    while u2 == 0:
        u2 = rng.next()
    z0 = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
    z1 = math.sqrt(-2 * math.log(u1)) * math.sin(2 * math.pi * u2)
    return z0, z1


def generate_normal_sample(rng, mu, sigma, n):
    sample = []
    while len(sample) < n:
        z0, z1 = box_muller(rng)
        sample.append(mu + sigma * z0)
        if len(sample) < n:
            sample.append(mu + sigma * z1)
    return sample[:n]


def normal_cdf(x):
    t = 1 / (1 + 0.2316419 * abs(x))
    d = 0.3989423 * math.exp(-x * x / 2)
    prob = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    return 1 - prob if x > 0 else prob


def normal_pdf(x, mu, sigma):
    return (1 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def compute_normal_stats(sample, mu, sigma, n):
    emp_mean = sum(sample) / n
    emp_var = sum((x - emp_mean) ** 2 for x in sample) / n

    def rel_err(emp, theor):
        if abs(theor) < 1e-12:
            return None
        return abs(emp - theor) / abs(theor) * 100

    mean_err = rel_err(emp_mean, mu)
    var_err = rel_err(emp_var, sigma * sigma)

    k = max(2, int(1 + math.log2(n))) if n > 1 else 5
    min_val, max_val = min(sample), max(sample)
    if max_val - min_val < 1e-12:
        max_val = min_val + 1e-6
    width = (max_val - min_val) / k
    bins = []
    for i in range(k):
        left = min_val + i * width
        right = min_val + (i + 1) * width
        bins.append({"left": left, "right": right, "count": 0, "p": 0.0})

    for v in sample:
        idx = int((v - min_val) / width)
        if idx >= k:
            idx = k - 1
        bins[idx]["count"] += 1

    for b in bins:
        p_left = normal_cdf((b["left"] - mu) / sigma)
        p_right = normal_cdf((b["right"] - mu) / sigma)
        b["p"] = p_right - p_left

    # объединение редких бинов
    merged = []
    acc_c, acc_p = 0, 0.0
    for b in bins:
        acc_c += b["count"]
        acc_p += b["p"]
        if n * acc_p >= 5:
            merged.append({"count": acc_c, "p": acc_p})
            acc_c, acc_p = 0, 0.0
    if acc_c > 0:
        if merged:
            merged[-1]["count"] += acc_c
            merged[-1]["p"] += acc_p
        else:
            merged.append({"count": acc_c, "p": acc_p})

    valid = len(merged) >= 4     # нужно хотя бы df=1
    chi2 = 0.0
    if valid:
        for b in merged:
            expected = n * b["p"]
            if expected < 1e-12:
                valid = False
                break
            chi2 += (b["count"] - expected) ** 2 / expected
    if valid:
        df = max(1, len(merged) - 3)   # 2 параметра (μ, σ) оценены
        critical = chi2_critical(df)
        hypothesis = "принимается" if chi2 <= critical else "отвергается"
    else:
        df = 0
        critical = None
        hypothesis = "критерий неприменим"

    return {
        "bins": bins, "merged": merged,
        "emp_mean": emp_mean, "emp_var": emp_var,
        "mean_err": mean_err, "var_err": var_err,
        "chi2": chi2, "df": df, "critical": critical,
        "hypothesis": hypothesis, "valid": valid,
    }


#  GUI
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №6: Имитационное моделирование")
        self.root.geometry("1150x850")

        self.root.configure(bg="#f0f2f5")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#f0f2f5")
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TLabel", background="#f0f2f5", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.discrete_frame = ttk.Frame(self.notebook)
        self.normal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.discrete_frame, text="Дискретная СВ")
        self.notebook.add(self.normal_frame, text="Нормальная СВ")

        self.build_discrete_tab()
        self.build_normal_tab()

    # Дискретная СВ
    def build_discrete_tab(self):
        f = self.discrete_frame

        top = ttk.Frame(f)
        top.pack(fill="x", padx=10, pady=5)

        param = ttk.LabelFrame(top, text="Параметры", padding=10)
        param.pack(side="left", fill="x", expand=True)

        ttk.Label(param, text="Зерно (seed):").grid(row=0, column=0, sticky="w")
        self.seed_disc = tk.StringVar(value="12345")
        ttk.Entry(param, textvariable=self.seed_disc, width=12).grid(row=0, column=1, padx=5)

        ttk.Label(param, text="Вероятности p1..p5:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        pf = ttk.Frame(param)
        pf.grid(row=1, column=1, columnspan=3, pady=(10, 0))
        self.prob_vars = []
        for i in range(5):
            v = tk.StringVar(value="0.2")
            self.prob_vars.append(v)
            e = ttk.Entry(pf, textvariable=v, width=6)
            e.pack(side="left", padx=2)
        self.sum_label = ttk.Label(param, text="Сумма: 1.0000")
        self.sum_label.grid(row=2, column=1, pady=5, sticky="w")
        for v in self.prob_vars:
            v.trace_add("write", lambda *a: self.update_prob_sum())

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right", padx=10)
        for n in [10, 100, 1000, 10000]:
            ttk.Button(btn_frame, text=f"N = {n}",
                       command=lambda val=n: self.run_discrete(val)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Прогнать все N",
                   command=self.run_discrete_all).pack(side="left", padx=(10, 0))

        # Основная область
        main = ttk.Frame(f)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        left = ttk.LabelFrame(main, text="Частоты и вероятности", padding=5)
        left.pack(side="left", fill="both", expand=True)

        columns = ("val", "theor", "emp", "freq")
        self.disc_tree = ttk.Treeview(left, columns=columns, show="headings", height=5)
        for col, txt in zip(columns, ["Значение", "Теор. вер.", "Эмп. вер.", "Частота"]):
            self.disc_tree.heading(col, text=txt)
            self.disc_tree.column(col, width=90, anchor="center")
        self.disc_tree.pack(fill="both", expand=True)

        right = ttk.LabelFrame(main, text="Гистограмма вероятностей", padding=5)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.fig_disc, self.ax_disc = plt.subplots(figsize=(5, 4))
        self.canvas_disc = FigureCanvasTkAgg(self.fig_disc, master=right)
        self.canvas_disc.get_tk_widget().pack(fill="both", expand=True)

        # Сводная таблица по 4 N (по умолчанию скрыта)
        self.disc_all_frame = ttk.LabelFrame(f, text="Сводка по N = 10, 100, 1000, 10000", padding=5)
        self.disc_all_tree = ttk.Treeview(
            self.disc_all_frame,
            columns=("n", "mean", "mean_err", "var", "var_err",
                     "chi2", "df", "crit", "verdict"),
            show="headings", height=4,
        )
        for col, txt, w in [
            ("n", "N", 60), ("mean", "Среднее", 80), ("mean_err", "Погр. средн., %", 110),
            ("var", "Дисперсия", 90), ("var_err", "Погр. дисп., %", 100),
            ("chi2", "χ²", 80), ("df", "df", 50),
            ("crit", "χ²крит", 80), ("verdict", "Вердикт", 150),
        ]:
            self.disc_all_tree.heading(col, text=txt)
            self.disc_all_tree.column(col, width=w, anchor="center")
        self.disc_all_tree.pack(fill="x")
        # изначально скрыт
        self.disc_all_visible = False

        # Текстовое резюме
        self.disc_summary = tk.Text(f, height=7, font=("Segoe UI", 9), bg="#e9ecef")
        self.disc_summary.pack(fill="x", padx=10, pady=5)

    def update_prob_sum(self):
        try:
            p = [float(v.get()) for v in self.prob_vars]
        except ValueError:
            self.sum_label.config(text="Сумма: ошибка")
            return
        self.sum_label.config(text=f"Сумма: {sum(p):.4f}")

    def get_probs(self):
        try:
            p = [float(v.get()) for v in self.prob_vars]
        except ValueError:
            messagebox.showerror("Ошибка", "Вероятности должны быть числами")
            return None
        if any(x < 0 for x in p):
            messagebox.showerror("Ошибка", "Вероятности не могут быть отрицательными")
            return None
        s = sum(p)
        if s == 0:
            messagebox.showerror("Ошибка", "Сумма вероятностей равна нулю")
            return None
        return [x / s for x in p]

    def _fmt_err(self, err):
        return "н/д" if err is None else f"{err:.2f}%"

    def run_discrete(self, n):
        probs = self.get_probs()
        if probs is None:
            return
        try:
            seed = int(self.seed_disc.get())
        except ValueError:
            seed = 12345

        rng = CustomRNG(seed)
        sample = generate_discrete_sample(rng, probs, n)
        stats = compute_discrete_stats(sample, probs, n)

        # Таблица
        self.disc_tree.delete(*self.disc_tree.get_children())
        for i in range(5):
            self.disc_tree.insert("", "end", values=(
                i + 1, f"{probs[i]:.4f}",
                f"{stats['emp_probs'][i]:.4f}", stats["freq"][i],
            ))

        # График
        self.ax_disc.clear()
        x = [1, 2, 3, 4, 5]
        bars = self.ax_disc.bar(x, stats["emp_probs"], width=0.6,
                                color="skyblue", edgecolor="black")
        self.ax_disc.set_xlabel("Значение")
        self.ax_disc.set_ylabel("Вероятность")
        self.ax_disc.set_title(f"Эмпирические вероятности (N={n})")
        self.ax_disc.grid(axis="y", linestyle="--", alpha=0.7)
        for bar, prob in zip(bars, stats["emp_probs"]):
            h = bar.get_height()
            self.ax_disc.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                              f"{prob:.3f}", ha="center", va="bottom", fontsize=9)
        max_p = max(stats["emp_probs"]) if stats["emp_probs"] else 0.3
        self.ax_disc.set_ylim(0, max_p * 1.25)
        self.canvas_disc.draw()

        # Резюме
        self.disc_summary.delete("1.0", tk.END)
        lines = [
            f"N = {n}",
            f"Среднее: {stats['emp_mean']:.4f} (теор: {stats['theor_mean']:.4f}), "
            f"погр. {self._fmt_err(stats['mean_err'])}",
            f"Дисперсия: {stats['emp_var']:.4f} (теор: {stats['theor_var']:.4f}), "
            f"погр. {self._fmt_err(stats['var_err'])}",
        ]
        if stats["valid"]:
            lines.append(
                f"χ² = {stats['chi2']:.4f}, df = {stats['df']}, "
                f"χ²крит = {stats['critical']:.3f} → гипотеза {stats['hypothesis']}"
            )
        else:
            lines.append("χ²-критерий неприменим (после объединения редких "
                         "категорий ожидаемые частоты < 5 или df = 0)")
        self.disc_summary.insert(tk.END, "\n".join(lines))

    def run_discrete_all(self):
        probs = self.get_probs()
        if probs is None:
            return
        try:
            seed = int(self.seed_disc.get())
        except ValueError:
            seed = 12345

        # Обновляем summary в сводке
        if not self.disc_all_visible:
            self.disc_all_frame.pack(fill="x", padx=10, pady=(0, 5),
                                     before=self.disc_summary)
            self.disc_all_visible = True

        self.disc_all_tree.delete(*self.disc_all_tree.get_children())
        results = []
        for n in [10, 100, 1000, 10000]:
            rng = CustomRNG(seed)  # один и тот же seed — воспроизводимо
            sample = generate_discrete_sample(rng, probs, n)
            st = compute_discrete_stats(sample, probs, n)
            results.append((n, st))

            verdict = st["hypothesis"]
            if not st["valid"]:
                verdict = "критерий неприменим"
            self.disc_all_tree.insert("", "end", values=(
                n,
                f"{st['emp_mean']:.4f}",
                self._fmt_err(st["mean_err"]),
                f"{st['emp_var']:.4f}",
                self._fmt_err(st["var_err"]),
                f"{st['chi2']:.4f}" if st["valid"] else "—",
                st["df"] if st["valid"] else "—",
                f"{st['critical']:.3f}" if st["critical"] else "—",
                verdict,
            ))

        # Вывод
        self.disc_summary.delete("1.0", tk.END)
        self.disc_summary.insert(tk.END, self._build_disc_conclusion(results))

    def _build_disc_conclusion(self, results):
        lines = ["Вывод по дискретной СВ:"]
        # Сравнение относительных погрешностей
        err_means = [r[1]["mean_err"] for r in results if r[1]["mean_err"] is not None]
        err_vars = [r[1]["var_err"] for r in results if r[1]["var_err"] is not None]
        if err_means:
            lines.append(
                f"  • Относительная погрешность среднего: "
                f"от {err_means[0]:.2f}% (N={results[0][0]}) до {err_means[-1]:.2f}% (N={results[-1][0]})."
            )
        if err_vars:
            lines.append(
                f"  • Относительная погрешность дисперсии: "
                f"от {err_vars[0]:.2f}% (N={results[0][0]}) до {err_vars[-1]:.2f}% (N={results[-1][0]})."
            )
        # χ²
        for n, st in results:
            if st["valid"]:
                mark = "✓" if st["hypothesis"] == "принимается" else "✗"
                lines.append(f"  • N={n}: χ²={st['chi2']:.3f} ≤ {st['critical']:.3f} ({mark}), "
                             f"df={st['df']}")
            else:
                lines.append(f"  • N={n}: χ² неприменим (мало данных на категорию)")
        lines.append(
            "  • С ростом N погрешности среднего и дисперсии убывают (~1/√N), "
            "χ²-критерий применим начиная с N, при котором все ожидаемые частоты ≥ 5."
        )
        return "\n".join(lines)

    # Нормальная СВ
    def build_normal_tab(self):
        f = self.normal_frame

        top = ttk.Frame(f)
        top.pack(fill="x", padx=10, pady=5)

        param = ttk.LabelFrame(top, text="Параметры", padding=10)
        param.pack(side="left", fill="x", expand=True)

        ttk.Label(param, text="Зерно (seed):").grid(row=0, column=0, sticky="w")
        self.seed_norm = tk.StringVar(value="12345")
        ttk.Entry(param, textvariable=self.seed_norm, width=12).grid(row=0, column=1, padx=5)

        ttk.Label(param, text="Среднее μ:").grid(row=1, column=0, sticky="w")
        self.mu_var = tk.StringVar(value="0.0")
        ttk.Entry(param, textvariable=self.mu_var, width=12).grid(row=1, column=1, padx=5)

        ttk.Label(param, text="Дисперсия σ²:").grid(row=2, column=0, sticky="w")
        self.sigma2_var = tk.StringVar(value="1.0")
        ttk.Entry(param, textvariable=self.sigma2_var, width=12).grid(row=2, column=1, padx=5)

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right", padx=10)
        for n in [10, 100, 1000, 10000]:
            ttk.Button(btn_frame, text=f"N = {n}",
                       command=lambda val=n: self.run_normal(val)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Прогнать все N",
                   command=self.run_normal_all).pack(side="left", padx=(10, 0))

        chart_frame = ttk.LabelFrame(f, text="Гистограмма и теоретическая плотность", padding=10)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.fig_norm, self.ax_norm = plt.subplots(figsize=(8, 4))
        self.canvas_norm = FigureCanvasTkAgg(self.fig_norm, master=chart_frame)
        self.canvas_norm.get_tk_widget().pack(fill="both", expand=True)

        # Сводная таблица
        self.norm_all_frame = ttk.LabelFrame(f, text="Сводка по N = 10, 100, 1000, 10000", padding=5)
        self.norm_all_tree = ttk.Treeview(
            self.norm_all_frame,
            columns=("n", "mean", "mean_err", "var", "var_err",
                     "chi2", "df", "crit", "verdict"),
            show="headings", height=4,
        )
        for col, txt, w in [
            ("n", "N", 60), ("mean", "Среднее", 80), ("mean_err", "Погр. средн., %", 110),
            ("var", "Дисперсия", 90), ("var_err", "Погр. дисп., %", 100),
            ("chi2", "χ²", 80), ("df", "df", 50),
            ("crit", "χ²крит", 80), ("verdict", "Вердикт", 150),
        ]:
            self.norm_all_tree.heading(col, text=txt)
            self.norm_all_tree.column(col, width=w, anchor="center")
        self.norm_all_tree.pack(fill="x")
        self.norm_all_visible = False

        self.norm_summary = tk.Text(f, height=7, font=("Segoe UI", 9), bg="#e9ecef")
        self.norm_summary.pack(fill="x", padx=10, pady=5)

    def run_normal(self, n):
        try:
            seed = int(self.seed_norm.get())
            mu = float(self.mu_var.get())
            sigma2 = float(self.sigma2_var.get())
            if sigma2 <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные параметры (μ, σ² > 0, seed целое)")
            return

        sigma = math.sqrt(sigma2)
        rng = CustomRNG(seed)
        sample = generate_normal_sample(rng, mu, sigma, n)
        stats = compute_normal_stats(sample, mu, sigma, n)

        self.ax_norm.clear()
        bins = stats["bins"]
        x_centers = [(b["left"] + b["right"]) / 2 for b in bins]
        widths = [b["right"] - b["left"] for b in bins]
        self.ax_norm.bar(x_centers, [b["count"] for b in bins], width=widths,
                         color="skyblue", edgecolor="black", alpha=0.75,
                         label="Эмпирическая частота")

        # Теоретическая кривая (плотность, масштабированная под частоты)
        x_min = bins[0]["left"]
        x_max = bins[-1]["right"]
        avg_w = sum(widths) / len(widths) if widths else 1
        xs = []
        ys = []
        step = (x_max - x_min) / 200
        x = x_min
        while x <= x_max:
            xs.append(x)
            ys.append(normal_pdf(x, mu, sigma) * avg_w * n)
            x += step
        self.ax_norm.plot(xs, ys, "r-", linewidth=2, label="Теоретическая плотность")
        self.ax_norm.set_xlabel("Значение")
        self.ax_norm.set_ylabel("Частота")
        self.ax_norm.set_title(f"Нормальное распределение (N={n})")
        self.ax_norm.legend()
        self.ax_norm.grid(True, linestyle="--", alpha=0.5)
        self.fig_norm.tight_layout()
        self.canvas_norm.draw()

        # Резюме
        self.norm_summary.delete("1.0", tk.END)
        lines = [
            f"N = {n}",
            f"Среднее: {stats['emp_mean']:.4f} (теор: {mu:.4f}), "
            f"погр. {self._fmt_err(stats['mean_err'])}",
            f"Дисперсия: {stats['emp_var']:.4f} (теор: {sigma2:.4f}), "
            f"погр. {self._fmt_err(stats['var_err'])}",
        ]
        if stats["valid"]:
            lines.append(
                f"χ² = {stats['chi2']:.4f}, df = {stats['df']}, "
                f"χ²крит = {stats['critical']:.3f} → гипотеза {stats['hypothesis']}"
            )
        else:
            lines.append("χ²-критерий неприменим (после объединения редких "
                         "бинов ожидаемые частоты < 5 или df = 0)")
        self.norm_summary.insert(tk.END, "\n".join(lines))

    def run_normal_all(self):
        try:
            seed = int(self.seed_norm.get())
            mu = float(self.mu_var.get())
            sigma2 = float(self.sigma2_var.get())
            if sigma2 <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректные параметры (μ, σ² > 0, seed целое)")
            return
        sigma = math.sqrt(sigma2)

        if not self.norm_all_visible:
            self.norm_all_frame.pack(fill="x", padx=10, pady=(0, 5), before=self.norm_summary)
            self.norm_all_visible = True

        self.norm_all_tree.delete(*self.norm_all_tree.get_children())
        results = []
        for n in [10, 100, 1000, 10000]:
            rng = CustomRNG(seed)
            sample = generate_normal_sample(rng, mu, sigma, n)
            st = compute_normal_stats(sample, mu, sigma, n)
            results.append((n, st))
            verdict = st["hypothesis"] if st["valid"] else "критерий неприменим"
            self.norm_all_tree.insert("", "end", values=(
                n,
                f"{st['emp_mean']:.4f}",
                self._fmt_err(st["mean_err"]),
                f"{st['emp_var']:.4f}",
                self._fmt_err(st["var_err"]),
                f"{st['chi2']:.4f}" if st["valid"] else "—",
                st["df"] if st["valid"] else "—",
                f"{st['critical']:.3f}" if st["critical"] else "—",
                verdict,
            ))

        self.norm_summary.delete("1.0", tk.END)
        self.norm_summary.insert(tk.END, self._build_norm_conclusion(results))

    def _build_norm_conclusion(self, results):
        lines = ["Вывод по нормальной СВ:"]
        err_means = [r[1]["mean_err"] for r in results if r[1]["mean_err"] is not None]
        err_vars = [r[1]["var_err"] for r in results if r[1]["var_err"] is not None]
        if err_means:
            lines.append(
                f"  • Погрешность среднего: {err_means[0]:.2f}% (N={results[0][0]}) → "
                f"{err_means[-1]:.2f}% (N={results[-1][0]})."
            )
        if err_vars:
            lines.append(
                f"  • Погрешность дисперсии: {err_vars[0]:.2f}% (N={results[0][0]}) → "
                f"{err_vars[-1]:.2f}% (N={results[-1][0]})."
            )
        for n, st in results:
            if st["valid"]:
                mark = "✓" if st["hypothesis"] == "принимается" else "✗"
                lines.append(f"  • N={n}: χ²={st['chi2']:.3f} ≤ {st['critical']:.3f} ({mark}), "
                             f"df={st['df']}")
            else:
                lines.append(f"  • N={n}: χ² неприменим (мало данных)")
        lines.append(
            "  • Метод Бокса–Мюллера даёт нормальную выборку; с ростом N гистограмма "
            "приближается к теоретической плотности, а погрешности оценок убывают как 1/√N."
        )
        return "\n".join(lines)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()