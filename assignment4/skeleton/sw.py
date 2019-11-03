import udt
import struct
import config
import threading


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_port, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.HEADER_LENGTH = 16
        self.buffer = ""
        self.state = 0
        self.lock = threading.Lock()
        # sender state: 0(wait for call 0), 1(wait for ack 0),
        # 2(wait for call 1), 3(wait for ack 1)
        # receiver state: 0(waiting for call 0), 1(sending ack 0),
        # 2(waiting for call 1), 3(sending ack 1)

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        print("about to send message", msg)
        with self.lock:
            if self.state in [0, 2]:
                # this is the sender, which sends data, receives acks
                sequence_number = 0 if self.state == 0 else 1
                print("state = {0}, sequence_number = {1}".format(self.state, sequence_number))
                packet = self.make_packet(config.MSG_TYPE_DATA, sequence_number, msg)
                self.network_layer.send(packet)
                self.state = (self.state + 1) % 4
                return True
            else:
                # self.state = [1, 3]
                # this is the receiver, which send acks, receives data
                sequence_number = 0 if self.state == 1 else 1
                print("state = {0}, sequence number = {1}".format(self.state, sequence_number))
                packet = self.make_packet(config.MSG_TYPE_ACK, sequence_number, msg)
                self.network_layer.send(packet)
                self.state = (self.state + 1) % 4
                return True

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        print("about to handle arrival msg")
        with self.lock:
            msg = self.network_layer.recv()
            # TODO: impl protocol to handle arrived packet from network layer.
            # call self.msg_handler() to deliver to application layer.
            payload_length = len(msg) - 3 * self.HEADER_LENGTH
            tmp = struct.unpack("!%ds%ds%ds%ds" % (self.HEADER_LENGTH, self.HEADER_LENGTH
                                                   , self.HEADER_LENGTH, payload_length), msg)
            data_type = int(tmp[0].decode()[0])
            sequence_number = int(tmp[1].decode()[0])
            check_sum = int(tmp[2].decode()[0])
            pay_load = tmp[3]
            if self.state in [0, 2]:
                """print("Received message {0}".format(msg))
                print("state for receiver is {0}".format(self.state))"""
                """print("Receiver receives the following information: data_type :{0}, "
                      "sequence_number: {1}, check_sum: {2}, pay_load: {3}".format(
                        data_type, sequence_number, check_sum, pay_load))"""
                # meaning this is the receiver, which receives sequences
                if self.corrupted(check_sum, data_type, sequence_number):
                    print("receiver receive corrupted message {0}".format(msg))
                    self.state = (self.state - 1) % 4
                    self.send(b"")
                elif self.is_wrong_sequence(sequence_number):
                    print("Receiver receives wrong sequence number {0} {1}".format(msg, sequence_number))
                    self.state = (self.state - 1) % 4
                    self.send(b"")
                else:
                    # receiver receive the correct information
                    self.msg_handler(pay_load)
                    self.state = (self.state + 1) % 4
                    self.send(b"")  # send ack 0 or send ack 1
            else:
                # self.state in [1, 3] meaning this is the sender, which receiver ack information
                print("State for sender is {0}".format(self.state))
                print("Receiver receives the following information: data_type :{0}, "
                      "sequence_number: {1}, check_sum: {2}, pay_load: {3}"
                      .format(data_type, sequence_number, check_sum, pay_load))
                if self.corrupted(check_sum, data_type, sequence_number):
                    # sender will do nothing but wait until timeout
                    print("Sender receives corrupted message")
                    self.state = (self.state + 1) % 4
                elif self.is_wrong_ack(sequence_number):
                    # sender will do nothing but wait until time out
                    print("Sender receives wrong ack number ")
                    self.state = (self.state + 1) % 4
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

    def make_packet(self, msg_type, sequence_number, msg):
        check_sum = self.check_sum(msg_type, sequence_number)
        """print("msg_type is type {0}, {1}".format(type(msg_type), msg_type))
        print("sequence number is type {0}, {1}".format(type(sequence_number), sequence_number))
        print("check sum is type {0}, {1}".format(type(check_sum), check_sum))
        print("msg is type {0}, {1}".format(type(msg), msg))"""
        return struct.pack("!%ds%ds%ds%ds" % (self.HEADER_LENGTH, self.HEADER_LENGTH
                                              , self.HEADER_LENGTH, len(msg)),
                           str(msg_type).encode(), str(sequence_number).encode(),
                           check_sum.encode(), msg)

    def check_sum(self, msg_type, sequence_number):
        return str(msg_type + sequence_number)

    def corrupted(self, check_sum, data_type, sequence_number):
        return not (check_sum == (data_type + sequence_number))

    def stop_timer(self):
        pass

    def start_timer(self):
        pass

    def is_wrong_ack(self, sequence_number):
        # self.state in [1, 3]
        if self.state == 1 and sequence_number == 0:
            return False
        elif self.state in 3 and sequence_number == 1:
            return False
        return True

    def is_wrong_sequence(self, sequence_number):
        print("state {0}, sequence_number {1}".format(self.state, sequence_number))
        if self.state == 0 and sequence_number == 0:
            return False
        elif self.state == 2 and sequence_number == 1:
            return False
        return True
