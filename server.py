"""
IRCChat :
Internet Relay Chat an application that lets multiple users communicate via text messages with each other in common virtual rooms.

JEANNE BETCY VICTOR

FileName: server.py

Socket based Chat application
Chat Server functionalities:
1. Accepts multiple connections from clients
2. Read incoming messages from incoming client and broadcast them to all other connected clients in the same room.
3. Functionalities that help clients to create a room, join a room , leave a room, and list rooms are available
"""

import socket
import sys
import re
import select
from collections import defaultdict

#dictUser(key,value) - (channelname, users in the channel) 
dictUser = defaultdict(list)
#dictSockChannels(key,value)-(connSocket, all channels part of connSocket)
dictSockChannels = defaultdict(list)

#dictSockNames(key,Value) - (connSocket, Nicknames)
dictSockName = dict()
#to differentiate which user enters the nickname
welcumFlag = dict()

ERR_ERRONEOUSNICKNAME = 433
ERR_NICKNAMEINUSE    = 436
ERR_NEEDMOREPARAMS = 462
ERR_NOSUCHCHANNEL = 404
ERR_INVALIDCHANNELNAME = 453
ERR_USERNOTINCHANNEL = 442
ERR_USERONCHANNEL = 444
RPL_LIST = 323

host = ''
port = 8880
connList = []
welcomeFlag = False


def welcome(newSock,nickname_err):
    """ Welcomes the client and requests for clients nick name"""
    welcumFlag[newSock] = True
    if nickname_err == False:
        msg = 'Welcome to the Chat!\nSay us your nickname:'
    elif nickname_err == True:
	nickname_err = False
        msg = '\rPlease, try again.\nSay us your nickname:' 
    newSock.send(msg)
   

def getnickname(socket, nickname):
    """ Gets the valid nick name from Client"""
    welcumFlag[socket] = False
    if re.search('[^a-zA-Z0-9\-\_]', nickname):
        nickname_err = True
	socket.send('\rERR_ERRONEOUSNICKNAME:%d Invalid nick name. \n' % ERR_ERRONEOUSNICKNAME)
	welcome(socket,nickname_err)
    else:
        if nickname not in nicknamelist:
            nicknamelist.append(nickname)
	    nMsg = '\rName Accepted\n'
            socket.send(nMsg.encode())
	    listcommands(socket)
        else:
            nickname_err = True
	    socket.send('\rERR_NICKNAMEINUSE:%d Nick name in use. \n' % ERR_NICKNAMEINUSE)
	    welcome(socket,nickname_err)
    #print nicknamelist
    return nickname

def create_join(socket, uname, param):
    """ Joining channels specified. If channel do not exist, creates and joins the channel"""
    cmd, target = param.split(' ', 1)
    chName = target.strip()
    if re.search('^#([a-zA-Z0-9])', chName):
        if not uname in dictUser[chName]:
            if chName in channellist:
                dictUser[chName].append(uname)
		#Done, so that while sending chat msg,only users in that channel can get
		dictSockChannels[socket].append(chName) 
		msg = '\rYou joined %s\n\n' % chName
            else:
                #Create new channel
                channellist.append(chName)
                #add user to the channel
                dictUser[chName].append(uname)
		dictSockChannels[socket].append(chName)
		msg = '\r%s is created.\nYou joined %s\n\n' % (chName,chName)
	    msgToAll = "\r'"+dictSockName[socket]+"'"+ "entered %s \n\n" % chName
	    #Send message to all users in this channel about the entry of new client 	
	    msgtoall(socket,chName,msg,msgToAll)
        else:
            socket.send('\rERR_USERONCHANNEL:%d, %s already on channel %s\n\n' % (ERR_USERONCHANNEL,uname,chName))
    else:
        socket.send('\rERR_INVALIDCHANNELNAME:%d %s Invalid Channel Name\n\n' % (ERR_INVALIDCHANNELNAME,chName))
    
def listChannel(socket):
    """ List all Channels """
    if len(channellist)==0:
        msg = "\rNo active channels\n\n"
    else:
        msg = '\rRPL_LIST:%d Active rooms are...\n' % RPL_LIST
        for ch in channellist:
            msg += ch + "\n"
	msg = msg + "\n"
    socket.send(msg.encode())


def listUsersChannels(socket):
    """ List channels associated with a particular client"""
    if len(dictSockChannels[socket]) == 0:
	msg = '\rYou have not joined in any Channels\n\n'
    else:
	msg = '\rRPL_LIST:%d You are active in rooms....\n' % RPL_LIST
        for ch in dictSockChannels[socket]:
            msg += ch + '\n'
	msg = msg + "\n"
    socket.send(msg.encode())


def sendmessage(socket, uname, params):
    """ Send msg to the group"""
    cmd,target,msg = params.split(' ', 2)
    if target.startswith('#'):
        if target in channellist:
            if not uname in dictUser[target]:
                socket.send("\rERR_USERNOTINCHANNEL:%d, %s is not in %s. Cannot Send Message to the channel\n\n" % (ERR_USERNOTINCHANNEL,uname,target))
            else:
		msgToAll = '\r<'+dictSockName[socket]+'>'+msg +''
		msgtoall(socket,target,'',msgToAll)
        else:            
            socket.send("\rERR_NOSUCHCHANNEL:%d No Such channel\n\n" % ERR_NOSUCHCHANNEL)
    else:
        socket.send("\rERR_INVALIDCHANNELNAME:%d Invalid channel Name\n\n" % ERR_INVALIDCHANNELNAME)

