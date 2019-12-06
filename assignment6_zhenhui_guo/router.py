import os.path
import socket
import struct

import table
import threading
import util
import time

_CONFIG_UPDATE_INTERVAL_SEC = 5

_MAX_UPDATE_MSG_SIZE = 1024
_BASE_ID = 8000


def _ToPort(router_id):
    return _BASE_ID + router_id


def _ToRouterId(port):
    return port - _BASE_ID


class Router:
    def __init__(self, config_filename):
        # ForwardingTable has 3 columns (DestinationId,NextHop,Cost). It's
        # thread-safe.
        self._forwarding_table = table.ForwardingTable()
        # Config file has router_id, neighbors, and link cost to reach
        # them.
        self._config_filename = config_filename
        self._router_id = None
        # Socket used to send/recv update messages (using UDP).
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._config_updater = None
        self.distance_vector = {}

    def start(self):
        # Start a periodic closure to update config.
        self._config_updater = util.PeriodicClosure(
            self.load_config, _CONFIG_UPDATE_INTERVAL_SEC)
        self._config_updater.start()
        # TODO: init and start other threads.
        while True:
            # send update message to neighbor
            time.sleep(_CONFIG_UPDATE_INTERVAL_SEC)
            threading.Thread(target=self.send_update_to_neighbors()).start()
            threading.Thread(target=self.msg_handler()).start()
            self._config_updater.stop()
            self._config_updater.start()
            print(self._forwarding_table)

    def stop(self):
        if self._config_updater:
            self._config_updater.stop()
        # TODO: clean up other threads.
        # how to clean up other threads
        self._forwarding_table.reset(self._forwarding_table.snapshot())
        self._router_id = None
        self._config_updater = None
        self.distance_vector = {}

    def load_config(self):
        assert os.path.isfile(self._config_filename)
        with open(self._config_filename, 'r') as f:
            router_id = int(f.readline().strip())
            if not self._router_id:
                # load_config for the first time, read and initialize forwarding table
                self._socket.bind(('localhost', _ToPort(router_id)))
                self._router_id = router_id
                lines = f.readlines()
                for line in lines:
                    next_hop, distance = line.rstrip("\n").split(",")
                    next_hop, distance = int(next_hop), int(distance)
                    self.distance_vector[next_hop] = distance
                    self._forwarding_table.put(next_hop, (next_hop, distance))
            else:
                # todo: update forwarding table
                # don't really know what to do here
                print("reading the config file but doing nothing")
                pass
        f.close()

    def send_update_to_neighbors(self):
        message = self.pack_message()
        for router_id in self.distance_vector.keys():
            self._socket.sendto(message, ('localhost', _ToPort(router_id)))

    def pack_message(self):
        entry_count = 1 + self._forwarding_table.size()
        # print("When packing message, we got ", self._forwarding_table.snapshot())
        lst = [key for key in self.distance_vector.keys()]
        lst.append(self._router_id)
        message = b""
        message += struct.pack("!H", entry_count)
        lst.sort()
        for neighbor_id in lst:
            if neighbor_id == self._router_id:
                message += struct.pack("!HH", neighbor_id, 0)
            else:
                message += struct.pack("!HH", neighbor_id, self.distance_vector[neighbor_id])
        return message

    def update_forwarding_table(self, router_id, neighbor_distance_vector):
        distance = self.distance_vector[router_id]
        for key in self.distance_vector.keys():
            if key != router_id:
                new_distance = distance + neighbor_distance_vector[key]
                if new_distance < self.distance_vector[key]:
                    # update forwarding table
                    self._forwarding_table.put(key, (router_id, new_distance))
                    self.distance_vector[key] = new_distance

    def msg_handler(self):
        data, addr = self._socket.recvfrom(_MAX_UPDATE_MSG_SIZE)
        router_id = _ToRouterId(addr[1])
        # a dictionary for another router
        d = {}
        entry_count = struct.unpack("!H", data[0:2])[0]
        for i in range(entry_count):
            next_hop = struct.unpack("!H", data[2 + i * 4: 4 + i * 4])[0]
            cost = struct.unpack("!H", data[4 + i * 4: 6 + i * 4])[0]
            d[next_hop] = cost
        self.update_forwarding_table(router_id, d)
