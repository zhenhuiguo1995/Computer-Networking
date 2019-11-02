import udt
import struct
import config


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.sequence_number = 0
        self.HEADER_LENGTH = 16
        self.buffer = ""
        self.state = 0
        # sender state == 0(wait for call 0), 1(wait for ack 0),
        # 2(wait for call 1), 3(wait for ack 1)
        # receiver state: 0(waiting for call 0), 1(sending ack 0),
        # 2(waiting for call 1), 3(sending ack 1)

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        if self.state in [0, 2]:
            # this is the sender, which sends messages
            sequence_number = 0 if self.state == 0 else 1
            packet = self.make_packet(config.MSG_TYPE_DATA, sequence_number, msg)
            self.network_layer.send(packet)
            self.state = (self.state + 1) % 4
        else:
            # self.state = [1, 3]
            # this is the receiver, which send acks
            sequence_number = 0 if self.state == 1 else 1
            packet = self.make_packet(config.MSG_TYPE_ACK, sequence_number, msg)
            self.network_layer.send(packet)
            self.state = (self.state + 1) % 4

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.
        payload_length = len(msg) - 3 * self.HEADER_LENGTH
        tmp = struct.unpack("!%ds%ds%ds%ds" % (self.HEADER_LENGTH, self.HEADER_LENGTH
                                               , self.HEADER_LENGTH, payload_length), msg)
        data_type = int(tmp[0].decode())
        sequence_number = int(tmp[1].decode())
        check_sum = int(tmp[2].decode())
        pay_load = tmp[3]
        if self.state in [0, 2]:
            # meaning this is the receiver
            if self.corrupted(check_sum, data_type, sequence_number):
                self.state = (self.state - 1) % 4
                self.send("")
            elif self.is_wrong_ack(sequence_number):
                self.state = (self.state - 1) % 4
                self.send("")
            else:
                # receiver receive the correct information
                self.msg_handler(pay_load)
                self.send("")  # send ack 0 or send ack 1
                self.state = (self.state + 1) % 4
        else:
            # self.state in [1, 3] meaning this is the sender, which receiver ack information
            if self.corrupted(check_sum, data_type, sequence_number):
                # sender will do nothing but wait until timeout
                pass
            elif self.is_wrong_ack(sequence_number):
                # sender will do nothing but wait until time out
                pass
            else:
                # sender receives the right information
                self.state = (self.state + 1) % 4

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this
        # class.
        self.network_layer.shutdown()
        self.stop_timer()
        self.buffer = ""
        self.sequence_number = 0

    def make_packet(self, msg_type, sequence_number, msg):
        return struct.pack("!%ds%ds%ds%ds" % (self.HEADER_LENGTH, self.HEADER_LENGTH
                                              , self.HEADER_LENGTH, len(msg)),
                           str(msg_type).encode(), str(sequence_number).encode(),
                           self.check_sum(msg_type).encode(), msg)

    def check_sum(self, msg_type):
        return str(msg_type + self.sequence_number)

    def corrupted(self, check_sum, data_type, sequence_number):
        return check_sum != (data_type + sequence_number)

    def stop_timer(self):
        pass

    def start_timer(self):
        pass

    def is_wrong_ack(self, sequence_number):
        if self.state in [0, 1] and sequence_number == 0:
            return True
        elif self.state in [2, 3] and sequence_number == 1:
            return True
        return False
