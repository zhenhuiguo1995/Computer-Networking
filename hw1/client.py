import socket
import struct

server_name = socket.getfqdn()
print('Hostname', server_name)
server_port = 8181

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.connect((server_name, server_port))
print('Connected to server ', server_name)

expression_number = 1
first_expression = "2-4+29"
byte_first_expression = first_expression.encode('utf-8')
bufsize = 16

#print(byte_first_expression)
bs = struct.pack('!hh%ds' % len(byte_first_expression),
                 expression_number, len(first_expression), first_expression.encode('utf-8'))
#print(bs)
s.sendall(bs)
end_of_file = False
data = ""
while not end_of_file:
    data += s.recv(bufsize)
    if not data:
        end_of_file = True

print('Client received: ', data)