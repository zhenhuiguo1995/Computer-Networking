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

    def start(self):
        # Start a periodic closure to update config.
        self._config_updater = util.PeriodicClosure(
            self.load_config, _CONFIG_UPDATE_INTERVAL_SEC)
        self._config_updater.start()
        # TODO: init and start other threads.
        while True:
            # send update message to neighbor
            time.sleep(6)
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

    def load_config(self):
        assert os.path.isfile(self._config_filename)
        with open(self._config_filename, 'r') as f:
            router_id = int(f.readline().strip())
            # Only set router_id when first initialize.
            if not self._router_id:
                # load_config for the first time, read and initialize forwarding table
                self._socket.bind(('localhost', _ToPort(router_id)))
                self._router_id = router_id
                lines = f.readlines()
                for line in lines:
                    next_hop, distance = line.rstrip("\n").split(",")
                    self._forwarding_table.put(int(next_hop),
                                               (int(next_hop), int(distance)))
            else:
                # todo: update forwarding table
                pass
        f.close()
        # print(self._forwarding_table)

    def send_update_to_neighbors(self):
        message = self.pack_message()
        for router_id in self._forwarding_table.get_keys():
            self._socket.sendto(message, ('localhost', _ToPort(router_id)))

    def pack_message(self):
        entry_count = 1 + self._forwarding_table.size()
        print("When packing message, we got ", self._forwarding_table.snapshot())
        lst = self._forwarding_table.get_keys()
        lst.append(self._router_id)
        message = b""
        message += struct.pack("!H", entry_count)
        lst.sort()
        for i in lst:
            if i == self._router_id:
                message += struct.pack("!HH", i, 0)
            else:
                message += struct.pack("!HH", i, self._forwarding_table.get(i)[1])
        return message

    def update_forwarding_table(self, router_id, d):
        distance = self._forwarding_table.get(router_id)[1]
        start_router = self._router_id
        middle_router = router_id
        for key in self._forwarding_table.get_keys():
            if key != start_router and key != middle_router:
                if distance + d[key] < self._forwarding_table.get(key)[1]:
                    # update forwarding table
                    self._forwarding_table.put(key, (middle_router, distance + d[key]))

    def msg_handler(self):
        # todo : check the format of an addr variable
        # here I assume addr = (host_ip, port_number)
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
