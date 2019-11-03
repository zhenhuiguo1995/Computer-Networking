import udt
import struct
import config
import threading
import time


class StopAndWait:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.HEADER_LENGTH = 16
        self.buffer = b""
        self.lock = threading.Lock()
        self.sequence_number = 0
        self.timer = None
        self.state = config.WAIT_FOR_CALL
        self.WAIT_TIME = 100

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        while self.state == config.WAIT_FOR_ACK:
            print("Sender is waiting for ack")
            time.sleep(0.1)
        self.timer = threading.Timer(config.TIMEOUT_MSEC/1000, self.resend)
        packet = self.make_packet(config.MSG_TYPE_DATA, msg)
        self.network_layer.send(packet)
        self.timer.start()
        print("sender sends message {0}".format(packet))
        self.buffer = packet
        self.state = config.WAIT_FOR_ACK
        return True

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.
        print("Message received is {0}, will decode the message".format(msg))
        if len(msg) < 6:
            self.resend()
        else:
            tmp = struct.unpack("!hhh", msg[:6])
            data_type = tmp[0]
            sequence_number = tmp[1]
            check_sum = tmp[2]
            pay_load = msg[6:]  # byte
            if self.corrupted(check_sum, data_type, sequence_number, pay_load):
                if data_type == config.MSG_TYPE_DATA:  # receiver
                    print("Receiver receives corrupted message, will resend")
                    self.resend()
                else:
                    print("Sender receives a corrupted message, will wait for timeout")
            elif self.sequence_number != sequence_number:
                if data_type == config.MSG_TYPE_DATA:  # receiver
                    print("Receiver receives wrong sequence number, will resend")
                    self.resend()
                else:
                    pass
            else:
                if data_type == config.MSG_TYPE_DATA:  # receiver
                    self.msg_handler(pay_load)
                    packet = self.make_packet(config.MSG_TYPE_ACK, b"")
                    print("Receiver receives a valid packet {0}".format(msg))
                    print("Receiver will send ack packet to sender {0}\n".format(packet))
                    self.network_layer.send(packet)
                    self.buffer = packet
                    self.sequence_number = (1 - self.sequence_number)
                    self.state = config.WAIT_FOR_CALL
                else:  # sender
                    print("Sender receives a correct ack packet, {0}\n".format(msg))
                    self.timer.cancel()
                    self.sequence_number = (1 - self.sequence_number)
                    self.state = config.WAIT_FOR_CALL

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this class.
        print("About to shutdown network layer, buffer will be set to empty")
        self.network_layer.shutdown()
        print("already cancelled the timer")
        self.buffer = b""

    def make_packet(self, msg_type, msg):
        total = self.check_sum(msg_type, self.sequence_number, msg)
        return struct.pack("!hhh", msg_type, self.sequence_number, total) + msg

    def check_sum(self, msg_type, sequence_number, msg):
        return (msg_type + sequence_number + int.from_bytes(msg, byteorder="big"))\
               % (2**16)

    def corrupted(self, sum, data_type, sequence_number, pay_load):
        return not (sum == self.check_sum(data_type, sequence_number, pay_load))

    def resend(self):
        print("the message being resented is {0}".format(self.buffer))
        self.network_layer.send(self.buffer)
