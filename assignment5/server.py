import socket
import threading
from utils import *
from config import *

WHITE = 255, 255, 255
BLACK = 0, 0, 0
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
ORANGE = 255, 165, 0
SCREEN_WIDTH = 32 * 20
SCREEN_HEIGHT = 32 * 20


class Server:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((UDP_IP, UDP_PORT))
        self.game_player_dict = {}
        self.apple_dict = {}
        self.direction_map = {0: (0, -1), 1: (1, 0), 2: (0, 1), 3: (-1, 0)}
        self.game_status_dict = {}
        self.timer_list = {}
        self.lock = threading.Lock()

    def msg_handler(self, data, addr):
        # handles a message
        msg_type, id_length, name_length = struct.unpack("!BBB", data[0:3])
        game_id = struct.unpack("!%ds" % id_length, data[3:3 + id_length])[0]
        nick_name = struct.unpack("!%ds" % name_length,
                                  data[3 + id_length: 3 + id_length + name_length])[0]
        if msg_type == 1:
            # create a new game
            # the color of the snake needs to redefined
            print("create the first user information")
            port_number = int(struct.unpack("!H", data[-2:])[0])
            first_player = Player(game_id, nick_name, port_number, addr, GREEN)
            self.game_player_dict[game_id] = [first_player]
            self.game_status_dict[game_id] = GameStatus(NOT_STARTED)
            self.send_msg(struct.pack("!B", 4), addr)
        elif msg_type == 2:
            # 2nd player joins the game
            port_number = int(struct.unpack("!H", data[-2:])[0])
            second_player = Player(game_id, nick_name, port_number, addr, ORANGE)
            self.game_player_dict[game_id].append(second_player)
            # send message to both players and wait for a second
            for player in self.game_player_dict[game_id]:
                self.send_msg(struct.pack("!B", 5), player.ip_address)
            time.sleep(1)
            print("Game now starts")
            self.game_status_dict[game_id].game_status = ON_GOING
            self.apple_dict[game_id] = choose_random_pos()
            self.timer_list[game_id] = threading.Timer(50 / 1000, self.send_update_to_client)
            self.timer_list[game_id].start()
        elif msg_type == 3:
            # msg_type = 3, this is a change direction message
            direction = int(struct.unpack("!B", data[-1:])[0])
            dx, dy = self.direction_map[direction]
            for player in self.game_player_dict[game_id]:
                if player.nick_name == nick_name:
                    player.snake_app.dx = dx
                    player.snake_app.dy = dy

    def receive_msg(self):
        return self.socket.recvfrom(1024)

    def send_msg(self, msg, addr):
        self.socket.sendto(msg, addr)

    def _get_bitmap_for_player(self, player):
        return player.snake_app.get_bitmap()

    def pack_msg(self, game_id, player):
        msg = b""
        if self.game_player_dict[game_id][0] == player:
            msg = struct.pack("!BBBB", 7, 0, self.apple_dict[game_id][0], self.apple_dict[game_id][1])

        else:
            msg = struct.pack("!BBBB", 7, 1, self.apple_dict[game_id][0], self.apple_dict[game_id][1])
        msg += self._get_bitmap_for_player(self.game_player_dict[game_id][0])
        msg += self._get_bitmap_for_player(self.game_player_dict[game_id][1])
        return msg

    def game_over_message(self, game_id):
        result = self.game_status_dict[game_id].result
        winner = self.game_status_dict[game_id].winner
        return struct.pack("!BBB%ds" % len(winner), 6, result, len(winner), winner)

    def send_update_to_client(self):
        for game_id in self.game_player_dict.keys():
            print("send update to client")
            # what is the condition
            if self.game_status_dict[game_id].game_status == ON_GOING:
                # game is on going
                # todo: record the head information of each player
                for player in self.game_player_dict[game_id]:
                    if self.timer_list[game_id].is_alive():
                        self.timer_list[game_id].cancel()
                        self.timer_list[game_id] = threading.Timer(50 / 1000, self.send_update_to_client)
                        self.timer_list[game_id].start()
                        # two players should run in two threads
                        threading.Thread(player.snake_app.run_once(self.apple_dict[game_id]))
                # run once and check condition
                head_1 = self.game_player_dict[game_id][0].snake_app.get_head()
                head_2 = self.game_player_dict[game_id][1].snake_app.get_head()
                body_1 = self.game_player_dict[game_id][0].snake_app.get_body()
                body_2 = self.game_player_dict[game_id][1].snake_app.get_body()
                game_ended, winner_id = is_game_ended(head_1, head_2, body_1, body_2)
                # todo : the apple on the client side does not change
                # todo : find out why
                self.update_apple(game_id, head_1, head_2, body_1, body_2)
                if game_ended:
                    self.game_status_dict[game_id].game_status = ENDED
                    self.game_status_dict[game_id].result = 0 if winner_id is None else 1
                    if self.game_status_dict[game_id].result == 1:
                        self.game_status_dict[game_id].winner = self.game_player_dict[game_id][0].nick_name \
                            if winner_id == 1 else self.game_player_dict[game_id][1].nick_name

                for player in self.game_player_dict[game_id]:
                    if game_ended:
                        player.snake_app.game_over = True
                        self.send_msg(self.game_over_message(game_id), player.ip_address)
                    else:
                        self.send_msg(self.pack_msg(game_id, player), player.ip_address)
            elif self.game_status_dict[game_id].game_status == ENDED:
                # game has ended
                for player in self.game_player_dict[game_id]:
                    message = self.game_over_message(game_id)
                    self.send_msg(message, player.ip_address)

    def update_apple(self, game_id, head_1, head_2, body_1, body_2):
        apple = self.apple_dict[game_id]
        if apple == head_1 or apple == head_2:
            print("apple pos is", apple)
            print(head_1, body_1)
            print(head_2, body_2)
            new_apple = choose_random_pos()
            while new_apple in head_1 or apple in head_2:
                new_apple = choose_random_pos()
            self.apple_dict[game_id] = new_apple


server = Server()
while True:
    data, addr = server.receive_msg()
    print("received message: ", data)
    threading.Thread(target=server.msg_handler(data, addr))
