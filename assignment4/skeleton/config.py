# Port numbers used by unreliable network layers.
SENDER_LISTEN_PORT = 8080
RECEIVER_LISTEN_PORT = 8081

# Parameters for unreliable network.
BIT_ERROR_PROB = 0.3
MSG_LOST_PROB = 0.3

# Parameters for transport protocols.
TIMEOUT_MSEC = 150
WINDOW_SIZE = 20

# Packet size for network layer.
MAX_SEGMENT_SIZE = 512
# Packet size for transport layer.
MAX_MESSAGE_SIZE = 500

# Message types used in transport layer.
MSG_TYPE_DATA = 1
MSG_TYPE_ACK = 2

# Sender and receiver states
WAIT_FOR_CALL = 0
WAIT_FOR_ACK = 1
SENDER_WAIT_RATIO = 0.75
