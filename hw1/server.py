import socket

host_name = socket.getfqdn()
print('hostname is ', host_name)

host_ip = socket.gethostbyname(host_name)
print('host IP address is', host_ip)
host_port = 8181

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host_ip, host_port))