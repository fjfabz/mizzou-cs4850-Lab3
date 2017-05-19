# Kevin Free, Mizzou CS Senior, 18114059
# CS4850 Networks
# 26 April 2017
# Lab 3, Version 2
# Multiuser Chat Room
# ----- Client code -----

import socket
import select
import sys

print '\nWelcome to Lab 3 Version 2 Chat Server by Kevin Free (18114059)'
print 'Available commands are:'
print 'login <UserID> <Password>'
print 'newuser <UserID> <Password>'
print 'send all <message>'
print 'send UserID <message>'
print 'who'
print 'logout\n'

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
server_address = ('localhost', 14059)
print 'connecting to %s port %s...' % server_address
try:
    sock.connect(server_address)
except:
    print 'Unable to connect\n'
    sys.exit()

while 1:
    # Sockets we will read from are standard in, and the server connection
    socket_list = [sys.stdin, sock]

    # Select based multiplexing, checking both sockets
    read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

    for socket in read_sockets:
        # Incoming message from server
        if socket == sock:
            data = socket.recv(1024)
            # Self-explanatory checks and closing the connection
            if not data:
                print 'Disconnected from chat server\n'
                sock.close()
                sys.exit()
            elif data == 'exit':
                print 'Successful disconnection\n'
                sock.close()
                sys.exit()
            elif data == 'full':
                print 'Server already is connected to the max number of clients\n'
                sock.close()
                sys.exit()
            # Print out the response otherwise
            else:
                print str(data)

        # User entered a message
        else:
            msg = raw_input()
            sock.send(msg)
