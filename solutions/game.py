import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter


def convolve2d(grid, kernel):
    """
    Реализация 2D свертки с использованием NumPy (без циклов).
    
    grid: квадратная матрица (np.array)
    kernel: 3x3 ядро, например [[1,1,1],[1,0,1],[1,1,1]]
    
    Возвращает:
        result: матрица, где каждый элемент — сумма соседей с учётом ядра
    """
    result = np.zeros_like(grid)
    size = grid.shape[0]
    
    # Проходим по смещениям ядра
    for i in range(-1, 2):
        for j in range(-1, 2):
            if kernel[i+1, j+1] == 0:
                continue
            # Смещаем массив с wrap-around
            result += np.roll(np.roll(grid, i, axis=0), j, axis=1)
    
    return result



class GameOfLife:
    def __init__(self, size: int = 50, p: float = 0.2):
        self.size = size
        self.p = p
        self.grid = np.random.choice([0, 1], size=(size, size), p=[p, 1 - p])  # Инициализируем начальную позицию

    def count_neighbors(self, grid):
        """Подсчет количества живых соседей для каждой клетки"""
        kernel = np.array([[1, 1, 1],
                          [1, 0, 1],
                          [1, 1, 1]])
        return convolve2d(grid, kernel)
    
    def update(self):
        """Обновление состояния игры по правилам"""
        neighbors = self.count_neighbors(self.grid)
        
        # Правила игры:
        # 1. Живая клетка с 2 или 3 соседями выживает
        # 2. Мертвая клетка с 3 соседями оживает
        # 3. Остальные умирают или остаются мертвыми
        
        birth = (self.grid == 0) & (neighbors == 3)
        survive = (self.grid == 1) & ((neighbors == 2) | (neighbors == 3))
        
        self.grid = np.where(birth | survive, 1, 0)
        return self.grid

def animate(step):
    grid = game.update()
    img.set_data(grid)
    return [img]


if __name__ == "__main__":
    size = 100
    frames = 100
    game = GameOfLife(size=size, p=0.5)

    fig, ax = plt.subplots()
    img = plt.imshow(game.grid, cmap="binary")
    ax.axis("off")

    anim = FuncAnimation(fig, animate, frames=frames, interval=100)

    writer = PillowWriter(fps=5)
    anim.save("game_of_life.gif", writer=writer)
