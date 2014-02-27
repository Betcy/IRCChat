"""
IRCChat :
Internet Relay Chat an application that lets multiple users communicate via text messages with each other in common virtual rooms.

JEANNE BETCY VICTOR

FileName: client.py

Socket based Chat application
Chat Client functionalities:
1. Listens for incoming messages from the server
2. Send the user message to the server
"""

import socket  #for sockets
import sys
import select

BUFF_SIZE = 1024
host = sys.argv[1] #'localhost'
port = int(sys.argv[2]) #8888
# create an AF_INET, STREAM SOCKETS (TCP)
# AF_INET - Address famile for IPv4 version
# SOCK_STREAM - TCP oriented
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "Socket Created"
try:
    clientsocket.connect((host, port))
    print 'Socket Connected to ' + host
except:
    print 'Unable to connect ' + host
    sys.exit()

socketList = [sys.stdin,clientsocket]


def prompt():
    sys.stdout.write('<Me>')
    sys.stdout.flush()

while 1:
    #Waiting for input from stdin and clientsocket
    rsocket, wsocket, esocket = select.select(socketList, [], [])
    for s in rsocket:
	if s is clientsocket: 
	    reply = s.recv(BUFF_SIZE)
	    if not reply:
	        print 'Shutting down \n'
		sys.exit()
	    else:		
		if 'Say us your nickname:' in reply.decode():
		    name = raw_input(reply)
		    s.send(name)
		else:
		    sys.stdout.write(reply.decode())
	    prompt()
	else:
	    reply = sys.stdin.readline()
	    clientsocket.sendall(reply)
	    prompt()

