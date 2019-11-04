import dummy
import gbn
import sw
import struct


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
    assert name == 'dummy' or name == 'sw' or name == 'gbn'
    if name == 'dummy':
        return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
    if name == 'sw':
        return sw.StopAndWait(local_port, remote_port, msg_handler)
    if name == 'gbn':
        return gbn.GoBackN(local_port, remote_port, msg_handler)


def make_packet(msg_type, sequence_number, msg):
    checksum = calculate_checksum(msg_type, sequence_number, msg)
    return struct.pack("!HHH", msg_type, sequence_number, checksum) + msg


def calculate_checksum(msg_type, sequence_number, pay_load):
    result = msg_type + sequence_number
    for i in range(0, len(pay_load) - 1, 2):
        result += int.from_bytes(pay_load[i: i + 2], byteorder='big')
    if len(pay_load) % 2 != 0:
        result += int.from_bytes(pay_load[len(pay_load) - 1:], byteorder='big')
    return result % (2 ** 16)


def unpack_packet(msg):
    if is_corrupted(msg):
        return None, None, None, False
    else:  # the msg is a valid message
        msg_type = struct.unpack("!H", msg[0:2])
        sequence_number = struct.unpack("!H", msg[2:4])
        pay_load = msg[6:]
        return msg_type, sequence_number, pay_load, True


def is_corrupted(msg):
    if len(msg) < 6:
        return True
    msg_type = struct.unpack("!H", msg[0:2])[0]
    sequence_number = struct.unpack("!H", msg[2:4])[0]
    expected_check_sum = struct.unpack("!H", msg[4:6])[0]
    pay_load = msg[6:]
    actual_check_sum = calculate_checksum(msg_type, sequence_number, pay_load)
    print("Expected check sum is {0}, actual check sum is {1}, they are {2}"
          .format(expected_check_sum, actual_check_sum, expected_check_sum == actual_check_sum))
    if expected_check_sum == actual_check_sum:
        return False
    return True
