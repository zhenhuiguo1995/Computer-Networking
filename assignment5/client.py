import sys
import threading

import pygame
import socket
from utils import *
import struct
from config import *

pygame.init()


class Client:
    def __init__(self, game_id, nick_name, port_number, color):
        self.game_id = game_id  # str
        self.nick_name = nick_name  # str
        self.port_number = port_number  # integer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.game_over = False
        self.color = color
        self.dx, self.dy = 0, 1
        self.rows, self.cols = ROWS, COLUMNS
        self.snake_size = 20
        self.surface = pygame.display.set_mode((self.cols * self.snake_size, self.rows * self.snake_size))
        self.winner = ""
        self.DIRECTION_MAP = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}

    def show_message_on_board(self, msg):
        pygame.display.flip()
        pygame.display.set_caption('Snake Game')
        self.surface.fill(WHITE)
        assert pygame.font.get_init()
        font = pygame.font.Font(None, 60)
        text = font.render(msg, True, BLUE)
        text_rect = text.get_rect()
        text_x = self.surface.get_width() / 2 - text_rect.width / 2
        text_y = self.surface.get_height() / 2 - text_rect.height / 2
        self.surface.blit(text, [text_x, text_y])
        pygame.display.flip()

    def send_message(self, msg):
        self.socket.sendto(msg, (UDP_IP, UDP_PORT))

    def pack_message(self, type_of_message):
        message = struct.pack("!BBB%ds%dsH" % (len(self.game_id), len(self.nick_name)),
                              type_of_message, len(self.game_id), len(self.nick_name),
                              self.game_id.encode(), self.nick_name.encode(), self.port_number)
        self.send_message(message)

    def send_change_direction_message(self, dir):
        message = struct.pack("!BBB%ds%dsB" % (len(self.game_id), len(self.nick_name)),
                              3, len(self.game_id), len(self.nick_name),
                              self.game_id.encode(), self.nick_name.encode(), dir)
        self.send_message(message)

    def receive_message(self):
        return self.socket.recvfrom(1024)

    def draw_game_over(self, msg):
        assert pygame.font.get_init()
        font = pygame.font.Font(None, 60)
        text = font.render(msg, True, BLUE)
        text_rect = text.get_rect()
        text_x = self.surface.get_width() / 2 - text_rect.width / 2
        text_y = self.surface.get_height() / 2 - text_rect.height / 2
        self.surface.blit(text, [text_x, text_y])
        pygame.display.flip()

    def _draw_rect(self, pos, color):
        x, y = pos
        pygame.draw.rect(self.surface, color,
                         (x * self.snake_size + 1, y * self.snake_size + 1, self.snake_size - 2, self.snake_size - 2))

    def _draw_snake(self, bitmap, color):
        # bitmap is a 128 bytes byte array object
        snake_body = bitmap_to_snake(bitmap)
        for (x, y) in snake_body:
            print(x, y)
        for pos in snake_body:
            self._draw_rect(pos, color)

    def render_board(self, apple, bitmap_1, bitmap_2):
        print("Client is going to render board")
        self.surface.fill(WHITE)
        self._draw_rect(apple, RED)
        self._draw_snake(bitmap_1, GREEN)
        self._draw_snake(bitmap_2, ORANGE)
        pygame.display.flip()

    def update_direction(self):
        # TODO: player and opponent will never receive a key press event
        keys = pygame.key.get_pressed()
        direction_changed = False
        if keys[pygame.K_LEFT] and self.DIRECTION_MAP[(self.dx, self.dy)] != 3:
            self.dx, self.dy = -1, 0
            direction_changed = True
        if keys[pygame.K_UP] and self.DIRECTION_MAP[(self.dx, self.dy)] != 0:
            self.dx, self.dy = 0, -1
            direction_changed = True
        if keys[pygame.K_DOWN] and self.DIRECTION_MAP[(self.dx, self.dy)] != 2:
            self.dx, self.dy = 0, 1
            direction_changed = True
        # print("Direction changed", direction_changed)
        if direction_changed:
            self.send_change_direction_message(self.DIRECTION_MAP[(self.dx, self.dy)])

    def msg_handler(self):
        data, address = self.receive_message()
        if len(data) == 1:
            message_type = int(struct.unpack("!B", data)[0])
            if message_type == 4:
                # wait for 2nd user send message
                client.show_message_on_board("waiting for opponent")
            else:
                # message_type = 5 -> wait for one second for game to start
                client.show_message_on_board("Game is about to start")
                time.sleep(1)
        else:
            threading.Thread(target=client.update_direction())
            message_type = int(struct.unpack("!B", data[0:1])[0])
            if message_type == 6:
                # game over information
                client.game_over = True
                result = int(struct.unpack("!B", data[1:2])[0])
                if result == 1:
                    length = int(struct.unpack("!B", data[2:3])[0])
                    client.winner = struct.unpack("!%ds" % length, data[3:])[0]
            else:
                # message_type = 7
                # decode bitmap message
                sequence_number = struct.unpack("!B", data[1:2])[0]
                apple_row = struct.unpack("!B", data[2:3])[0]
                apple_column = struct.unpack("!B", data[3:4])[0]
                if sequence_number == 0:
                    player_bitmap = struct.unpack("%ds" % 128, data[4:132])[0]
                    opponent_bitmap = struct.unpack("%ds" % 128, data[132:])[0]
                    client.render_board((apple_row, apple_column), player_bitmap, opponent_bitmap)
                else:
                    player_bitmap = struct.unpack("%ds" % 128, data[132:])[0]
                    opponent_bitmap = struct.unpack("%ds" % 128, data[4:132])[0]
                    client.render_board((apple_row, apple_column), player_bitmap, opponent_bitmap)


if __name__ == '__main__':
    # assume the input is valid
    command_type = sys.argv[1]
    game_id = sys.argv[2]
    nick_name = sys.argv[3]
    port_number = int(sys.argv[4])
    client = None
    if command_type == 'create':
        # first player sends information to server
        client = Client(game_id, nick_name, port_number, GREEN)
        client.pack_message(1)
    elif command_type == 'join':
        # second player sends information to server
        client = Client(game_id, nick_name, port_number, ORANGE)
        client.pack_message(2)
    clock = pygame.time.Clock()
    FPS = 5  # frames-per-second
    while True:
        clock.tick(FPS)
        if not client.game_over:
            threading.Thread(target=client.msg_handler())
            # check if direction was changed
        else:
            if client.winner == "":
                client.draw_game_over("It is a draw")
            else:
                client.draw_game_over("{0} is the winner".format(client.winner))
