import tkinter as tk
import random

# ПАРАМЕТРЫ СЕТКИ
CELL_SIZE = 10
ROWS = 60
COLS = 80
UPDATE_DELAY = 100  # мс

# СОСТОЯНИЯ
EMPTY = 0
TREE = 1
BURNING = 2
ASH = 3

# Типы леса
NORMAL = 1
DENSE = 2
WET = 3


class ForestFire:
    def __init__(self, root):
        self.root = root
        self.running = False

        self.canvas = tk.Canvas(
            root,
            width=COLS * CELL_SIZE,
            height=ROWS * CELL_SIZE,
            bg="white"
        )
        self.canvas.grid(row=0, column=0, rowspan=10)

        # Панель управления
        self.create_controls()

        self.reset()

    # GUI
    def create_controls(self):
        tk.Button(self.root, text="Старт", command=self.start).grid(row=0, column=1)
        tk.Button(self.root, text="Пауза", command=self.pause).grid(row=1, column=1)
        tk.Button(self.root, text="Сброс", command=self.reset).grid(row=2, column=1)

        tk.Label(self.root, text="Влажность").grid(row=3, column=1)
        self.humidity = tk.Scale(self.root, from_=0, to=100, orient="horizontal")
        self.humidity.set(30)
        self.humidity.grid(row=4, column=1)

        tk.Label(self.root, text="Вероятность молнии").grid(row=5, column=1)
        self.lightning = tk.Scale(self.root, from_=0, to=100, orient="horizontal")
        self.lightning.set(1)
        self.lightning.grid(row=6, column=1)

        tk.Label(self.root, text="Рост деревьев").grid(row=7, column=1)
        self.growth = tk.Scale(self.root, from_=0, to=100, orient="horizontal")
        self.growth.set(2)
        self.growth.grid(row=8, column=1)

        tk.Label(self.root, text="Направление ветра").grid(row=9, column=1)
        self.wind_dir = tk.StringVar(value="None")
        wind_menu = tk.OptionMenu(self.root, self.wind_dir,
                                  "None", "N", "S", "E", "W")
        wind_menu.grid(row=10, column=1)

        tk.Label(self.root, text="Сила ветра").grid(row=11, column=1)
        self.wind_strength = tk.Scale(self.root, from_=1, to=3,
                                      orient="horizontal")
        self.wind_strength.set(1)
        self.wind_strength.grid(row=12, column=1)

    # ИНИЦИАЛИЗАЦИЯ
    def reset(self): # сброс
        self.running = False
        self.grid = [[self.random_tree() for _ in range(COLS)]
                     for _ in range(ROWS)]
        self.draw()

    def random_tree(self):
        r = random.random()
        if r < 0.6:
            return (TREE, NORMAL)
        elif r < 0.75:
            return (TREE, DENSE)
        elif r < 0.9:
            return (TREE, WET)
        else:
            return (EMPTY, None)

    # ЗАПУСК
    def start(self): # запуск
        if not self.running:
            self.running = True
            self.update()

    def pause(self):
        self.running = False

    # ЛОГИКА ОБНОВЛЕНИЯ
    def update(self):
        if not self.running:
            return

        new_grid = [[(EMPTY, None) for _ in range(COLS)]
                    for _ in range(ROWS)]

        for i in range(ROWS):
            for j in range(COLS):
                state, tree_type = self.grid[i][j]

                if state == EMPTY:
                    # Рост дерева
                    if random.random() < self.growth.get() / 1000:
                        new_grid[i][j] = (TREE, NORMAL)
                    else:
                        new_grid[i][j] = (EMPTY, None)

                elif state == TREE:
                    if self.is_burning_neighbor(i, j):
                        if random.random() < self.fire_probability(tree_type, i, j):
                            new_grid[i][j] = (BURNING, tree_type)
                        else:
                            new_grid[i][j] = (TREE, tree_type)
                    elif random.random() < self.lightning.get() / 10000:
                        new_grid[i][j] = (BURNING, tree_type)
                    else:
                        new_grid[i][j] = (TREE, tree_type)

                elif state == BURNING:
                    new_grid[i][j] = (ASH, None)

                elif state == ASH:
                    new_grid[i][j] = (EMPTY, None)

        self.grid = new_grid
        self.draw()
        self.root.after(UPDATE_DELAY, self.update)

    # ПРОВЕРКА СОСЕДЕЙ
    def is_burning_neighbor(self, x, y):
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < ROWS and 0 <= ny < COLS:
                    if self.grid[nx][ny][0] == BURNING:
                        return True
        return False

    def fire_probability(self, tree_type, x, y):
        base = 0.3 # вероятность горения

        # Тип леса
        if tree_type == DENSE:
            base = 0.6
        elif tree_type == WET:
            base = 0.15

        # Влажность
        humidity_factor = 1 - self.humidity.get() / 100
        base *= humidity_factor

        # Ветер
        wind = self.wind_dir.get()
        strength = self.wind_strength.get()

        if wind != "None":
            if wind == "N" and x > 0 and self.grid[x - 1][y][0] == BURNING:
                base *= strength
            elif wind == "S" and x < ROWS - 1 and self.grid[x + 1][y][0] == BURNING:
                base *= strength
            elif wind == "W" and y > 0 and self.grid[x][y - 1][0] == BURNING:
                base *= strength
            elif wind == "E" and y < COLS - 1 and self.grid[x][y + 1][0] == BURNING:
                base *= strength

        return min(base, 1)

    # ОТРИСОВКА
    def draw(self):
        self.canvas.delete("all")
        for i in range(ROWS):
            for j in range(COLS):
                state, tree_type = self.grid[i][j]
                x1 = j * CELL_SIZE # лево
                y1 = i * CELL_SIZE # вверх
                x2 = x1 + CELL_SIZE # право
                y2 = y1 + CELL_SIZE # низ

                color = "white"

                if state == TREE:
                    if tree_type == NORMAL:
                        color = "green"
                    elif tree_type == DENSE:
                        color = "darkgreen"
                    elif tree_type == WET:
                        color = "lightgreen"

                elif state == BURNING:
                    color = "red"

                elif state == ASH:
                    color = "gray"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=""
                )


# ЗАПУСК
root = tk.Tk()
root.title("Моделирование лесного пожара")
app = ForestFire(root)
root.mainloop()