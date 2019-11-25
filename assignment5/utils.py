import random
import struct
import time
from config import *
from snake import SnakeApp


def get_current_time():
    return time.time()


def choose_random_pos():
    x = random.randrange(ROWS)
    y = random.randrange(COLUMNS)
    return x, y


class Player:
    def __init__(self, game_id, nick_name, port_number, ip_address, color):
        self.game_id = game_id
        self.nick_name = nick_name
        self.port_number = port_number
        self.ip_address = ip_address
        self.snake_app = SnakeApp(color)
        self.result = None
        self.winner = ""


class GameStatus:
    def __init__(self, game_status):
        self.game_status = game_status
        self.result = None
        self.winner = ""


def bitmap_to_snake(bitmap):
    body = []
    print(bitmap, len(bitmap))
    for i in range(ROWS):
        number = struct.unpack("!I", bitmap[i * 4: (i + 1) * 4])[0]
        binary_number = bin(number)[2:]
        # print("binary number is", binary_number)
        offset = COLUMNS - len(binary_number)
        for j in range(len(binary_number)):
            if binary_number[j] == '1':
                body.append((i, j + offset))
    return body


def is_game_ended(head_1, head_2, body_1, body_2):
    # if one of the snake is out of bound
    if out_of_bound(head_1):
        return True, 2
    if out_of_bound(head_2):
        return True, 1
    # if head positions are the same
    if head_1 == head_2:  # draw game
        return True, None
    if head_1 in body_1[1:] or head_1 in body_2[1:]:
        return True, 2
    if head_2 in body_2[1:] or head_2 in body_1[1:]:
        return True, 1
    return False, None


def out_of_bound(pair):
    x, y = pair
    if x < 0 or x >= COLUMNS or y < 0 or y >= ROWS:
        return True
    return False