def listcommands(socket):
    """ Listing all commands """
    msg = '\n[Commands Used:]\nJoin a Channel-<JOIN> #chName\nList all Channels-<LISTALL>\nList users channel-<LIST>\n'\
	  + 'SendMessage to Channel- SENDMSG #<channelName> <msg>\nTo leave a channel-<LEAVE> #chName\n'\
          + 'To quit-<QUIT>\nTo list all commands-<CMD>\n\n'
    socket.send(msg.encode())

def leavechannel(socket,uname,params):
    """ Leave a particular channel """
    cmd, target = params.split(' ', 1)
    chName = target.strip()
    if re.search('^#([a-zA-Z0-9])', chName):
	if chName in channellist:
	    if chName in dictSockChannels[socket]:
	        dictSockChannels[socket].remove(chName)
	        dictUser[chName].remove(uname)
	        msg = '\rYou are removed from channel %s\n\n' % chName
	        msgToAll = "\r'"+dictSockName[socket]+"'"+ "left %s \n\n" % chName
	        #Send message to all users in this channel about the entry of new client 	
   	        msgtoall(socket,chName,msg,msgToAll)
	    else:
	        socket.send('\rERR_USERNOTINCHANNEL:%d User not in this channel\n\n' % ERR_USERNOTINCHANNEL)
	else:
	    socket.send("\rERR_NOSUCHCHANNEL:%d No such channel\n\n" % ERR_NOSUCHCHANNEL)    	    
    else:
        socket.send('\rERR_INVALIDCHANNELNAME:%d, %s is Invalid Channel Name\n\n' % (ERR_INVALIDCHANNELNAME,chName))
    

def quit(socket):
    """ Clients quits the session"""
    print "\rClient %s is Disconnected " % dictSockName[socket]
    nicknamelist.remove(dictSockName[socket])
    for name in dictUser.itervalues():
        if dictSockName[socket] in name:
	    name.remove(dictSockName[socket])
    del dictSockName[socket]
    socket.close()
    connList.remove(socket)
	

def msgtoall(socket,chName,msg,msgToAll):
    """ Sends message to all other clients when a user in the common channel sends a message/enters a channel/leaves the channel"""
    for client in connList:
        if client != socket:
            if chName in dictSockChannels[client]:
                client.send(msgToAll)
	    #else:
	        #print 'channel : %s not in dictSockChannels[client] : %s' % (chName,dictSockChannels[client])
	else:
	    socket.send(msg)

BUFF_SIZE = 1024
channellist = []
nicknamelist = []
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Server: Socket Created'
serversocket.bind(('', port))
print 'Server: Socket Bind is complete'
serversocket.listen(5)
print 'Socket Listening'

connList.append(serversocket)
while 1:

    ready_to_read,ready_to_write,in_error = select.select(connList,[],[])
    for i in ready_to_read:
        #New Connection
	if i == serversocket:
	    connectionsocket, addr = serversocket.accept()
    	    connList.append(connectionsocket)
    	    print "Client <%s, %s> connected " % addr 
	    nicknameErrFlag = False
	    welcome(connectionsocket,nicknameErrFlag)
	else:
	    try:
		if welcumFlag[i] == True:
    		    nickname = i.recv(BUFF_SIZE)
    		    name = getnickname(i, nickname)
		    dictSockName[i] = name
	        else:
		    msgFromClient = i.recv(BUFF_SIZE)	
		    if msgFromClient:
                        if '<JOIN>' in msgFromClient:
			    if msgFromClient.count(' ') < 1:	
				i.send('\rERR_NEEDMOREPARAMS:%d Insufficient Params\n' % ERR_NEEDMOREPARAMS)   
			    else:
				create_join(i, dictSockName[i], msgFromClient )
			elif '<LIST>' in msgFromClient: 
			    listUsersChannels(i)
    			elif '<LISTALL>' in msgFromClient:
           		    listChannel(i)
    			elif '<SENDMSG>' in msgFromClient:
			    if msgFromClient.count(' ') < 2:	
				i.send('\rERR_NEEDMOREPARAMS:%d Insufficient Params\n\n' % ERR_NEEDMOREPARAMS)   
			    else:
        		        sendmessage(i, dictSockName[i], msgFromClient)
			elif '<CMD>' in msgFromClient:
			    listcommands(i)
			elif '<LEAVE>' in msgFromClient:
			    if msgFromClient.count(' ') < 1:	
				i.send('\rERR_NEEDMOREPARAMS:%d Insufficient Params\n\n' % ERR_NEEDMOREPARAMS)   
			    else:
			        leavechannel(i,dictSockName[i], msgFromClient)
		        elif '<QUIT>' in msgFromClient:
			    quit(i)
			#else:
			    #print 'MSG not recognized'
		    else:
			quit(i)
	    except:   
		quit(i)
	
		continue

serversocket.close()
