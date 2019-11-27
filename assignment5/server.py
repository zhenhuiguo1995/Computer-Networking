import socket
import threading
from utils import *
from config import *


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

    def msg_handler(self):
        data, addr = server.receive_msg()
        msg_type, id_length, name_length = struct.unpack("!BBB", data[0:3])
        game_id = struct.unpack("!%ds" % id_length, data[3:3 + id_length])[0]
        nick_name = struct.unpack("!%ds" % name_length,
                                  data[3 + id_length: 3 + id_length + name_length])[0]
        if msg_type == 1:
            print("create the first user information")
            port_number = int(struct.unpack("!H", data[-2:])[0])
            first_player = Player(game_id, nick_name, port_number, addr, GREEN)
            self.game_player_dict[game_id] = [first_player]
            self.game_status_dict[game_id] = GameStatus(NOT_STARTED)
            self.send_msg(struct.pack("!B", 4), addr)
        elif msg_type == 2:
            port_number = int(struct.unpack("!H", data[-2:])[0])
            second_player = Player(game_id, nick_name, port_number, addr, ORANGE)
            self.game_player_dict[game_id].append(second_player)
            for player in self.game_player_dict[game_id]:
                self.send_msg(struct.pack("!B", 5), player.addr)
            time.sleep(1)
            print("Game now starts")
            self.game_status_dict[game_id].game_status = ON_GOING
            self.apple_dict[game_id] = choose_random_pos()
            self.timer_list[game_id] = threading.Timer(INTERVAL, self.send_update_to_client)
            self.timer_list[game_id].start()
        elif msg_type == 3:
            direction = int(struct.unpack("!B", data[-1:])[0])
            print("Direction is going to change to ", direction)
            dx, dy = self.direction_map[direction]
            for player in self.game_player_dict[game_id]:
                if player.nick_name == nick_name and player.game_id == game_id:
                    player.snake_app.change_direction(dx, dy)

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
        print("game over message will be sent")
        if winner == "":
            return struct.pack("!BBB", 6, result, len(winner))
        return struct.pack("!BBB%ds" % len(winner), 6, result, len(winner), winner)

    def check_hit_itself(self, game_id):
        if self.game_player_dict[game_id][0].snake_app.game_over:
            return True, 2
        elif self.game_player_dict[game_id][1].snake_app.game_over:
            return True, 1
        return False, None

    def send_update_to_client(self):
        for game_id in self.game_player_dict.keys():
            print("send update to client")
            # what is the condition
            if self.game_status_dict[game_id].game_status == ON_GOING:
                # game is on going
                # todo: record the head information of each player
                if self.timer_list[game_id].is_alive():
                    self.timer_list[game_id].cancel()
                    self.timer_list[game_id] = threading.Timer(INTERVAL, self.send_update_to_client)
                    self.timer_list[game_id].start()
                for player in self.game_player_dict[game_id]:
                    player.snake_app.run_once(self.apple_dict[game_id])
                    threading.Thread(self.send_msg(self.pack_msg(game_id, player), player.addr))
                hit_itself, winner_id = self.check_hit_itself(game_id)
                if hit_itself:
                    self.game_status_dict[game_id].game_status = ENDED
                    self.game_status_dict[game_id].result = 1
                    self.game_status_dict[game_id].winner = self.game_player_dict[game_id][0].nick_name \
                        if winner_id == 1 else self.game_player_dict[game_id][1].nick_name
                    for player in self.game_player_dict[game_id]:
                        player.snake_app.game_over = True
                        self.send_msg(self.game_over_message(game_id), player.addr)
                        return
                # if did not hit itself, then check if hit another snake
                head_1 = self.game_player_dict[game_id][0].snake_app.get_head()
                head_2 = self.game_player_dict[game_id][1].snake_app.get_head()
                body_1 = self.game_player_dict[game_id][0].snake_app.get_body()
                body_2 = self.game_player_dict[game_id][1].snake_app.get_body()
                game_ended, winner_id = is_game_ended(head_1, head_2, body_1, body_2)
                self.update_apple(game_id, head_1, head_2, body_1, body_2)
                if game_ended:
                    print("Game ended is true and winner is {0}".format(winner_id))
                    # build game end information
                    self.game_status_dict[game_id].game_status = ENDED
                    self.game_status_dict[game_id].result = 0 if winner_id is None else 1
                    if self.game_status_dict[game_id].result == 1:
                        self.game_status_dict[game_id].winner = self.game_player_dict[game_id][0].nick_name \
                            if winner_id == 1 else self.game_player_dict[game_id][1].nick_name
                    for player in self.game_player_dict[game_id]:
                        if game_ended:
                            player.snake_app.game_over = True
                            threading.Thread(self.send_msg(self.game_over_message(game_id), player.addr))
                            print("to player: ", player.nick_name)
                    """else:
                        self.send_msg(self.pack_msg(game_id, player), player.addr)"""
            elif self.game_status_dict[game_id].game_status == ENDED:
                for player in self.game_player_dict[game_id]:
                    player.snake_app.game_over = True
                    threading.Thread(self.send_msg(self.game_over_message(game_id), player.addr))

    def update_apple(self, game_id, head_1, head_2, body_1, body_2):
        apple = self.apple_dict[game_id]
        if apple == head_1 or apple == head_2:
            new_apple = choose_random_pos()
            while new_apple in body_1 or new_apple in body_2:
                new_apple = choose_random_pos()
            self.apple_dict[game_id] = new_apple


server = Server()
while True:
    threading.Thread(target=server.msg_handler()).start()
