from socket import *
import os
import sys
import struct
import time
import select
import binascii

import datetime



ICMP_ECHO_REQUEST = 8


def checksum(string):
	csum = 0
	countTo = (len(string) // 2) * 2
	count = 0

	while count < countTo:
		thisVal = string[count+1] * 256 + string[count]
		csum = csum + thisVal
		csum = csum & 0xffffffff
		count = count + 2

	if countTo < len(string):
		csum = csum + string[len(string) - 1]
		csum = csum & 0xffffffff

	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum
	answer = answer & 0xffff
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer




def receiveOnePing(mySocket, ID, timeout, destAddr):
	timeLeft = timeout

	while True:
		startedSelect = time.time()
		whatReady = select.select([mySocket], [], [], timeLeft)
		howLongInSelect = (time.time() - startedSelect)
		if whatReady[0] == []: # Timeout
			return (False, "Request timed out.")

		timeReceived = time.time()
		recPacket, addr = mySocket.recvfrom(1024)

		# Fetch the ICMPHeader from the received IP
		ICMPHeader = recPacket[20:28]
		dest_IP = inet_ntoa(recPacket[12:16])

		rawTTL = struct.unpack("s", bytes([recPacket[8]]))[0]

		# binascii -- Convert between binary and ASCII
		TTL = int(binascii.hexlify(rawTTL), 16)

		# Fetch icmpType, code, checksum, packetID, and sequence from ICMPHeader
		# using struct.unpack method

		contents = struct.unpack("bbHHh", ICMPHeader)
		icmpType = contents[0]
		code = contents[1]
		checksum = contents[2]
		packetID = contents[3]
		sequence = contents[4]

		done = icmpType == 0

		byte = struct.calcsize("d")
		timeSent = struct.unpack("d", recPacket[28:28 + byte])[0]
		pack_time = (timeReceived - timeSent)*1000
		ret_val = (dest_IP, pack_time)

		return (done, ret_val)



def sendOnePing(mySocket, destAddr, ID, ttl):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)

	myChecksum = 0
	# Make a dummy header with a 0 checksum
	# struct -- Interpret strings as packed binary data
	header = struct.pack("BBHHH", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	data = struct.pack("d", time.time())
	# Calculate the checksum on the data and the dummy header.

	myChecksum = checksum(header + data)

	# Get the right checksum, and put in the header
	if sys.platform == 'darwin':
		# Convert 16-bit integers from host to network byte order
		myChecksum = htons(myChecksum) & 0xffff
	else:
		myChecksum = htons(myChecksum)

	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	packet = header + data

	mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))

	mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not string

def doOnePing(destAddr, timeout, ttl):
	icmp = getprotobyname("icmp")

	# SOCK_RAW is a powerful socket type. For more details:   http://sock-raw.org/papers/sock_raw
	mySocket = socket(AF_INET, SOCK_RAW, icmp)

	myID = os.getpid() & 0xFFFF  # Return the current process i
	st = datetime.datetime.now()
	sendOnePing(mySocket, destAddr, myID, ttl)
	got_back = receiveOnePing(mySocket, myID, timeout, destAddr)
	end = datetime.datetime.now()

	code_time = end-st
	code_time = (code_time.microseconds)/1000

	mySocket.close()

	return (got_back, code_time)



def ping(host, timeout=1):
	# timeout=1 means: If one second goes by without a reply from the server,
	# the client assumes that either the client's ping or the server's pong is lost
	dest = gethostbyname(host)
	print("Pinging " + host + " using Python:")
	print("")
	print("TTL\tIP\t\t\tRTT(ms)")
	# Send ping requests to a server separated by approximately one second
	done = False
	ttl = 1
	while not done:
		# for i in range(NUM_PACKETS):
		got_back = doOnePing(dest, timeout, ttl)
		if isinstance(got_back[0][1], str):
			done, delay = got_back[0][0], got_back[0][1]
			print(ttl,"\t* * *")
		else:
			done, pack_info, code_time = got_back[0][0], got_back[0][1], got_back[1]
			if len(str(pack_info[0])) > 13:
				print(ttl,"\t",pack_info[0],"\t",code_time)
			else:
				print(ttl,"\t",pack_info[0],"\t\t",code_time)
		time.sleep(1) # one second
		ttl += 1

	return code_time

if __name__ == '__main__':
	if len(sys.argv) == 2:
		ping(sys.argv[1])
	else:
		ping("google.com")
