import sys
from socket import *
import numpy 

from util import *
import time
import random

PACKET_SIZE = 1472      # 1500-8(udp header)-20(IP header) = 1472
PAYLOAD_SIZE = 1456     # 1472(PACKET_SIZE)-16(Header) = 1456
ret_time = 0.5          # timeout value
pkt_list = []
    
class RDTSocket(UnreliableSocket):
    """
    You need to implement the following functions to provide reliability over UnreliableSocket
    """
    def __init__(self, window_size):
        super(RDTSocket, self).__init__()
        self.window = {}     # keeps mapping of <seq_num, message> pairs
        self.window_size = window_size
        self._send_to = None # specifies the address of the socket on the other side
        self.send_base = 0   # points to the oldest unacked packet
        self.recv_base = 0   # points to the next expected packet
        done = False
        receiver_address = None
        sender_address = None
        self.t = ''
        self.rcvd_pkts = []
        end_pkt = None
        """
        Add any other necesesary initial arguments
        """ 

    def accept(self):
        """
        Accept a connection. The socket must be bound to an address and listening for
        connections. The return value is the address of the socket on the other end of the connection.

        This function should be a blocking function.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        ##
        print("Entered accept phase")
        data = None
        start = time.time()
        ##try to receive start packet
        while True: 
                try:
                        data, addr = self.recvfrom(PACKET_SIZE)
                        print("received data")
                        self._send_to = addr
                        sender_address = addr
                        print(self._send_to)
                        data = bytearray(data)
                        print('found start message from', addr, '...')
                        pkt_header = PacketHeader(data[:16])
                        h_type = pkt_header.type
                        self.recv_base = 1
                        if pkt_header.type==START:
                                pkt1_header = PacketHeader(type=ACK, seq_num = 1, length = 0)
                                msg = ""
                                pkt1_header.checksum = compute_checksum(pkt1_header / msg)
                                snd_pkt = pkt1_header / msg
                                print("sending Start ACK to sender...") 
                                print (pkt1_header.seq_num)
                                self.sendto(bytes(snd_pkt), addr)
                                print("Start ACK sent")
                                start = time.time()
                                break ##break if start packet received
                        elif pkt_header.type == DATA:
                                print("Dropping data packet")
                                 continue ##drop data packets
                        else: 
                                print("Packet of type", h_type, "has been dropped...")
                                data = None
                                continue
                except OSError:
                                continue
                return self._send_to
                  
                                             
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def connect(self, address):
        """
        Connect to a remote socket at address.
        Corresponds to the process of establishing a connection on the client side.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        ##send start message to receiver       
        receiver_address = address
        print('address saved', address, '...')
        data = None
        pkt_header = PacketHeader(type=START, seq_num=0, length=0) 
        msg="" 
        pkt_header.checksum = compute_checksum(pkt_header / msg)
        pkt = pkt_header / msg
        print('start packet made')
        self.sendto(bytes(pkt), address)
        print('start packet sent')
        start = time.time()
        print("Sending start packet")
        self.send_base = 0
        self._send_to = address
        
             
        ### I noticed that the start ack gets lost every single time, so if this code is uncommented, it will get stuck sending start and start ack back and forth     
        """
        while True:
                try:
                        data, addr = self.recvfrom(PACKET_SIZE)
                        print(PacketHeader(data[:16].type), PacketHeader(data[:16].seq_num))
                        if PacketHeader(data[:16]).type == 3:
                                print('Start ACK received')
                                print(self._send_to)
                                break
                        if PacketHeader(data[:16]).type == DATA:
                               break
                        else:
                                data = None
                                continue
                except: 
                        if ((time.time() - start) >= 1):
                                print ("timeout reached, resending start")
                                self.connect(address)
                        else:
                                continue
        """
        
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def recv(self, bufsize):
        """
        Receive data from the socket. The return value is the received data.
        The maximum amount of data to be received at once is specified by bufsize.
        """
        print("Entered recv phase")
        data = None
        assert self._send_to, "Connection not established yet."
        
        ##receive packet from sender
        while not data:
                try: 
                        data, addr = self.recvfrom(PACKET_SIZE)
                        print('data packet received')
                except OSError:
                        continue
	
        print("making data packets")
        lastAck = time.time()
        while data:
                pkt1_header = PacketHeader(data[:16])
                print(pkt1_header.seq_num, pkt1_header.type)
                if pkt1_header.type == 2 and pkt1_header.seq_num < self.recv_base: ##if it is a repeat packet, resend ACK
                        print('repeat packet, resending ACK')
                        pkt_header = PacketHeader(type=ACK, seq_num = pkt1_header.seq_num + 1, length=0)
                        msg = ""
                        pkt_header.checksum = compute_checksum(pkt_header / msg)
                        snd_pkt = pkt_header / msg
                        self.sendto(bytes(snd_pkt), self._send_to)
                        print('Ack', pkt_header.seq_num, 'sent')
                        self.recv(bufsize)
                if pkt1_header.type == 2 and pkt1_header.seq_num >= self.recv_base: ##if it is in the window
                        if verify_packet(pkt1_header, data[16:]): ##if it is not corrupt
                                if pkt1_header.seq_num > self.recv_base: ##if it is not the expected packet, send ACK N
                                        print('out of order packet received')
                                        self.rcvd_pkts.append(data)
                                        pkt_header = PacketHeader(type=ACK, seq_num=self.recv_base, length=0)
                                        msg = ""
                                        pkt_header.checksum = compute_checksum(pkt_header / msg)
                                        snd_pkt = pkt_header / msg
                                        self.sendto(bytes(snd_pkt), self._send_to)
                                        print('Ack', pkt_header.seq_num, 'sent')
                                        self.recv(bufsize)
                                if pkt1_header.seq_num == self.recv_base: ## if it is N, send ACK + 1 of next packet in buffer
                                        print("in order packet received")
                                        self.t += data[16:].decode()
                                        print(self.t)
                                        print(data[16:].decode())
                                        for i in self.rcvd_pkts:
                                                if PacketHeader(i[:16]).seq_num == self.recv_base + 1: ##find data from packets
                                                        self.recv_base = PacketHeader(i[:16]).seq_num 
                                                        self.t += i[16:].decode() ##append data to final message
                                        self.recv_base += 1
                                        pkt_header = PacketHeader(type=ACK, seq_num=self.recv_base, length =0)
                                        msg=""
                                        pkt_header.checksum = compute_checksum(pkt_header / msg)
                                        snd_pkt = pkt_header / msg
                                        self.sendto(bytes(snd_pkt), self._send_to)
                                        print(self._send_to)
                                        print('ACK', pkt_header.seq_num, 'sent')
                                        self.recv(bufsize) ##send cumulative ACK
                        else:
                               print("Packet corrupted, dropped")
                               self.recv(bufsize) #drop corrupt and redo method
                if (pkt1_header.seq_num > self.recv_base + self.window_size): ##drop packets outside of window
                         print("Packet outside of window, has been dropped")
                         self.recv(bufsize) 
                if (pkt1_header.seq_num == 0): ###drop outside of window
                        print("Packet outside of window, has been dropped")
                        self.recv(bufsize)
                if pkt1_header.type == 1: ##if the end packet is sent
                        if self.recv_base >= pkt1_header.seq_num: ##if all previous packets have been acked
                                print('END packet received')
                                pkt_header = PacketHeader(type=END_ACK, seq_num = pkt1_header.seq_num, length = 0)
                                msg = ""
                                pkt_header.checksum = compute_checksum(pkt_header / msg)
                                snd_pkt = pkt_header / msg
                                self.sendto(bytes(snd_pkt), self._send_to) ##send END ACK
                                print('End ACK sent')
                                end_pkt = snd_pkt
                                lastAck = time.time()
                                break
                        else:
                                pkt_header = PacketHeader(type=ACK, seq_num = self.recv_base, length = 0)
                                msg = ""
                                pkt_header.checksum = compute_checksum(pkt_header / msg)
                                snd_pkt = pkt_header / msg
                                self.sendto(bytes(snd_pkt), self._send_to) ##else send ACK for N
                else: 
                        print("Corrupt packet, dropped")
                        self.recv(bufsize)
                        
        print("message data returned") ##return the file
        fileLines =  self.t
        print(fileLines)
        return fileLines
        
	
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
	
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def send(self, _bytes):
        """
        Send data to the socket. _bytes contains the bytearray of the data.
        The socket must be connected to a remote socket, i.e. self._send_to must not be none.
        """
        
        print("Entered send function")
        print (self._send_to)
        assert self._send_to, "Connection not established yet. Use sendto instead."
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        sntpkts = []
        x = 1
        y = 0
        done = False
        for i in range(0, int(len(_bytes) / PAYLOAD_SIZE) + 1): ##Divide the file into packets and fill list with packets
                print("Making packets")
                data = _bytes[y:y+PAYLOAD_SIZE]
                print(y + PAYLOAD_SIZE)
                pkt_header = PacketHeader(type=DATA, seq_num=x, length = len(data))
                msg = data
                pkt_header.checksum = compute_checksum(pkt_header / msg)
                pkt = pkt_header / msg
                print(pkt_header.seq_num)
                pkt_list.append(pkt)
                x+=1
                y+=PAYLOAD_SIZE + 1
                print("Packets made")
        	
        z = 0
        
        if self.window_size > len(pkt_list):
                self.window_size = len(pkt_list) #adjust window size if over number of packets
        
	
        for i in range(self.window_size - 1): ##fill window array
	        self.window[i] = "Empty"
	        
        lastAck = time.time()
        while self.window: ##while the window is there
                if z < len(pkt_list): ###if in the list, send packets to receiver
                        self.sendto(bytes(pkt[z]), self._send_to)
                        print(pkt_list[z].seq_num)
                        self.window[pkt_list[z].seq_num] = bytes(pkt_list[z])[16:]
                        print("appending packets to window")
                        z += 1
              
                try:
                        pkt, addr = self.recvfrom(PACKET_SIZE) ## check for ACKS
                        pkt_header = PacketHeader(pkt[:16])
                        if pkt_header.type==ACK:
                                print('ACK', pkt_header.seq_num, 'received')
                                if pkt_header.seq_num == self.send_base + 2:
                                        del self.window[pkt_header.seq_num - 1] ##adjust window size on ACK receipt
                                        self.send_base += 1
                                        lastAck = time.time()
                                if pkt_header.seq_num == len(pkt_list) + 1: ##if list is over go to end
                                        break
                                        
                except:
                        if(time.time()-lastAck >= ret_time): ##resend packets at timeout
                                print("timeout reached, resending packets")
                                for key in self.window:
                                       if self.window[key] != "Empty":
                                                self.sendto(bytes(pkt_list[key - 1]), self._send_to)
                                                print ('resending packet', pkt_list[key-1].seq_num, 'to receiver')
                                                lastAck = time.time()

        print("sending end packet") ##send END packet
        pkt_header = PacketHeader(type=END, seq_num= len(pkt_list) + 1, length = 0)
        msg = ""
        pkt_header.checksum = compute_checksum(pkt_header / msg)
        pkt = pkt_header / msg
        self.sendto(bytes(pkt), self._send_to)
        print("end packet sent")
               
        """
                while True:
                        try: 
                                data, addr = self.recvfrom(PACKET_SIZE)
                                pkt_header = PacketHeader(data[:16])
                                if pkt_header.type == END_ACK:
                                        print('End ACK received')
                                        break
                        except:
                                if lastAck- time.time() >= ret_time:
                                        self.sendto(bytes(pkt), self._send_to)
                                        continue
        """
                                
        #############################################################################
        #                             END OF YOUR CODE                              #
        #############################################################################

    def close(self):
        """
        Finish the connection and release resources. For simplicity, assume that
        after a socket is closed, neither futher sends nor receives are allowed.
        """
        lastAck = time.time()
        while True: ##look for end ack and close
                        try: 
                                data, addr = self.recvfrom(PACKET_SIZE)
                                pkt_header = PacketHeader(data[:16])
                                if pkt_header.type == END_ACK:
                                        print('End ACK received')
                                        self.sock.close()
                                        print("Connection close")
                        except:
                                if lastAck- time.time() >= ret_time:
                                        self.sendto(bytes(end_pkt), self.send_to)
                                        continue
    """
    Add any necessary auxiliary functions
    """
