import struct
from config import *
import pygame
import random

pygame.init()


class Snake:
    # pos = (x, y), where x is the col offset, and y is the row offset.
    def __init__(self, pos, rows, cols):
        self.rows, self.cols = rows, cols
        self.body = [pos]
        self.dx, self.dy = 0, 1

    # move the snake once
    def move(self, apple):
        x, y = self.body[0]
        nx, ny = (x + self.dx) % ROWS, (y + self.dy) % COLUMNS
        """nx, ny = (x + self.dx), (y + self.dy)
        if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
            return False"""
        if (nx, ny) in self.body:
            return False
        self.body.insert(0, (nx, ny))
        if not (nx, ny) == apple:
            self.body.pop()
        return True

    # Return the head of the snake.
    def head(self):
        return self.body[0]

    def set_y(self, bit_num, y):
        y_shift = 1 << 31
        bit_num |= (y_shift >> y)
        return bit_num

    def snake_to_bitmap(self):
        bitmap = [0 for _ in range(32)]
        for x, y in self.body:
            bitmap[x] = self.set_y(bitmap[x], y)
        result = b""
        for number in bitmap:
            result += struct.pack("!I", number)
        return result


class SnakeApp:
    def __init__(self, snake_color):
        self.rows, self.cols = 32, 32
        self.snake_size = 20
        snake_start_pos = self._choose_random_pos()
        self.snake = Snake(snake_start_pos, self.rows, self.cols)
        self.game_over = False
        self.snake_color = snake_color

    def _choose_random_pos(self):
        x = random.randrange(self.cols)
        y = random.randrange(self.rows)
        return x, y

    def run_once(self, apple):
        if self.game_over:
            return False  # unable to run once
        else:
            status = self.snake.move(apple)
            if not status:
                self.game_over = True

    def get_bitmap(self):
        return self.snake.snake_to_bitmap()

    def get_head(self):
        return self.snake.head()

    def get_body(self):
        return self.snake.body

    def change_direction(self, dx, dy):
        self.snake.dx = dx
        self.snake.dy = dy


"""
if __name__ == "__main__":
    clock = pygame.time.Clock()
    FPS = 10  # frames-per-second
    game = SnakeApp(GREEN)
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        # game.run_once()
"""
