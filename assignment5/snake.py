import struct

import pygame
import random

pygame.init()


class Snake:
    # pos = (x, y), where x is the col offset, and y is the row offset.
    def __init__(self, pos, rows, cols):
        self.rows, self.cols = rows, cols
        self.body = [pos]
        self.dx, self.dy = 0, 1

    def _update_dir(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]: self.dx, self.dy = 1, 0
        if keys[pygame.K_LEFT]: self.dx, self.dy = -1, 0
        if keys[pygame.K_UP]: self.dx, self.dy = 0, -1
        if keys[pygame.K_DOWN]: self.dx, self.dy = 0, 1

    # Return true if move is okay, false otherwise.
    def move(self, apple):
        self._update_dir()
        x, y = self.body[0]
        nx, ny = (x + self.dx) % 32, (y + self.dy) % 32
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
        if self.game_over: return
        if not self.snake.move(apple):
            self.game_over = True
            return
        if self.snake.head() == apple:
            while apple in self.snake.body:
                apple = self._choose_random_pos()

    def get_bitmap(self):
        return self.snake.snake_to_bitmap()

    def get_head(self):
        return self.snake.head()

    def get_body(self):
        return self.snake.body


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
