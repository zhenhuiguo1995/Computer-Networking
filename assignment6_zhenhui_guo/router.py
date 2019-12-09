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
        self._send_updater = None
        self.distance_vector = {}
        self.neighbor_vectors = {}
        self.has_changed = True

    def start(self):
        # Start a periodic closure to update config.
        self._config_updater = util.PeriodicClosure(
            self.load_config, _CONFIG_UPDATE_INTERVAL_SEC)
        self._config_updater.start()
        # TODO: init and start other threads.
        self._send_updater = util.PeriodicClosure(
            self.send_update_to_neighbors,_CONFIG_UPDATE_INTERVAL_SEC)
        while True:
            threading.Thread(target=self.msg_handler()).start()
            print(self._forwarding_table)

    def stop(self):
        if self._config_updater:
            self._config_updater.stop()
        # TODO: clean up other threads.
        if self._send_updater:
            self._send_updater.stop()
        self._forwarding_table = None
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
            snapshot = [(self._router_id, self._router_id, 0)]
            distance_vector_updated = False
            for line in lines:
                next_hop, distance = line.rstrip("\n").split(",")
                next_hop, distance = int(next_hop), int(distance)
                snapshot.append((next_hop, next_hop, distance))
                if next_hop not in self.distance_vector or self.distance_vector[next_hop] != distance:
                    distance_vector_updated = True
                self.distance_vector[next_hop] = distance
            if distance_vector_updated:
                self.has_changed = True
                self._forwarding_table.reset(snapshot)
            # print("distance vector is: ", self.distance_vector)
                print("forwarding table is: \n", self._forwarding_table)
        f.close()

    def send_update_to_neighbors(self):
        message = self.pack_message()
        for router_id in self.distance_vector.keys():
            self._socket.sendto(message, ('localhost', _ToPort(router_id)))

    def pack_message(self):
        entry_count = self._forwarding_table.size()
        # print("When packing message, we got ", self._forwarding_table.snapshot())
        snapshot = self._forwarding_table.snapshot()
        message = b""
        message += struct.pack("!H", entry_count)
        for element in snapshot:
            # pack message based on forwarding table
            message += struct.pack("!HH", element[0], element[2])
        return message

    """def update_forwarding_table(self):
        # first clear the forwarding table
        self._forwarding_table = table.ForwardingTable()
        self._forwarding_table.put(self._router_id, (self._router_id, 0))
        for next_hop in self.neighbor_vectors.keys():
            distance = self.distance_vector[next_hop]
            for end_router in self.neighbor_vectors[next_hop].keys():
                if end_router != next_hop and end_router != self._router_id:
                    new_distance = distance + self.neighbor_vectors[next_hop][end_router]
                    if new_distance < self.distance_vector[end_router]:
                        self._forwarding_table.put(end_router, (next_hop, new_distance))
                    else:
                        self._forwarding_table.put(end_router, (end_router, self.distance_vector[end_router]))"""

    def msg_handler(self):
        data, addr = self._socket.recvfrom(_MAX_UPDATE_MSG_SIZE)
        router_id = _ToRouterId(addr[1])
        d = {}
        entry_count = struct.unpack("!H", data[0:2])[0]
        for i in range(entry_count):
            next_hop = struct.unpack("!H", data[2 + i * 4: 4 + i * 4])[0]
            cost = struct.unpack("!H", data[4 + i * 4: 6 + i * 4])[0]
            d[next_hop] = cost
        print("We received message: ", d)
        if router_id in self.neighbor_vectors and self.neighbor_vectors[router_id] == d:
            return
        else:
            self.neighbor_vectors[router_id] = d
            self.relax()

    def relax(self):
        self.has_changed = False
        # a temporary forwarding table
        table = {}
        table[self._router_id] = (self._router_id, 0)
        for router_id in self.distance_vector:
            table[router_id] = (router_id, self.distance_vector[router_id])
        for router_id in self.neighbor_vectors:
            vector = self.neighbor_vectors[router_id] # a dict
            pairs = [vector[key] for key in vector]
            for key in pairs:
                destination = key[0]
                cost = key[1]
                if destination not in table or table[router_id][1] + cost < table[destination][1]:
                    table[destination] = (router_id, table[router_id][1] + cost)
        snapshot = []
        for router_id in table:
            snapshot.append((router_id, table[router_id][0], table[router_id][1]))
        self._forwarding_table.reset(snapshot)




