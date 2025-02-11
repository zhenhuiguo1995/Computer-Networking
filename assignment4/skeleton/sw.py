import udt
from config import *
import threading
import time
import util


class StopAndWait:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.lock = threading.Lock()
        self.is_sender = False
        self.buffer = b""
        self.sequence_number = 0
        self.timer = None
        self.state = WAIT_FOR_CALL

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        self.is_sender = True
        threading.Thread(target=self.send_msg(msg))
        return True

    def send_msg(self, msg):
        while self.state == WAIT_FOR_ACK:  # wait until receives current ack
            time.sleep(SENDER_WAIT_RATIO * TIMEOUT_MSEC / 1000)
        packet = util.make_packet(MSG_TYPE_DATA, self.sequence_number, msg)
        with self.lock:
            self.network_layer.send(packet)
            self.timer = self.get_timer()
            self.state = WAIT_FOR_ACK  # already sent a message, now wait for ack
            self.buffer = packet
            self.timer.start()

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.
        msg_type, msg_sequence_number, pay_load, is_valid = util.unpack_packet(msg)
        if not is_valid:  # packet is corrupted
            if not self.is_sender:  # receiver receive wrong data
                if self.buffer == b'':  # no buffer, just wait until times out, sender will resend
                    return
                else:  # receiver will resend the previous ack
                    self.network_layer.send(self.buffer)
            return
        if msg_type == MSG_TYPE_ACK:  # sender
            if self.sequence_number == msg_sequence_number and self.state == WAIT_FOR_ACK:
                with self.lock:
                    self.timer.cancel()
                    self.sequence_number = 1 - self.sequence_number
                    self.state = WAIT_FOR_CALL
        else:  # receiver
            if self.sequence_number == msg_sequence_number:
                self.msg_handler(pay_load)
                packet = util.make_packet(MSG_TYPE_ACK, self.sequence_number, b'')
                self.network_layer.send(packet)
                self.buffer = packet
                self.sequence_number = 1 - self.sequence_number
            else:
                self.network_layer.send(self.buffer)
        return

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this class.
        if self.is_sender:
            self.wait_for_last_ack()
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.buffer = b"" # buffer needs to be cleaned
        self.network_layer.shutdown()

    def resend(self):
        with self.lock:
            self.network_layer.send(self.buffer)
            self.timer = self.get_timer()
        self.timer.start()
        return

    def get_timer(self):
        return threading.Timer(TIMEOUT_MSEC / 1000, self.resend)

    def wait_for_last_ack(self):
        while self.state == WAIT_FOR_ACK:
            print("Sender is waiting for the last ACK")
            time.sleep(1)
