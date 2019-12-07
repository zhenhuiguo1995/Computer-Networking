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


"""
1. direct link cost update  -> read config file
2. update neighbor distance -> (not true distance)
3. send update to neighbor -> not distance vector(true link cost), but forwarding table
4. each time we read config file, we clear and rebuild link cost update
5. each time we received message from neighbors, we clear the forwarding table
"""


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
        self.neighbor_vector = {}
        self.num_of_neighbors = 0
        self.lock = threading.Lock()

    def start(self):
        # Start a periodic closure to update config.
        self._config_updater = util.PeriodicClosure(
            self.load_config, _CONFIG_UPDATE_INTERVAL_SEC)
        self._config_updater.start()
        # TODO: init and start other threads.
        while True:
            # send update message to neighbor
            time.sleep(_CONFIG_UPDATE_INTERVAL_SEC)
            # first send update, next recv message, otherwise code will not run
            threading.Thread(target=self.send_update_to_neighbors()).start()
            threading.Thread(target=self.msg_handler()).start()
            self._config_updater.stop()
            self._config_updater.start()
            print(self._forwarding_table)

    def stop(self):
        if self._config_updater:
            self._config_updater.stop()
        # TODO: clean up other threads.
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
                    self.num_of_neighbors += 1
                self._forwarding_table.put(self._router_id, (self._router_id, 0))
                print("Reading config for the first time: ", self._forwarding_table)
            else:
                # todo: read config file and rewrite distance vector
                lines = f.readlines()
                # clear distance vector
                self.distance_vector = {}
                for line in lines:
                    next_hop, distance = line.rstrip("\n").split(",")
                    next_hop, distance = int(next_hop), int(distance)
                    self.distance_vector[next_hop] = distance
        f.close()

    def send_update_to_neighbors(self):
        message = self.pack_message()
        for router_id in self.distance_vector.keys():
            self._socket.sendto(message, ('localhost', _ToPort(router_id)))

    def pack_message(self):
        entry_count = self._forwarding_table.size()
        print("When packing message, we got ", self._forwarding_table.snapshot())
        with self.lock:
            lst = [key for key in self.distance_vector.keys()]
            lst.append(self._router_id)
            message = b""
            message += struct.pack("!H", entry_count)
            lst.sort()
            for key in lst:
                # pack message based on forwarding table
                message += struct.pack("!HH", key, self._forwarding_table.get(key)[1])
        return message

    def update_forwarding_table(self):
        with self.lock:
            # first clear the forwarding table
            self._forwarding_table = table.ForwardingTable()
            self._forwarding_table.put(self._router_id, (self._router_id, 0))
            for next_hop in self.neighbor_vector.keys():
                distance = self.distance_vector[next_hop]
                for end_router in self.neighbor_vector[next_hop].keys():
                    if end_router != next_hop and end_router != self._router_id:
                        new_distance = distance + self.neighbor_vector[next_hop][end_router]
                        if new_distance < self.distance_vector[end_router]:
                            self._forwarding_table.put(end_router, (next_hop, new_distance))
                        else:
                            self._forwarding_table.put(end_router, (end_router, self.distance_vector[end_router]))

            """for key in neighbor_forwarding_table.keys():
                if key != self._router_id:
                    # if key is not reachable from self._router_id
                    new_distance = distance + neighbor_forwarding_table[key]
                    if key not in self.distance_vector:
                        self._forwarding_table.put(key, (router_id, new_distance))
                    else:
                        if new_distance < self.distance_vector[key]:
                            # we choose router_id as the next hop
                            self._forwarding_table.put(key, (router_id, new_distance))
                        else:  # new_distance >= self.distance_vector[key]
                            # we choose key as next hop
                            self._forwarding_table.put(key, (key, self.distance_vector[key]))
                else:
                    self._forwarding_table.put(key, (self._router_id, 0))"""

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
        print("We received message: ", d)
        self.neighbor_vector[router_id] = d
        if len(self.neighbor_vector) == self.num_of_neighbors:
            self.update_forwarding_table()
