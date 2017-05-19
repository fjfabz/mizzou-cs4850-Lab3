# Kevin Free, Mizzou CS Senior, 18114059
# CS4850 Networks
# 26 April 2017
# Lab 3, Version 2
# Multiuser Chat Room
# ----- Server code -----

import socket
import sys
import select

MAXCLIENTS = 3
USERS = [] # List of users with passwords
ACTIVEUSERS = [] # List of users with addresses

# login function
def login(user, password, socket):
    # Checks for the User and password to match what's on file
    for u, p in USERS:
        if u == user:
            if p == password:
                # Logic to work around Python's inability to assign to global lists of tuples in a function
                i = 0
                j = -1
                # If the user is already active, reject login
                for au, s in ACTIVEUSERS:
                    if au == user:
                        return 'Unable to log in. User is already active'
                    if s == socket:
                        j = i
                    i += 1
                # Update active user to include the name and socket of who logged in
                if j != -1:
                    ACTIVEUSERS[j] = (user, socket)
                    return 'Login successful.'
    return 'Unable to log in. UserID or Password is incorrect.'

# Function to create a new user
def newuser(user, password):
    global USERS
    # If the password is too short or too long
    if len(password) < 4 or len(password) > 8:
        return 'Password must be between 4 and 8 characters'
    # If the username is too long
    elif len(user) > 31:
        return 'UserId must be less than 32 characters'
    # If the attempted user name is server, because the code uses that statically to represent the server's address
    elif user == 'server':
        return 'Invalid name'
    else:
        # Check if userid is already taken
        for u, p in USERS:
            if u == user:
                return 'UserID is already taken'
        # If it's available, update the file
        with open('users.txt', 'a') as f:
            f.write(user + ' ' + password + '\n')
            f.close()
        USERS += [(user, password)]
        return 'New user created successfully'

# Function to send a message
def sendmess(touser, fromsocket, message):
    global ACTIVEUSERS
    sendself = 0
    fromuser = ''
    tosocket = fromsocket

    # Find the socket you are trying to send to, and the user that is sending the message
    for name, soc in ACTIVEUSERS:
        if name == touser:
            tosocket = soc
            sendself = 1
        if soc == fromsocket:
            fromuser = name

    # if you're not logged in
    if fromuser == '':
        return 'Access denied. Please log in first.'

    # If the message is being sent to everyone
    elif touser == 'all':
        # For everyone logged in that isn't the server or the sender
        for name, soc in ACTIVEUSERS:
            if soc != server_socket and soc != fromsocket:
                try:
                    # Generic message for if the user has left
                    if message == '***hasleft***':
                        if name != '':
                            soc.send(fromuser + ' has left the chat.')
                    # Generic message for logging in
                    elif message == '***hasjoined***':
                        if name != '':
                            soc.send(fromuser + ' has joined the chat.')
                    # Send custom message with user pre-message
                    else:
                        soc.send(fromuser + ': ' + message)
                except:
                    # broken socket connection, close socket, make user inactive
                    ACTIVEUSERS = [i for i in ACTIVEUSERS if i[1] != soc]
                    soc.close()
                    continue

    # If the user is sending to themself or an inactive user, handle appropriately
    elif tosocket == fromsocket:
        if sendself == 1:
            tosocket.send(touser + ': ' + message)
        else:
            return 'User is not active.'

    # Sending to one user
    else:
        try:
            tosocket.send(fromuser + ': ' + message)
        except:
            # If unable to send to that user, assume connection is broken
            ACTIVEUSERS = [i for i in ACTIVEUSERS if i[1] != tosocket]
            tosocket.close()
            return 'User you attempted to contact has had their connection interrupted.'

    return 'success'

# MAIN

# Read in users and passwords from file
f = open('users.txt')
line = f.readline()
while line:
    splitline = line.split()
    # Add all other users and passwords to the list
    USERS.append((splitline[0], splitline[1]))
    line = f.readline()
f.close

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# Bind the socket to the port
HOST = '0.0.0.0'
PORT = 14059
server_address = (HOST, PORT)
print 'starting up server on port ' + str(PORT)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen(10)
print 'working...'

# Put server into active users list, logic purposes
ACTIVEUSERS.append(('server', server_socket))

# endless loop
while 1:
    # get list of active sockets
    x, ACTIVESOCKETS = tuple(map(list, zip(*ACTIVEUSERS)))
    # select function over the sockets. Select waits for something to be received
    # over a connection and then does something with that connection
    read_sockets, write_sockets, error_sockets = select.select(ACTIVESOCKETS, [], [])

    for sock in read_sockets:
        # if a new connection is established
        if sock == server_socket:
            # MAXCLIENTS check, establish connection if not exceeding
            if len(ACTIVEUSERS) < MAXCLIENTS + 1:
                sockfd, addr = server_socket.accept()
                ACTIVEUSERS.append(('', sockfd))
                sockfd.send('Successfully connected!')
            # Otherwise, reject connection
            else:
                sockfd, addr = server_socket.accept()
                sockfd.send('full')
                sockfd.close()

        else:
            try:
                # try to receive data from the a socket
                data = sock.recv(1024)
                # if data is received
                if data:
                    # get message into words
                    received = data.split()

                    # user types logout, send exit message to client, inform the other users,
                    # remove from active users list
                    if received[0] == 'logout':
                        sock.send('exit')
                        sendmess('all', sock, '***hasleft***')
                        ACTIVEUSERS = [i for i in ACTIVEUSERS if i[1] != sock]

                    # User types login, call function and if successful, log user in,
                    # tell other users he has joined, and return response to the client
                    elif received[0] == 'login' and len(received) == 3:
                        login_response = login(received[1], received[2], sock)
                        sendmess('all', sock, '***hasjoined***')
                        sock.send(login_response)

                    # Call new user function, reply to client with response
                    elif received[0] == 'newuser' and len(received) == 3:
                        newuser_response = newuser(received[1], received[2])
                        sock.send(newuser_response)

                    # user types who, search active users list for names and return them
                    elif received[0] == 'who':
                        who = ''
                        for name, fred in ACTIVEUSERS:
                            # remove server and blank entries from the user list
                            if name != 'server' and name != '':
                                who += ', ' + name
                        sock.send(who[2:])

                    # If user tries to send message, call sendmess function with recipient, socket, and message
                    elif received[0] == 'send' and len(received) >= 2:
                        shit = 1
                        send_response = sendmess(received[1], sock, ' '.join(received[2:]))
                        # if there was a problem, tell client what happened
                        if send_response != 'success':
                            sock.send(send_response)

                    # Any other input is invalid
                    else:
                        sock.send('Invalid command, try again.')

                # If data is not a message, client has gone offline. Tell other users client has left,
                # remove from active users list, and close the socket
                else:
                    sendmess('all', sock, '***hasleft***')
                    ACTIVEUSERS = [i for i in ACTIVEUSERS if i[1] != sock]
                    sock.close()

            # catch any exceptions in this whole loop, meaning the client connection has failed
            except:
                sendmess('all', sock, '***hasleft***')
                ACTIVEUSERS = [i for i in ACTIVEUSERS if i[1] != sock]
                sock.close()
                continue

server_socket.close()
