import threading
import time
from config import *
import udt
import util


# Go-Back-N reliable transport protocol.
class GoBackN:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.lock = threading.Lock()
        self.base = 0
        self.next_sequence_number = 0
        self.expected_sequence_number = 0
        self.timer = self.get_timer()
        self.is_sender = False
        self.buffer = [b'' for _ in range(WINDOW_SIZE)]

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        self.is_sender = True
        if self.next_sequence_number < self.base + WINDOW_SIZE:
            # window can still accommodate message
            threading.Thread(target=self.send_msg(msg))
            return True
        else:  # window is full, cannot send any messages
            return False

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.
        msg_type, msg_sequence_number, pay_load, is_valid = util.unpack_packet(msg)
        if not is_valid:
            if not self.is_sender:  # receiver
                if self.expected_sequence_number == 0:  # first message
                    return
                packet = util.make_packet(MSG_TYPE_ACK, self.expected_sequence_number - 1, b'')
                self.network_layer.send(packet)
            return
        if msg_type == MSG_TYPE_ACK:  # sender
            with self.lock:
                self.base = msg_sequence_number + 1  # increase base
                if self.base == self.next_sequence_number:  # all messages in buffer have been acked
                    self.timer.cancel()
                else:
                    if self.timer.is_alive():
                        self.timer.cancel()
                    self.timer = self.get_timer()
                    self.timer.start()
        else:  # receiver
            if msg_sequence_number == self.expected_sequence_number:
                self.msg_handler(pay_load)
                packet = util.make_packet(MSG_TYPE_ACK, self.expected_sequence_number, b'')
                self.network_layer.send(packet)
                self.expected_sequence_number += 1
            else:
                if self.expected_sequence_number == 0:  # first message
                    return  # just wait
                # ack previous message
                packet = util.make_packet(MSG_TYPE_ACK, self.expected_sequence_number - 1, b'')
                self.network_layer.send(packet)

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this
        # class.
        if self.is_sender:
            self.wait_for_last_ack()
        if self.timer.is_alive():
            self.timer.cancel()
        self.buffer = []  # clean buffer
        self.network_layer.shutdown()

    def get_timer(self):
        return threading.Timer(TIMEOUT_MSEC / 1000, self.resend)

    def send_msg(self, msg):
        with self.lock:
            packet = util.make_packet(MSG_TYPE_DATA, self.next_sequence_number, msg)
            self.network_layer.send(packet)
            self.buffer[self.next_sequence_number % WINDOW_SIZE] = packet
            if self.base == self.next_sequence_number:
                if self.timer.is_alive():
                    self.timer.cancel()
                self.timer = self.get_timer()
                self.timer.start()
            self.next_sequence_number += 1

    def resend(self):
        with self.lock:
            if self.timer.is_alive():
                self.timer.cancel()
            self.timer = self.get_timer()
            for i in range(self.base, self.next_sequence_number):
                self.network_layer.send(self.buffer[i % WINDOW_SIZE])
            self.timer.start()

    def wait_for_last_ack(self):
        while self.base < self.next_sequence_number - 1:
            time.sleep(1)
